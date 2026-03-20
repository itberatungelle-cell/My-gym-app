import streamlit as st
import pandas as pd
import requests
import altair as alt

# --- KONFIGURATION ---
# Die neue ID deiner sauberen Tabelle
SHEET_ID = "1uaia-yDeIbjpZZmEyyd8vZrPRHPTCyS8UKGkkbH4N0Q" 
READ_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"
# Die Form-URL bleibt gleich, da das Formular ja noch dasselbe ist
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
                    st.success("Gespeichert!")
                    st.cache_data.clear()
                else: st.error("Fehler beim Senden.")
            except: st.error("Verbindungsproblem.")

# --- 2. DATEN LADEN ---
@st.cache_data(ttl=1)
def load_data():
    try:
        df = pd.read_csv(READ_URL)
        # Wir nehmen die letzten 3 Spalten (Tag, Uhrzeit, Auslastung)
        # Da die Tabelle neu ist, sollte hier nichts mehr verschoben sein
        df = df.iloc[:, -3:].copy()
        df.columns = ["Wochentag", "Uhrzeit", "Auslastung"]
        df["Auslastung"] = pd.to_numeric(df["Auslastung"], errors='coerce').fillna(0)
        df["Uhrzeit"] = pd.to_numeric(df["Uhrzeit"], errors='coerce').fillna(0).astype(int)
        return df
    except: return pd.DataFrame()

df = load_data()

if not df.empty:
    tage_order = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

    # --- 3. ZEITFENSTER-CHECK ---
    st.divider()
    st.subheader("🧐 Dein Zeitfenster-Check")
    col_a, col_b, col_c = st.columns([1, 1, 1.5])
    
    with col_a:
        check_day = st.selectbox("Wähle einen Tag:", tage_order)
    with col_b:
        time_range = st.slider("Zeitspanne:", 6, 23, (17, 20))
    
    filtered_df = df[(df["Wochentag"] == check_day) & (df["Uhrzeit"].between(time_range[0], time_range[1]))]
    
    with col_c:
        if not filtered_df.empty:
            best_hour = filtered_df.groupby("Uhrzeit")["Auslastung"].mean().idxmin()
            score = filtered_df.groupby("Uhrzeit")["Auslastung"].mean().min()
            st.success(f"Am **{check_day}** ist **{int(best_hour)}:00 Uhr** am besten! (Score: {score:.1f})")
        else:
            st.info("Noch keine Daten für diesen Bereich vorhanden.")

    # --- 4. HEATMAP ---
    st.subheader("🌡️ Auslastungs-Matrix (Heatmap)")
    hm_data = df.groupby(["Wochentag", "Uhrzeit"], observed=True)["Auslastung"].mean().reset_index()
    
    chart = alt.Chart(hm_data).mark_rect().encode(
        x=alt.X('Wochentag:N', sort=tage_order, title=None),
        y=alt.Y('Uhrzeit:O', title="Uhrzeit", sort="descending"),
        color=alt.Color('Auslastung:Q', scale=alt.Scale(scheme='redyellowgreen', reverse=True), legend=None),
        tooltip=['Wochentag', 'Uhrzeit', 'Auslastung']
    ).properties(height=400)
    
    text = chart.mark_text(baseline='middle').encode(
        text=alt.Text('Auslastung:Q', format='.1f'),
        color=alt.condition(alt.datum.Auslastung > 7, alt.value('white'), alt.value('black'))
    )
    st.altair_chart(chart + text, use_container_width=True)

    # --- 5. WOCHENVERLAUF ---
    st.subheader("📈 Durchschnitt pro Tag")
    bar_data = df.groupby("Wochentag", observed=True)["Auslastung"].mean().reset_index()
    bars = alt.Chart(bar_data).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
        x=alt.X('Wochentag:N', sort=tage_order),
        y=alt.Y('Auslastung:Q', title="Score", scale=alt.Scale(domain=[0, 10])),
        color=alt.Color('Auslastung:Q', scale=alt.Scale(scheme='redyellowgreen', reverse=True), legend=None)
    ).properties(height=250)
    st.altair_chart(bars, use_container_width=True)

    with st.expander("Rohdaten anzeigen"):
        st.dataframe(df, use_container_width=True)

else:
    st.info("Die neue Tabelle ist noch leer. Trag dein erstes Training ein!")
    
