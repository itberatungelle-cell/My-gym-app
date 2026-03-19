import streamlit as st
import pandas as pd
import requests
import altair as alt

# --- KONFIGURATION ---
# 1. Deine Google Sheet ID (Fest eingetragen)
SHEET_ID = "160eAiq0CW9p8py6GhbkVMdABXtoB3ANtoh1ez1dpZ_4" 
READ_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

# 2. Deine Google Form URL (Fest eingetragen)
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
        # Daten an Google Forms senden (mit deinen IDs aus dem Link)
        payload = {
            "entry.2114330699": day,
            "entry.1094088238": time,
            "entry.1741468156": crowd
        }
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            response = requests.post(FORM_URL, data=payload, headers=headers)
            if response.ok:
                st.success(f"Erfolgreich gespeichert: {day}, {time}:00 Uhr, Level {crowd}")
                st.balloons()
                st.cache_data.clear() # Cache leeren für frische Daten
            else:
                st.error(f"Google Fehler-Code: {response.status_code}")
        except Exception as e:
            st.error(f"Verbindung fehlgeschlagen: {e}")

# --- DATEN LADEN & SORTIEREN ---
@st.cache_data(ttl=5)
def load_data():
    try:
        df = pd.read_csv(READ_URL)
        # Wir nehmen die letzten 3 Spalten (Wochentag, Uhrzeit, Auslastung)
        df = df.iloc[:, -3:] 
        df.columns = ["Wochentag", "Uhrzeit", "Auslastung"]
        
        # Wochentage für die Sortierung definieren
        tage_ordnung = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
        df["Wochentag"] = pd.Categorical(df["Wochentag"], categories=tage_ordnung, ordered=True)
        
        # Auslastung in Zahlen umwandeln
        df["Auslastung"] = pd.to_numeric(df["Auslastung"], errors='coerce')
        return df
    except:
        return pd.DataFrame()

df = load_data()

# --- AUSWERTUNG & GRAFIK ---
if not df.empty:
    st.divider()
    st.subheader("📊 Deine Analyse")

    # Durchschnitt berechnen
    stats = df.groupby(["Wochentag", "Uhrzeit"], observed=True)["Auslastung"].mean().reset_index()
    stats = stats.sort_values(["Wochentag", "Uhrzeit"])

    # 1. Die Top 3 Empfehlungen (Die leersten Zeiten)
    best_times = stats.sort_values(by="Auslastung")
    st.write("Die 3 besten (leersten) Zeiten für dich:")
    cols = st.columns(3)
    for i, row in enumerate(best_times.head(3).itertuples()):
        with cols[i]:
            st.metric(label=str(row.Wochentag), value=f"{row.Uhrzeit}:00 Uhr", delta=f"Auslastung: {row.Auslastung:.1f}", delta_color="inverse")
    
    # 2. Farbiges Altair Diagramm (Grün = Leer, Rot = Voll)
    st.write("### Auslastung im Wochenverlauf")
    chart = alt.Chart(stats).mark_bar().encode(
        x=alt.X('Wochentag:N', sort=["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"], title="Tag"),
        y=alt.Y('Auslastung:Q', title="Durchschnittliche Auslastung (1-10)"),
        color=alt.Color('Auslastung:Q', 
                        scale=alt.Scale(scheme='yellowgreenred', reverse=False),
                        legend=None),
        tooltip=['Wochentag', 'Uhrzeit', 'Auslastung']
    ).properties(height=400)

    st.altair_chart(chart, use_container_width=True)

    # 3. Rohdaten Ansicht
    with st.expander("Alle Einträge anzeigen"):
        st.dataframe(df.sort_values("Wochentag", ascending=True), use_container_width=True)
else:
    st.divider()
    st.info("Noch keine Daten vorhanden. Trage oben dein Training ein!")
    
