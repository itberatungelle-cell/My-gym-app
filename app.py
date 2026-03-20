import streamlit as st
import pandas as pd
import requests
import altair as alt

# --- KONFIGURATION ---
# Deine brandneue Tabellen-ID
SHEET_ID = "1b9-9gcxOrF57pp4z_IkcUlsb6QHQdNBKiJ4oqbBtbCc" 
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
            weather_input = st.selectbox("Wetter heute", ["Sonne", "Bewölkt", "Regen"])
        with col2:
            time = st.slider("Uhrzeit (Stunde)", 6, 23, 17)
            crowd = st.select_slider("Wie voll war es? (1-10)", options=list(range(1, 11)), value=5)
        
        submitted = st.form_submit_button("Speichern")
        
        if submitted:
            # IDs: 2114330699 (Tag), 1688325016 (Wetter), 1094088238 (Zeit), 1741468156 (Score)
            payload = {
                "entry.2114330699": day,
                "entry.1688325016": weather_input,
                "entry.1094088238": str(time),
                "entry.1741468156": str(crowd)
            }
            try:
                r = requests.post(FORM_URL, data=payload, timeout=5)
                if r.ok:
                    st.success(f"Eintrag gespeichert: {day}, {time} Uhr bei {weather_input}!")
                    st.cache_data.clear()
                else: st.error("Fehler beim Senden an Google Forms.")
            except: st.error("Verbindungsproblem.")

# --- 2. DATEN LADEN ---
@st.cache_data(ttl=1)
def load_data():
    try:
        df = pd.read_csv(READ_URL)
        # Wir nehmen die letzten 4 Spalten der neuen Tabelle
        df = df.iloc[:, -4:].copy()
        df.columns = ["Wochentag", "Wetter", "Uhrzeit", "Auslastung"]
        
        # Datentypen bereinigen
        df["Auslastung"] = pd.to_numeric(df["Auslastung"], errors='coerce').fillna(0)
        df["Uhrzeit"] = pd.to_numeric(df["Uhrzeit"], errors='coerce').fillna(0).astype(int)
        return df
    except: return pd.DataFrame()

df = load_data()

if not df.empty:
    tage_order = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

    # --- 3. FILTER & ZEITFENSTER-CHECK ---
    st.divider()
    st.subheader("📊 Analyse & Wetter-Filter")
    
    # Multiselect für das Wetter
    selected_weather = st.multiselect(
        "Daten filtern nach Wetterlage:", 
        options=["Sonne", "Bewölkt", "Regen"], 
        default=["Sonne", "Bewölkt", "Regen"]
    )
    
    # Gefilterte Daten für die gesamte Seite
    filtered_df = df[df["Wetter"].isin(selected_weather)]

    st.subheader("🧐 Dein Zeitfenster-Check")
    c1, c2 = st.columns([1, 2])
    with c1:
        check_day = st.selectbox("Tag wählen:", tage_order)
        t_range = st.slider("Zeitspanne (z.B. 17-20 Uhr):", 6, 23, (17, 20))
    
    # Check-Logik
    check_df = filtered_df[(filtered_df["Wochentag"] == check_day) & 
                           (filtered_df["Uhrzeit"].between(t_range[0], t_range[1]))]
    
    with c2:
        if not check_df.empty:
            avg_scores = check_df.groupby("Uhrzeit")["Auslastung"].mean()
            best_h = avg_scores.idxmin()
            min_score = avg_scores.min()
            st.success(f"Beste Zeit am **{check_day}** ({', '.join(selected_weather)}):\n\n"
                       f"👉 **{int(best_h)}:00 Uhr** (Schnitt: {min_score:.1f})")
        else:
            st.info("Für diese Filter-Kombination liegen noch keine Daten vor.")

    # --- 4. VISUALISIERUNG ---
    st.subheader("🌡️ Auslastungs-Matrix (Heatmap)")
    if not filtered_df.empty:
        hm_data = filtered_df.groupby(["Wochentag", "Uhrzeit"], observed=True)["Auslastung"].mean().reset_index()
        
        heatmap = alt.Chart(hm_data).mark_rect().encode(
            x=alt.X('Wochentag:N', sort=tage_order, title=None),
            y=alt.Y('Uhrzeit:O', title="Uhrzeit", sort="descending"),
            color=alt.Color('Auslastung:Q', scale=alt.Scale(scheme='redyellowgreen', reverse=True), legend=None),
            tooltip=['Wochentag', 'Uhrzeit', 'Auslastung', 'Wetter']
        ).properties(height=400)
        
        # Zahlen in die Felder schreiben
        text = heatmap.mark_text(baseline='middle').encode(
            text=alt.Text('Auslastung:Q', format='.1f'),
            color=alt.condition(alt.datum.Auslastung > 7, alt.value('white'), alt.value('black'))
        )
        st.altair_chart(heatmap + text, use_container_width=True)
    else:
        st.warning("Bitte wähle mindestens ein Wetter im Filter aus.")

    with st.expander("Komplette Datentabelle einsehen"):
        st.dataframe(df, use_container_width=True)

else:
    st.info("Die neue Tabelle ist noch leer. Zeit für den ersten Eintrag! 🏋️")
    
