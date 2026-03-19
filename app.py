import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Gym-Tracker Cloud", page_icon="🏋️")
st.title("🏋️ Gym-Flow Tracker (Cloud)")

# Verbindung zu Google Sheets herstellen
# Ersetze den Link unten durch DEINEN Google Sheets Link!
url = "https://docs.google.com/spreadsheets/d/160eAiq0CW9p8py6GhbkVMdABXtoB3ANtoh1ez1dpZ_4/edit?usp=drivesdk"

conn = st.connection("gsheets", type=GSheetsConnection)

# Daten laden
try:
    data = conn.read(spreadsheet=url, usecols=[0, 1, 2])
    data = data.dropna(how="all")
except:
    data = pd.DataFrame(columns=["Wochentag", "Uhrzeit", "Auslastung"])

# --- EINGABE ---
with st.form("entry_form"):
    st.subheader("Neuen Besuch eintragen")
    day = st.selectbox("Wochentag", ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"])
    time = st.slider("Uhrzeit", 6, 23, 17)
    crowd = st.select_slider("Auslastung (1-10)", options=list(range(1, 11)))
    
    if st.form_submit_button("In Google Sheets speichern"):
        new_entry = pd.DataFrame([[day, time, crowd]], columns=["Wochentag", "Uhrzeit", "Auslastung"])
        updated_data = pd.concat([data, new_entry], ignore_index=True)
        
        # In Google Sheets schreiben
        conn.update(spreadsheet=url, data=updated_data)
        st.success("Erfolgreich in Google Sheets gespeichert!")
        st.balloons()
        data = updated_data

# --- AUSWERTUNG ---
if not data.empty:
    st.divider()
    st.subheader("📊 Deine Statistiken")
    avg_data = data.groupby(["Wochentag", "Uhrzeit"])["Auslastung"].mean().reset_index()
    best_times = avg_data.sort_values(by="Auslastung")

    st.write("Die leersten Zeiten bisher:")
    for i, row in best_times.head(3).iterrows():
        st.info(f"📍 {row['Wochentag']} um {row['Uhrzeit']}:00 | Score: {row['Auslastung']:.1f}")
        
