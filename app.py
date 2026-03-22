import streamlit as st
import pandas as pd
import requests
import altair as alt
from datetime import datetime, timedelta

# --- KONFIGURATION ---
SHEET_ID = "1b9-9gcxOrF57pp4z_IkcUlsb6QHQdNBKiJ4oqbBtbCc" 
READ_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScLmlWy29EqqOpN--6EOEb_QlnxiarS24vKbj1bAs1nZhqEzg/formResponse"

st.set_page_config(page_title="Gym Tracker", page_icon="🏋️", layout="wide")
st.title("🏋️ Mein Gym-Flow Tracker")

# --- AUTOMATISCHE ZEITZONEN-LOGIK (DEUTSCHLAND) ---
def get_german_time():
    now_utc = datetime.utcnow()
    
    # Bestimmung der Sommerzeit (Letzter Sonntag im März bis letzter Sonntag im Oktober)
    # Einfache Logik für den Hausgebrauch:
    year = now_utc.year
    # Sommerzeit beginnt am letzten Sonntag im März
    dst_start = datetime(year, 3, 31) - timedelta(days=(datetime(year, 3, 31).weekday() + 1) % 7)
    # Sommerzeit endet am letzten Sonntag im Oktober
    dst_end = datetime(year, 10, 31) - timedelta(days=(datetime(year, 10, 31).weekday() + 1) % 7)
    
    if dst_start <= now_utc < dst_end:
        offset = 2 # Sommerzeit (MESZ)
    else:
        offset = 1 # Winterzeit (MEZ)
        
    german_time = now_utc + timedelta(hours=offset)
    days_de = {0: "Montag", 1: "Dienstag", 2: "Mittwoch", 3: "Donnerstag", 4: "Freitag", 5: "Samstag", 6: "Sonntag"}
    return days_de[german_time.weekday()], german_time.hour

current_day_de, current_hour = get_german_time()

# --- 1. EINGABE-BEREICH ---
with st.expander("➕ Neues Training eintragen", expanded=False):
    with st.form("gym_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            tage_liste = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
            day = st.selectbox("Wochentag", tage_liste, index=tage_liste.index(current_day_de))
            weather_input = st.selectbox("Wetter heute", ["Sonne", "Bewölkt", "Regen"])
        with col2:
            # Nutzt die berechnete deutsche Stunde
            time = st.slider("Uhrzeit (Stunde)", 6, 23, value=min(max(current_hour, 6), 23))
            crowd = st.select_slider("Wie voll war es? (1-10)", options=list(range(1, 11)), value=5)
        
        if st.form_submit_button("Speichern"):
            payload = {
                "entry.2114330699": day,
                "entry.1688325016": weather_input,
                "entry.1094088238": str(time),
                "entry.1741468156": str(crowd)
            }
            try:
                r = requests.post(FORM_URL, data=payload, timeout=5)
                if r.ok:
                    st.success(f"Eintrag für {time}:00 Uhr erfolgreich!")
                    st.cache_data.clear()
                else: st.error("Fehler beim Senden.")
            except: st.error("Verbindungsproblem.")

# --- 2. DATEN LADEN ---
@st.cache_data(ttl=1)
def load_data():
    try:
        df = pd.read_csv(READ_URL)
        if df.empty: return pd.DataFrame()
        df = df.iloc[:, -4:].copy()
        df.columns = ["Wochentag", "Wetter", "Uhrzeit", "Auslastung"]
        df["Auslastung"] = pd.to_numeric(df["Auslastung"], errors='coerce').fillna(0)
        df["Uhrzeit"] = pd.to_numeric(df["Uhrzeit"], errors='coerce').fillna(0).astype(int)
        return df
    except: return pd.DataFrame()

df = load_data()

# --- 3. ANALYSE ---
if not df.empty:
    tage_order = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    
    st.divider()
    st.subheader("📊 Wetter-Filter & Zeit-Check")
    selected_weather = st.multiselect("Wetterlage:", ["Sonne", "Bewölkt", "Regen"], default=["Sonne", "Bewölkt", "Regen"])
    filtered_df = df[df["Wetter"].isin(selected_weather)]

    # --- ZEITFENSTER-CHECK ---
    c1, c2 = st.columns([1, 2])
    with c1:
        check_day = st.selectbox("Tag:", tage_order, index=tage_order.index(current_day_de))
        # Startet automatisch bei der aktuellen Stunde
        t_range = st.slider("Prognose für Zeitraum:", 6, 23, (min(max(current_hour, 6), 22), 23))
    
    check_df = filtered_df[(filtered_df["Wochentag"] == check_day) & (filtered_df["Uhrzeit"].between(t_range[0], t_range[1]))]
    with c2:
        if not check_df.empty:
            avg_scores = check_df.groupby("Uhrzeit")["Auslastung"].mean()
            best_h = avg_scores.idxmin()
            st.success(f"Beste Zeit heute: **{int(best_h)}:00 Uhr**")
        else: st.info("Noch keine Daten vorhanden.")

    # --- HEATMAP ---
    st.subheader("🌡️ Auslastungs-Matrix")
    if not filtered_df.empty:
        hm_data = filtered_df.groupby(["Wochentag", "Uhrzeit"], observed=True)["Auslastung"].mean().reset_index()
        if not hm_data.empty:
            heatmap = alt.Chart(hm_data).mark_rect().encode(
                x=alt.X('Wochentag:N', sort=tage_order, title=None),
                y=alt.Y('Uhrzeit:O', title="Uhrzeit", sort="descending"),
                color=alt.Color('Auslastung:Q', scale=alt.Scale(scheme='redyellowgreen', reverse=True), legend=None),
                tooltip=['Wochentag', 'Uhrzeit', 'Auslastung']
            ).properties(height=400)
            
            text = heatmap.mark_text(baseline='middle').encode(
                text=alt.Text('Auslastung:Q', format='.1f'),
                color=alt.condition(alt.datum.Auslastung > 7, alt.value('white'), alt.value('black'))
            )
            st.altair_chart(heatmap + text, use_container_width=True)

    with st.expander("Rohdaten anzeigen"):
        st.dataframe(df)
else:
    st.info("Trage dein erstes Training ein, um die Analyse zu starten!")
    
