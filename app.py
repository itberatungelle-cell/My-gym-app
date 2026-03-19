import streamlit as st
import pandas as pd
import requests

# --- KONFIGURATION ---
# Deine IDs sind hier fest verbaut:
SHEET_ID = "160eAiq0CW9p8py6GhbkVMdABXtoB3ANtoh1ez1dpZ_4" 
READ_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"
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
        payload = {
            "entry.2114330699": day,
            "entry.1094088238": str(time),
            "entry.1741468156": str(crowd)
        }
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            response = requests.post(FORM_URL, data=payload, headers=headers)
            if response.ok:
                st.success(f"Gespeichert! {day}, {time} Uhr (Level {crowd})")
                st.balloons()
                st.cache_data.clear()
            else:
                st.error(f"Fehler: Google antwortet nicht korrekt ({response.status_code})")
        except:
            st.error("Verbindung fehlgeschlagen.")

# --- DATEN LADEN & VORBEREITEN ---
@st.cache_data(ttl=2)
def load_data():
    try:
        df = pd.read_csv(READ_URL)
        # Wir nehmen die letzten 3 Spalten (Wochentag, Uhrzeit, Auslastung)
        df = df.iloc[:, -3:].copy()
        df.columns = ["Wochentag", "Uhrzeit", "Auslastung"]
        
        # Datentypen korrigieren
        df["Auslastung"] = pd.to_numeric(df["Auslastung"], errors='coerce').fillna(0)
        df["Uhrzeit"] = pd.to_numeric(df["Uhrzeit"], errors='coerce').fillna(0).astype(int)
        
        # Sortierung festlegen
        tage_ordnung = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
        df["Wochentag"] = pd.Categorical(df["Wochentag"], categories=tage_ordnung, ordered=True)
        return df
    except:
        return pd.DataFrame()

df = load_data()

# --- ANALYSE ANZEIGEN ---
if not df.empty:
    st.divider()
    st.subheader("📊 Deine Analyse")

    # Durchschnitt berechnen
    stats = df.groupby(["Wochentag", "Uhrzeit"], observed=True)["Auslastung"].mean().reset_index()
    stats = stats.sort_values(["Wochentag", "Uhrzeit"])

    # 1. Die Top 3 Empfehlungen (Fix: Inverse Farben für Rot/Grün)
    best_times = stats.sort_values(by="Auslastung", ascending=True)
    st.write("Die besten Zeiten zum Trainieren:")
    cols = st.columns(3)
    
    for i, row in enumerate(best_times.head(3).itertuples()):
        with cols[i]:
            # delta_color="inverse" sorgt dafür, dass NIEDRIGE Werte GRÜN angezeigt werden
            st.metric(
                label=str(row.Wochentag), 
                value=f"{row.Uhrzeit}:00 Uhr", 
                delta=f"Level {row.Auslastung:.1f}", 
                delta_color="inverse"
            )
    
    # 2. Visuelles Diagramm (Robustes Standard-Chart für Handy)
    st.write("### Auslastung im Überblick")
    
    # Wir bereiten die Daten für das Balkendiagramm vor
    chart_data = stats.groupby("Wochentag", observed=True)["Auslastung"].mean()
    st.bar_chart(chart_data)

    # 3. Rohdaten Ansicht
    with st.expander("Alle Einträge anzeigen"):
        st.dataframe(df.sort_values("Wochentag"), use_container_width=True)
else:
    st.info("Noch keine Daten vorhanden. Bitte einen Test-Eintrag machen!")
    
