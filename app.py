import streamlit as st
import pandas as pd
import requests
import altair as alt

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
        try:
            r = requests.post(FORM_URL, data=payload)
            if r.ok:
                st.success("Gespeichert!")
                st.balloons()
                st.cache_data.clear()
            else:
                st.error("Fehler beim Senden.")
        except:
            st.error("Verbindungsproblem.")

# --- DATEN LADEN ---
@st.cache_data(ttl=1)
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
    
    # 1. Top 3 Metriken (Fix: Niedrig = Grün)
    stats_detail = df.groupby(["Wochentag", "Uhrzeit"], observed=True)["Auslastung"].mean().reset_index()
    best_times = stats_detail.sort_values(by="Auslastung", ascending=True).head(3)
    
    st.subheader("📊 Beste Zeiten")
    cols = st.columns(3)
    for i, row in enumerate(best_times.itertuples()):
        with cols[i]:
            # delta_color="inverse" macht kleine Zahlen GRÜN
            st.metric(label=str(row.Wochentag), value=f"{row.Uhrzeit}:00", delta=f"Score {row.Auslastung:.1f}", delta_color="inverse")

    # 2. DAS DIAGRAMM (Altair fixiert die Sortierung)
    st.subheader("📈 Auslastung im Wochenverlauf")
    chart_data = df.groupby("Wochentag", observed=True)["Auslastung"].mean().reset_index()
    
    # Hier wird die Sortierung knallhart festgelegt:
    tage_order = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    
    chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X('Wochentag:N', sort=tage_order, title="Tag"),
        y=alt.Y('Auslastung:Q', title="Durchschnitt"),
        color=alt.Color('Auslastung:Q', scale=alt.Scale(scheme='yellowgreenred'), legend=None),
        tooltip=['Wochentag', 'Auslastung']
    ).properties(height=300)

    st.altair_chart(chart, use_container_width=True)
    
    with st.expander("Daten-Tabelle"):
        st.write(df)
else:
    st.info("Noch keine Daten vorhanden.")
    
