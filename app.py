import streamlit as st
import pandas as pd
import requests

# --- KONFIGURATION ---
# 1. Deine Google Sheet ID (aus der Tabellen-URL)
SHEET_ID = "160eAiq0CW9p8py6GhbkVMdABXtoB3ANtoh1ez1dpZ_4" 
READ_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

# 2. Deine Google Form Daten (aus deinem Link extrahiert)
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScLmlWy29EqqOpN--6EOEb_QlnxiarS24vKbj1bAs1nZhqEzg/formResponse"

st.set_page_config(page_title="Gym Tracker", page_icon="🏋️")
st.title("🏋️ Mein Gym-Flow Tracker")

# --- EINGABE-BEREICH ---
with st.form("gym_form", clear_on_submit=True):
    st.subheader("Neues Training eintragen")
    day = st.selectbox("Wochentag", ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"])
    time = st.slider("Uhrzeit (Stunde)", 6, 23, 17)
    crowd = st.select_slider("Wie voll war es? (1=Leer, 10=Voll)", options=list(range(1, 11)), value=5)
    
    submitted = st.form_submit_button("Speichern")
    
    if submitted:
        # Daten an Google Forms senden
        payload = {
            "entry.2114330699": day,
            "entry.1094088238": time,
            "entry.1741468156": crowd
        }
        try:
            response = requests.post(FORM_URL, data=payload)
            if response.status_code == 200:
                st.success(f"Erfolgreich gespeichert: {day}, {time}:00 Uhr, Level {crowd}")
                st.balloons()
                st.cache_data.clear() # Cache leeren für frische Daten
            else:
                st.error("Fehler beim Senden an Google.")
        except:
            st.error("Verbindung fehlgeschlagen.")

# --- AUSWERTUNG ---
st.divider()
st.subheader("📊 Deine Analyse")

@st.cache_data(ttl=5) # Daten alle 5 Sek. neu laden
def load_data():
    try:
        df = pd.read_csv(READ_URL)
        # Spaltennamen anpassen (Google Sheets benennt sie oft nach dem Zeitstempel)
        # Wir nehmen die letzten 3 Spalten
        df = df.iloc[:, -3:] 
        df.columns = ["Wochentag", "Uhrzeit", "Auslastung"]
        return df
    except:
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # Berechnung des Schnitts
    df["Auslastung"] = pd.to_numeric(df["Auslastung"], errors='coerce')
    stats = df.groupby(["Wochentag", "Uhrzeit"])["Auslastung"].mean().reset_index()
    best_times = stats.sort_values(by="Auslastung")

    st.write("Die 3 besten (leersten) Zeiten:")
    cols = st.columns(3)
    for i, row in enumerate(best_times.head(3).itertuples()):
        with cols[i]:
            st.metric(label=row.Wochentag, value=f"{row.Uhrzeit}:00 Uhr", delta=f"Score: {row.Auslastung:.1f}", delta_color="inverse")
    
    # Kleines Diagramm zur Übersicht
    st.bar_chart(data=stats, x="Wochentag", y="Auslastung")
else:
    st.info("Noch keine Daten vorhanden. Trage dein erstes Training oben ein!")
    
