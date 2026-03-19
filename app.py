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
            r = requests.post(FORM_URL, data=payload, timeout=5)
            if r.ok:
                st.success("Erfolgreich gespeichert!")
                st.cache_data.clear()
            else:
                st.error("Google Forms Fehler.")
        except:
            st.error("Verbindung fehlgeschlagen.")

# --- DATEN LADEN ---
@st.cache_data(ttl=1)
def load_data():
    try:
        df = pd.read_csv(READ_URL)
        df = df.iloc[:, -3:].copy()
        df.columns = ["Wochentag", "Uhrzeit", "Auslastung"]
        df["Auslastung"] = pd.to_numeric(df["Auslastung"], errors='coerce').fillna(0)
        df["Uhrzeit"] = pd.to_numeric(df["Uhrzeit"], errors='coerce').fillna(0).astype(int)
        return df
    except:
        return pd.DataFrame()

df = load_data()

# --- ANALYSE ---
if not df.empty:
    st.divider()
    
    # 1. Beste Zeiten (Metriken oben)
    st.subheader("✅ Beste Zeiten (Schön leer)")
    stats_detail = df.groupby(["Wochentag", "Uhrzeit"], observed=True)["Auslastung"].mean().reset_index()
    best_times = stats_detail.sort_values(by="Auslastung", ascending=True).head(3)
    
    cols = st.columns(3)
    for i, row in enumerate(best_times.itertuples()):
        with cols[i]:
            # delta_color="normal" macht positive Zahlen hier GRÜN, da wir die Top 3 (Guten) zeigen
            st.metric(
                label=f"{row.Wochentag}", 
                value=f"{row.Uhrzeit}:00 Uhr", 
                delta=f"Level {row.Auslastung:.1f}", 
                delta_color="normal" 
            )

    # 2. Das Diagramm (Altair Grafik)
    st.subheader("📈 Auslastung im Wochenverlauf")
    chart_data = df.groupby("Wochentag", observed=True)["Auslastung"].mean().reset_index()
    tage_order = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    
    # Altair Chart mit optimiertem Handy-Layout
    chart = alt.Chart(chart_data).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
        x=alt.X('Wochentag:N', sort=tage_order, title=None, axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('Auslastung:Q', title="Durchschnitt (1-10)", scale=alt.Scale(domain=[0, 10])),
        color=alt.Color('Auslastung:Q', scale=alt.Scale(scheme='redyellowgreen', reverse=True), legend=None),
        tooltip=['Wochentag', 'Auslastung']
    ).properties(height=350)

    st.altair_chart(chart, use_container_width=True)
    
    with st.expander("Rohdaten-Tabelle"):
        st.dataframe(df, use_container_width=True)
else:
    st.info("Noch keine Daten vorhanden. Trage dein erstes Training oben ein!")
    
