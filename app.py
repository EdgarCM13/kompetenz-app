import os
import json
import streamlit as st
from groq import Groq

# Setările paginii web
st.set_page_config(page_title="Kompetenzanalyse", page_icon="📊", layout="centered")

st.title("📊 Kompetenzanalyse")
st.markdown("Kostenloses digitales Instrument für die fortgeschrittene Kompetenzanalyse und Erstellung professioneller Aktionspläne.")

# Accesarea cheii secrete pentru Groq
api_key = st.secrets.get("GROQ_API_KEY")

if not api_key:
    st.error("Fehler: Der API-Key fehlt in den Secrets der Anwendung (GROQ_API_KEY).")
    client = None
else:
    client = Groq(api_key=api_key)

# -------------------------------------------------------------------------
# Session State Initialisierung pentru a păstra datele la reîncărcare/resetare
# -------------------------------------------------------------------------
if "domeniu" not in st.session_state:
    st.session_state.domeniu = ""
if "vechime" not in st.session_state:
    st.session_state.vechime = ""
if "educatie" not in st.session_state:
    st.session_state.educatie = ""
if "obiective" not in st.session_state:
    st.session_state.obiective = ""
if "observatii" not in st.session_state:
    st.session_state.observatii = ""
if "raport" not in st.session_state:
    st.session_state.raport = ""

# -------------------------------------------------------------------------
# Sidebar: Funcționalități de Salvare și Încărcare (Import / Export JSON)
# -------------------------------------------------------------------------
st.sidebar.header("📁 Datenverwaltung")

uploaded_file = st.sidebar.file_uploader("Gespeicherte Analyse laden (JSON)", type=["json"])
if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        st.session_state.domeniu = data.get("domeniu", "")
        st.session_state.vechime = data.get("vechime", "")
        st.session_state.educatie = data.get("educatie", "")
        st.session_state.obiective = data.get("obiective", "")
        st.session_state.observatii = data.get("observatii", "")
        st.session_state.raport = data.get("raport", "")
        st.sidebar.success("Daten erfolgreich geladen!")
    except Exception as e:
        st.sidebar.error(f"Fehler beim Laden der Datei: {e}")

# -------------------------------------------------------------------------
# Formularul principal
# -------------------------------------------------------------------------
with st.form("client_form"):
    st.subheader("Angaben zum Teilnehmer / Bewerber")
    
    domeniu = st.text_input("Hauptbereich / Hauptberufserfahrung (z. B. Logistik, Management, IT):", value=st.session_state.domeniu)
    vechime = st.text_input("Berufserfahrung / Berufshistorie:", value=st.session_state.vechime)
    educatie = st.text_input("Bildung, Qualifikationen und Zertifizierungen (z. B. IHK, Studium):", value=st.session_state.educatie)
    obiective = st.text_area("Berufliches Ziel oder gewünschte Richtung des Teilnehmers:", value=st.session_state.obiective)
    observatii = st.text_area("Weitere Beobachtungen (soziale Kompetenzen, Barrieren, Sprachniveau):", value=st.session_state.observatii)
    
    submitted = st.form_submit_button("Analyse generieren")

# Buton separat de resetare în afara formularului
if st.button("Formular & Bericht zurücksetzen"):
    st.session_state.domeniu = ""
    st.session_state.vechime = ""
    st.session_state.educatie = ""
    st.session_state.obiective = ""
    st.session_state.observatii = ""
    st.session_state.raport = ""
    st.rerun()

if submitted:
    # Salvăm valorile în session_state
    st.session_state.domeniu = domeniu
    st.session_state.vechime = vechime
    st.session_state.educatie = educatie
    st.session_state.obiective = obiective
    st.session_state.observatii = observatii

    if not domeniu or not obiective:
        st.warning("Bitte füllen Sie mindestens den Bereich und das berufliche Ziel aus.")
    elif not client:
        st.error("Groq Client ist nicht initialisiert (API-Key fehlt).")
    else:
        with st.spinner("Profil wird analysiert und Bericht wird generiert..."):
            
            system_prompt = """Sie sind ein KI-Experte für Job-Coaching und auf den deutschen Arbeitsmarkt ausgerichtet, spezialisiert auf die Erstellung von "Kompetenzanalysen" für Teilnehmer von Programmen zur beruflichen Integration. 
Generieren Sie einen strukturierten Bericht in deutscher Sprache (unter Verwendung relevanter deutscher Begriffe wie Fachkompetenz, Sozialkompetenz), der exakt diese Struktur einhält:
1. ZUSAMMENFASSUNG DES PROFILS (Kurze Synthese)
2. KOMPETENZANALYSE (Fachkompetenz, Methodenkompetenz, Sozialkompetenz, Personale Kompetenz)
3. STÄRKEN-SCHWÄCHTE-ANALYSE & LÜCKEN (Stärken, Defizite/Lücken im Vergleich zum Arbeitsmarkt)
4. ENTWICKLUNGS- UND HANDLUNGSEMPFEHLUNGEN (Handlungsempfehlungen für den Coach)"""

            user_input = f"""
            Bereich: {domeniu}
            Erfahrung: {vechime}
            Bildung: {educatie}
            Ziel: {obiective}
            Beobachtungen: {observatii}
            """

            try:
                response = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=0.3
                )
                
                st.session_state.raport = response.choices[0].message.content
                st.success("Die Analyse wurde erfolgreich generiert!")
                
            except Exception as e:
                st.error(f"Ein Fehler ist bei der Generierung aufgetreten: {e}")

# -------------------------------------------------------------------------
# Afișarea Raportului și Opțiuni de Print / Salvare (Export JSON)
# -------------------------------------------------------------------------
if st.session_state.raport:
    st.markdown("---")
    
    # Câmpuri pentru completare manuală (cu pixul după printare)
    st.markdown("""
    <div style="border: 2px dashed #888; padding: 15px; border-radius: 5px; margin-bottom: 20px; background-color: #f9f9f9;">
        <h4 style="margin-top:0; color: #333;">Teilnehmerangaben (zum manuellen Ausfüllen):</h4>
        <p><b>Name:</b> __________________________________________________</p>
        <p><b>Datum:</b> ____________________ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Kundennummer:</b> ____________________</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📄 Bericht der Kompetenzanalyse")
    st.markdown(st.session_state.raport)
    
    st.markdown("---")
    
    # Stil pentru printare
    st.markdown("""
    <style>
    @media print {
        body * {
            visibility: hidden;
        }
        #printable-area, #printable-area * {
            visibility: visible;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    col_print, col_save = st.columns(2)
    
    with col_print:
        if st.button("🖨️ Bericht Drucken"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
            
    with col_save:
        export_data = {
            "domeniu": st.session_state.domeniu,
            "vechime": st.session_state.vechime,
            "educatie": st.session_state.educatie,
            "obiective": st.session_state.obiective,
            "observatii": st.session_state.observatii,
            "raport": st.session_state.raport
        }
        json_str = json.dumps(export_data, ensure_ascii=False, indent=4)
        
        st.download_button(
            label="💾 Analyse speichern (zum Bearbeiten)",
            data=json_str,
            file_name="kompetenzanalyse_daten.json",
            mime="application/json"
        )
