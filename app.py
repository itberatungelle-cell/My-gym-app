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
        return round(res['main']['temp'], 1), res['weather'][0]['description']
    except:
        return None, None

current_temp, current_desc = get_weather()

st.title("🏋️ Mein ultimativer Gym-Planer")
if current_temp is not None:
    st.info(f"🌡️ **Aktuell in Wilhelmsdorf:** {current_temp}°C | {current_desc.capitalize()}")

# --- 1. EINGABE ---
with st.expander("➕ Training eintragen", expanded=False):
    with st.form("gym_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            day = st.selectbox("Wochentag", ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"])
        with col2:
            time = st.slider("Uhrzeit", 6, 23, 17)
        crowd = st.select_slider("Auslastung (1=Leer, 10=Voll)", options=list(range(1, 11)), value=5)
        if st.form_submit_button("Speichern"):
            payload = {
                "entry.2114330699": day, "entry.1094088238": str(time), "entry.1741468156": str(crowd),
                "entry.1365025023": str(current_temp), "entry.1773205727": current_desc
            }
            if requests.post(FORM_URL, data=payload).ok:
                st.success("Gespeichert!"); st.cache_data.clear()

# --- 2. DATEN LADEN ---
@st.cache_data(ttl=1)
def load_data():
    try:
        df = pd.read_csv(READ_URL).iloc[:, -5:]
        df.columns = ["Wochentag", "Uhrzeit", "Auslastung", "Temperatur", "Wetter"]
        for col in ["Auslastung", "Uhrzeit", "Temperatur"]:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except: return pd.DataFrame()

df = load_data()

if not df.empty:
    tage_order = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

    # --- 3. GLOBALER WETTER-FILTER ---
    st.divider()
    wetter_filter = st.segmented_control(
        "Wetterlage auswählen (filtert alle Grafiken):", 
        options=["Alle", "☀️ Heiß (>=20°C)", "☁️ Kühl (<20°C)"], 
        default="Alle"
    )
    
    dff = df.copy()
    if "Heiß" in wetter_filter: dff = df[df["Temperatur"] >= 20]
    elif "Kühl" in wetter_filter: dff = df[df["Temperatur"] < 20]

    if dff.empty:
        st.warning("Keine Daten für diese Wetterlage vorhanden.")
    else:
        # --- 4. ZEITFENSTER-CHECK (Wunsch von vorhin) ---
        st.subheader("🧐 Dein persönlicher Check")
        c1, c2, c3 = st.columns([1, 1, 1.5])
        with c1: check_day = st.selectbox("Tag:", tage_order)
        with c2: t_range = st.slider("Zeitfenster:", 6, 23, (17, 20))
        
        check_df = dff[(dff["Wochentag"] == check_day) & (dff["Uhrzeit"].between(t_range[0], t_range[1]))]
        with c3:
            if not check_df.empty:
                best = check_df.groupby("Uhrzeit")["Auslastung"].mean().idxmin()
                st.success(f"Beste Zeit: **{int(best)}:00 Uhr**")
            else: st.write("Keine Daten im Fenster.")

        # --- 5. HEATMAP ---
        st.subheader("🌡️ Auslastungs-Matrix")
        hm_data = dff.groupby(["Wochentag", "Uhrzeit"])["Auslastung"].mean().reset_index()
        base = alt.Chart(hm_data).encode(
            x=alt.X('Wochentag:N', sort=tage_order, title=None),
            y=alt.Y('Uhrzeit:O', title="Uhrzeit", sort="descending")
        )
        heatmap = base.mark_rect().encode(
            color=alt.Color('Auslastung:Q', scale=alt.Scale(scheme='redyellowgreen', reverse=True), legend=None)
        )
        text = base.mark_text(baseline='middle').encode(
            text=alt.Text('Auslastung:Q', format='.1f'),
            color=alt.condition(alt.datum.Auslastung > 7, alt.value('white'), alt.value('black'))
        )
        st.altair_chart(heatmap + text, use_container_width=True)

        # --- 6. WOCHENVERLAUF ---
        st.subheader("📈 Durchschnitt pro Tag")
        bar_data = dff.groupby("Wochentag")["Auslastung"].mean().reset_index()
        bars = alt.Chart(bar_data).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X('Wochentag:N', sort=tage_order, title=None),
            y=alt.Y('Auslastung:Q', title="Score", scale=alt.Scale(domain=[0, 10])),
            color=alt.Color('Auslastung:Q', scale=alt.Scale(scheme='redyellowgreen', reverse=True), legend=None)
        ).properties(height=250)
        st.altair_chart(bars, use_container_width=True)

    with st.expander("Rohdaten"):
        st.dataframe(df)
else:
    st.info("Bitte erste Daten eintragen!")
    
