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

# --- EINGABE-BEREICH ---
with st.expander("➕ Neues Training eintragen", expanded=False):
    with st.form("gym_form", clear_on_submit=True):
        day = st.selectbox("Wochentag", ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"])
        time = st.slider("Uhrzeit (Stunde)", 6, 23, 17)
        crowd = st.select_slider("Wie voll war es? (1=Leer, 10=Voll)", options=list(range(1, 11)), value=5)
        submitted = st.form_submit_button("Speichern")
        
        if submitted:
            payload = {"entry.2114330699": day, "entry.1094088238": str(time), "entry.1741468156": str(crowd)}
            try:
                r = requests.post(FORM_URL, data=payload, timeout=5)
                if r.ok:
                    st.success("Gespeichert!")
                    st.cache_data.clear()
                else: st.error("Fehler.")
            except: st.error("Verbindungsproblem.")

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
    except: return pd.DataFrame()

df = load_data()

if not df.empty:
    tage_order = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    
    # --- 1. SCHNELLER VERGLEICH (DEINE FRAGE) ---
    st.divider()
    st.subheader("🧐 Wann soll ich gehen?")
    col_a, col_b = st.columns([1, 2])
    
    with col_a:
        check_day = st.selectbox("Wähle einen Tag:", tage_order)
    
    day_data = df[df["Wochentag"] == check_day]
    if not day_data.empty:
        # Durchschnitt pro Stunde für den gewählten Tag
        hourly_avg = day_data.groupby("Uhrzeit")["Auslastung"].mean().reset_index()
        best_hour = hourly_avg.loc[hourly_avg["Auslastung"].idxmin()]
        
        with col_b:
            st.info(f"Am **{check_day}** ist es um **{int(best_hour['Uhrzeit'])}:00 Uhr** am leersten (Score: {best_hour['Auslastung']:.1f}).")

    # --- 2. DIE HEATMAP (ALLE ZEITEN AUF EINEN BLICK) ---
    st.subheader("🌡️ Auslastungs-Matrix (Heatmap)")
    
    # Daten für Heatmap vorbereiten
    heatmap_data = df.groupby(["Wochentag", "Uhrzeit"], observed=True)["Auslastung"].mean().reset_index()
    
    heatmap = alt.Chart(heatmap_data).mark_rect().encode(
        x=alt.X('Wochentag:N', sort=tage_order, title=None),
        y=alt.Y('Uhrzeit:O', title="Uhrzeit", sort="descending"),
        color=alt.Color('Auslastung:Q', 
                        scale=alt.Scale(scheme='redyellowgreen', reverse=True),
                        title="Auslastung"),
        tooltip=['Wochentag', 'Uhrzeit', 'Auslastung']
    ).properties(height=400)
    
    # Text-Labels in die Heatmap schreiben (Scores anzeigen)
    text = heatmap.mark_text(baseline='middle').encode(
        text=alt.Text('Auslastung:Q', format='.1f'),
        color=alt.condition(
            alt.datum.Auslastung > 7,
            alt.value('white'),
            alt.value('black')
        )
    )
    
    st.altair_chart(heatmap + text, use_container_width=True)

    # --- 3. BESTE ZEITEN (FIX: OHNE ROT) ---
    st.subheader("✅ Top 3 Geheimtipps")
    best_times = heatmap_data.sort_values(by="Auslastung").head(3)
    cols = st.columns(3)
    for i, row in enumerate(best_times.itertuples()):
        with cols[i]:
            # Wir nutzen keine Deltas mehr, um das Rot zu vermeiden. 
            # Stattdessen ein schönes grünes Info-Feld.
            st.success(f"**{row.Wochentag}**\n\n**{int(row.Uhrzeit)}:00 Uhr**\n\nScore: {row.Auslastung:.1f}")

    # --- 4. WOCHENVERLAUF (DEINE LIEBLINGSGRAFIK) ---
    st.subheader("📈 Durchschnitt pro Tag")
    line_data = df.groupby("Wochentag", observed=True)["Auslastung"].mean().reset_index()
    chart = alt.Chart(line_data).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
        x=alt.X('Wochentag:N', sort=tage_order, title=None),
        y=alt.Y('Auslastung:Q', title="Score", scale=alt.Scale(domain=[0, 10])),
        color=alt.Color('Auslastung:Q', scale=alt.Scale(scheme='redyellowgreen', reverse=True), legend=None)
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)

else:
    st.info("Noch keine Daten vorhanden.")
    
