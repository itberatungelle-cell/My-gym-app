import streamlit as st
import pandas as pd
import requests

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
                st.cache_data.clear()
            else:
                st.error(f"Fehler bei Google ({response.status_code})")
        except:
            st.error("Verbindung fehlgeschlagen.")

# --- DATEN LADEN & VORBEREITEN ---
@st.cache_data(ttl=1)
def load_data():
    try:
        df = pd.read_csv(READ_URL)
        df = df.iloc[:, -3:].copy()
        df.columns = ["Wochentag", "Uhrzeit", "Auslastung"]
        
        df["Auslastung"] = pd.to_numeric(df["Auslastung"], errors='coerce').fillna(0)
        df["Uhrzeit"] = pd.to_numeric(df["Uhrzeit"], errors='coerce').fillna(0).astype(int)
        
        # Mapping für die harte Sortierung (Mo=0, Di=1...)
        tage_map = {"Montag": 0, "Dienstag": 1, "Mittwoch": 2, "Donnerstag": 3, "Freitag": 4, "Samstag": 5, "Sonntag": 6}
        df["TagNummer"] = df["Wochentag"].map(tage_map)
        
        return df
    except:
        return pd.DataFrame()

df = load_data()

# --- ANALYSE ANZEIGEN ---
if not df.empty:
    st.divider()
    st.subheader("📊 Deine Analyse")

    # 1. Top 3 Empfehlungen
    best_stats = df.groupby(["Wochentag", "Uhrzeit", "TagNummer"], observed=True)["Auslastung"].mean().reset_index()
    best_times = best_stats.sort_values(by="Auslastung", ascending=True)
    
    st.write("Die besten Zeiten zum Trainieren:")
    cols = st.columns(3)
    
    for i, row in enumerate(best_times.head(3).itertuples()):
        with cols[i]:
            # Wir nutzen "normal" aber drehen die Logik manuell, damit kleine Werte GRÜN werden
            st.metric(
                label=str(row.Wochentag), 
                value=f"{row.Uhrzeit}:00 Uhr", 
                delta=f"{row.Auslastung:.1f} Score", 
                delta_color="inverse"
            )
    
    # 2. Visuelles Diagramm (Harte Sortierung über TagNummer)
    st.write("### Auslastung im Wochenverlauf")
    
    # Wir gruppieren nach Nummer und Tagname, sortieren nach Nummer und nehmen dann den Namen als Index
    chart_stats = df.groupby(["TagNummer", "Wochentag"], observed=True)["Auslastung"].mean().reset_index()
    chart_stats = chart_stats.sort_values("TagNummer")
    
    # Das Diagramm braucht den Namen als Index für die Beschriftung
    chart_final = chart_stats.set_index("Wochentag")["Auslastung"]
    
    st.bar_chart(chart_final)

    with st.expander("Alle Einträge anzeigen"):
        st.dataframe(df.sort_values("TagNummer"), use_container_width=True)
else:
    st.info("Noch keine Daten vorhanden.")
    
