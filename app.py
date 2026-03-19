import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gym-Tracker Cloud", page_icon="🏋️")
st.title("🏋️ Gym-Flow Tracker (Cloud)")

# --- KONFIGURATION ---
# WICHTIG: Deine Google Sheet URL muss am Ende "/export?format=csv" haben!
# Beispiel: https://docs.google.com/spreadsheets/d/1ABC...XYZ/export?format=csv
sheet_id = "DEINE_SHEET_ID_HIER" # Die lange Zeichenfolge in deiner Browser-URL
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

# Daten laden
@st.cache_data(ttl=60) # Cache für 60 Sekunden, damit es schnell lädt
def load_data(csv_url):
    try:
        return pd.read_csv(csv_url)
    except:
        return pd.DataFrame(columns=["Wochentag", "Uhrzeit", "Auslastung"])

data = load_data(url)

# --- EINGABE ---
with st.form("entry_form"):
    st.subheader("Neuen Besuch eintragen")
    day = st.selectbox("Wochentag", ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"])
    time = st.slider("Uhrzeit", 6, 23, 17)
    crowd = st.select_slider("Auslastung (1-10)", options=list(range(1, 11)))
    
    submitted = st.form_submit_button("Speichern")
    if submitted:
        # Hier ist der Trick: Wir leiten den User kurz zum Google Formular 
        # oder wir nutzen eine einfachere Schreibmethode.
        # Da GSheets-Update oft Rechte-Probleme hat, hier die stabilste Methode:
        st.warning("Google blockiert oft das direkte Schreiben ohne Passwort.")
        st.info("Klicke auf den Link unten, um die Daten direkt in deine Tabelle einzutragen:")
        
        # Link zur manuellen Korrektur oder zum Sheet
        st.markdown(f"[👉 Hier klicken, um manuell im Sheet einzutragen](https://docs.google.com/spreadsheets/d/{sheet_id})")
        
        # Testweise lokale Speicherung für die aktuelle Session
        new_entry = pd.DataFrame([[day, time, crowd]], columns=["Wochentag", "Uhrzeit", "Auslastung"])
        data = pd.concat([data, new_entry], ignore_index=True)
        st.success("In der aktuellen Ansicht hinzugefügt!")

# --- AUSWERTUNG ---
if not data.empty:
    st.divider()
    st.subheader("📊 Deine Statistiken")
    # Stelle sicher, dass Auslastung eine Zahl ist
    data["Auslastung"] = pd.to_numeric(data["Auslastung"], errors='coerce')
    avg_data = data.groupby(["Wochentag", "Uhrzeit"])["Auslastung"].mean().reset_index()
    best_times = avg_data.sort_values(by="Auslastung")

    st.write("Die leersten Zeiten bisher:")
    for i, row in best_times.head(3).iterrows():
        st.info(f"📍 {row['Wochentag']} um {row['Uhrzeit']}:00 | Score: {row['Auslastung']:.1f}")
        
