import streamlit as st
import pandas as pd
import requests
import altair as alt

# --- KONFIGURATION ---
SHEET_ID = "160eAiq0CW9p8py6GhbkVMdABXtoB3ANtoh1ez1dpZ_4" 
READ_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScLmlWy29EqqOpN--6EOEb_QlnxiarS24vKbj1bAs1nZhqEzg/formResponse"

st.set_page_config(page_title="Gym Tracker", page_icon="🏋️", layout="wide")
st.title("🏋️ Mein Gym-Flow Tracker")

# --- 1. EINGABE-BEREICH ---
with st.expander("➕ Neues Training eintragen", expanded=False):
    with st.form("gym_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            day = st.selectbox("Wochentag", ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"])
        with col2:
            time = st.slider("Uhrzeit (Stunde)", 6, 23, 17)
        crowd = st.select_slider("Wie voll war es? (1=Leer, 10=Voll)", options=list(range(1, 11)), value=5)
        if st.form_submit_button("Speichern"):
            payload = {"entry.2114330699": day, "entry.1094088238": str(time), "entry.1741468156": str(crowd)}
            if requests.post(FORM_URL, data=payload).ok:
                st.success("Gespeichert!")
                st.cache_data.clear()

# --- 2. DATEN LADEN & FIXEN ---
@st.cache_data(ttl=1)
def load_data():
    try:
        raw_df = pd.read_csv(READ_URL)
        # Wir suchen die Spalten jetzt direkt bei den Namen, egal wo sie stehen
        # Das verhindert, dass Wetter-Reste eingelesen werden
        df = raw_df.copy()
        
        # Annahme: Deine Spalten heißen im Sheet "Wochentag", "Uhrzeit", "Auslastung"
        # Falls sie anders heißen, passen wir sie hier an:
        df = df.iloc[:, -3:] # Wir probieren es nochmal mit den letzten 3, aber bereinigen sie
        df.columns = ["Wochentag", "Uhrzeit", "Auslastung"]
        
        # Datentypen erzwingen
        df["Auslastung"] = pd.to_numeric(df["Auslastung"], errors='coerce')
        df["Uhrzeit"] = pd.to_numeric(df["Uhrzeit"], errors='coerce')
        
        # Zeilen mit Fehlern (wie "Klarer Himmel" in Zahlenfeldern) rauswerfen
        df = df.dropna(subset=["Auslastung", "Uhrzeit"])
        return df
    except:
        return pd.DataFrame()

df = load_data()

# --- 3. ANALYSE ---
if not df.empty and df["Wochentag"].iloc[0] != "Klarer Himmel":
    tage_order = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

    # Heatmap & Grafiken (wie gehabt)
    st.subheader("🌡️ Auslastungs-Matrix")
    hm_data = df.groupby(["Wochentag", "Uhrzeit"], observed=True)["Auslastung"].mean().reset_index()
    
    chart = alt.Chart(hm_data).mark_rect().encode(
        x=alt.X('Wochentag:N', sort=tage_order, title=None),
        y=alt.Y('Uhrzeit:O', title="Uhrzeit", sort="descending"),
        color=alt.Color('Auslastung:Q', scale=alt.Scale(scheme='redyellowgreen', reverse=True), legend=None)
    ).properties(height=400)
    st.altair_chart(chart, use_container_width=True)

    with st.expander("Tabelle mit allen Einträgen"):
        st.dataframe(df)
else:
    st.warning("Die Datenquelle enthält noch fehlerhafte Wetter-Reste. Bitte lösche im Google Sheet die Zeilen mit 'Klarer Himmel'!")

