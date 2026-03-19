import streamlit as st
import pandas as pd
import requests
import altair as alt

# --- KONFIGURATION ---
SHEET_ID = "160eAiq0CW9p8py6GhbkVMdABXtoB3ANtoh1ez1dpZ_4" 
READ_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScLmlWy29EqqOpN--6EOEb_QlnxiarS24vKbj1bAs1nZhqEzg/formResponse"
WEATHER_KEY = "48136aa9c01e220c6a1f77bf4b3d1898"
CITY = "Wilhelmsdorf,DE"

st.set_page_config(page_title="Gym Tracker Pro", page_icon="🏋️", layout="wide")

# --- WETTER FUNKTION ---
def get_weather():
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_KEY}&units=metric&lang=de"
        res = requests.get(url, timeout=5).json()
        temp = res['main']['temp']
        desc = res['weather'][0]['description']
        return round(temp, 1), desc
    except:
        return None, None

current_temp, current_desc = get_weather()

st.title("🏋️ Gym-Flow & Wetter Tracker")
if current_temp is not None:
    st.info(f"📍 **Wilhelmsdorf:** {current_temp}°C | {current_desc.capitalize()}")

# --- EINGABE-BEREICH ---
with st.expander("➕ Neues Training eintragen", expanded=True):
    with st.form("gym_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            day = st.selectbox("Wochentag", ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"])
        with col2:
            time = st.slider("Uhrzeit (Stunde)", 6, 23, 17)
            
        crowd = st.select_slider("Wie voll war es? (1=Leer, 10=Voll)", options=list(range(1, 11)), value=5)
        
        submitted = st.form_submit_button("Training Speichern")
        
        if submitted:
            payload = {
                "entry.2114330699": day,
                "entry.1094088238": str(time),
                "entry.1741468156": str(crowd),
                "entry.1365025023": str(current_temp) if current_temp else "N/A",
                "entry.1773205727": current_desc if current_desc else "N/A"
            }
            try:
                r = requests.post(FORM_URL, data=payload, timeout=5)
                if r.ok:
                    st.success(f"Gespeichert! ({day}, {time} Uhr, {current_temp}°C)")
                    st.cache_data.clear()
                else:
                    st.error("Fehler beim Senden an Google.")
            except:
                st.error("Verbindungsproblem.")

# --- DATEN LADEN ---
@st.cache_data(ttl=1)
def load_data():
    try:
        df = pd.read_csv(READ_URL)
        # Wir nehmen die letzten 5 Spalten aus dem Sheet
        df = df.iloc[:, -5:].copy()
        df.columns = ["Wochentag", "Uhrzeit", "Auslastung", "Temperatur", "Wetter"]
        df["Auslastung"] = pd.to_numeric(df["Auslastung"], errors='coerce').fillna(0)
        df["Uhrzeit"] = pd.to_numeric(df["Uhrzeit"], errors='coerce').fillna(0).astype(int)
        df["Temperatur"] = pd.to_numeric(df["Temperatur"], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame()

df = load_data()

# --- ANALYSE ---
if not df.empty:
    tage_order = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    
    st.divider()
    st.subheader("☀️ Wetter-Einfluss Analyse")
    
    wetter_filter = st.radio(
        "Daten filtern:", 
        ["Alle Tage", "Schönes Wetter (>= 20°C)", "Kühles Wetter (< 20°C)"], 
        horizontal=True
    )
    
    # Filter-Logik
    if "Schönes" in wetter_filter:
        display_df = df[df["Temperatur"] >= 20]
    elif "Kühles" in wetter_filter:
        display_df = df[df["Temperatur"] < 20]
    else:
        display_df = df

    if not display_df.empty:
        # Heatmap
        heatmap_data = display_df.groupby(["Wochentag", "Uhrzeit"], observed=True)["Auslastung"].mean().reset_index()
        
        chart = alt.Chart(heatmap_data).mark_rect().encode(
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
        
        # Beste Zeit im Filter
        best_row = heatmap_data.loc[heatmap_data["Auslastung"].idxmin()]
        st.success(f"💡 Tipp für dieses Wetter: **{best_row['Wochentag']}** um **{int(best_row['Uhrzeit'])}:00 Uhr** ist es am leersten.")
    else:
        st.warning("Noch keine Daten für diese Wetterlage gespeichert.")

    with st.expander("Vollständige Tabelle anzeigen"):
        st.dataframe(df, use_container_width=True)
else:
    st.info("Noch keine Daten vorhanden. Fang an zu tracken!")
    
