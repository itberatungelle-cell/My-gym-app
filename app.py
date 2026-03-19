import streamlit as st
import pandas as pd
import os

# Datei für die Daten
DATA_FILE = "gym_data.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["Wochentag", "Uhrzeit", "Auslastung"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

st.set_page_config(page_title="Gym-Checker", page_icon="🏋️")
st.title("🏋️ Gym-Flow Tracker")

data = load_data()

# --- EINGABE ---
with st.form("entry_form"):
    st.subheader("Neuen Besuch eintragen")
    day = st.selectbox("Wochentag", ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"])
    time = st.slider("Uhrzeit (Stunde)", 6, 23, 17)
    crowd = st.select_slider("Wie voll war es?", options=list(range(1, 11)))
    
    submitted = st.form_submit_button("Speichern")
    if submitted:
        new_entry = pd.DataFrame([[day, time, crowd]], columns=["Wochentag", "Uhrzeit", "Auslastung"])
        data = pd.concat([data, new_entry], ignore_index=True)
        save_data(data)
        st.success(f"Eingetragen: {day} um {time} Uhr (Level {crowd})")

# --- AUSWERTUNG ---
if not data.empty:
    st.divider()
    st.subheader("📊 Deine besten Zeiten")
    
    # Durchschnittliche Auslastung berechnen
    avg_data = data.groupby(["Wochentag", "Uhrzeit"])["Auslastung"].mean().reset_index()
    best_times = avg_data.sort_values(by="Auslastung")

    # Anzeige der Top-Zeiten
    for i, row in best_times.head(3).iterrows():
        st.info(f"📍 **{row['Wochentag']}** um **{row['Uhrzeit']}:00** | Score: **{row['Auslastung']:.1f}/10**")
    
    if st.checkbox("Alle Daten einsehen"):
        st.table(data)
else:
    st.info("Trage ein paar Trainings ein, um Statistiken zu sehen!")
  
