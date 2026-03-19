import streamlit as st
import pandas as pd
import requests
import altair as alt
from datetime import datetime

# --- KONFIGURATION ---
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
                st.cache_data.clear() # Cache sofort löschen
            else:
                st.error(f"Fehler bei Google ({response.status_code})")
        except:
            st.error("Verbindung fehlgeschlagen.")

# --- DATEN LADEN ---
@st.cache_data(ttl=0) # Wir schalten den Cache zum Testen komplett aus (0 Sekunden)
def load_data():
    try:
        df = pd.read_csv(READ_URL)
        df = df.iloc[:, -3:].copy()
        df.columns = ["Wochentag", "Uhrzeit", "Auslastung"]
        df["Auslastung"] = pd.to_numeric(df["Auslastung"], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame()

df = load_data()

# --- ANALYSE ---
if not df.empty:
    st.divider()
    st.subheader("📊 Deine Analyse")

    # 1. Top 3 Zeiten (Wir lassen die Farbe jetzt weg, wenn sie zickt, und machen es schlicht & klar)
    best_stats = df.groupby(["Wochentag", "Uhrzeit"], observed=True)["Auslastung"].mean().reset_index()
    best_times = best_stats.sort_values(by="Auslastung", ascending=True).head(3)
    
    st.write("Die besten Zeiten zum Trainieren:")
    cols = st.columns(3)
    for i, row in enumerate(best_times.itertuples()):
        with cols[i]:
            st.metric(label=str(row.Wochentag), value=f"{row.Uhrzeit}:00 Uhr", delta=f"Level {row.Auslastung:.1f}", delta_color="inverse")
    
    # 2. DAS PROFI-DIAGRAMM (Altair erzwingt die Sortierung)
    st.write("### Auslastung im Wochenverlauf")
    
    # Daten für die Grafik vorbereiten
    chart_stats = df.groupby("Wochentag", observed=True)["Auslastung"].mean().reset_index()
    
    # Altair Chart mit EXPLIZITER Sortierung
    tage_folge = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    
    chart = alt.Chart(chart_stats).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
        x=alt.X('Wochentag:N', sort=tage_folge, title="Wochentag"),
        y=alt.Y('Auslastung:Q', title="Durchschnittliche Auslastung"),
        color=alt.Color('Auslastung:Q', scale=alt.Scale(scheme='yellowgreenred'), legend=None),
        tooltip=['Wochentag', 'Auslastung']
    ).properties(height=350)

    st.altair_chart(chart, use_container_width=True)

    with st.expander("Rohdaten"):
        st.dataframe(df)
else:
    st.info("Noch keine Daten vorhanden.")

# Kleiner Test, ob die App aktuell ist
st.caption(f"App-Update: {datetime.now().strftime('%H:%M:%S')} Uhr")
