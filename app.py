import os
import streamlit as st
from groq import Groq
from io import BytesIO
import html
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import docx

# Setările paginii web
st.set_page_config(page_title="Kompetenzanalyse", page_icon="📊", layout="centered")

# Stiluri CSS personalizate pentru culorile butoanelor (Analiză = Verde, Zurücksetzen = Roșu)
st.markdown("""
    <style>
    /* Butonul principal (Analyse generieren) devine VERDE */
    div.stButton > button:first-child {
        background-color: #28a745 !important;
        color: white !important;
        border: none !important;
    }
    div.stButton > button:first-child:hover {
        background-color: #218838 !important;
        color: white !important;
    }
    /* Butonul de Reset (Zurücksetzen) devine ROȘU */
    div.row-widget.stButton > button:nth-child(2), 
    button[kind="secondary"] {
        background-color: #dc3545 !important;
        color: white !important;
        border: none !important;
    }
    button[kind="secondary"]:hover {
        background-color: #c82333 !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Kompetenzanalyse & Profiling")
st.markdown("Professionelles digitales Instrument zur Kompetenzanalyse, Dokumenten-Auswertung und Erstellung des Handlungsplans.")

# Accesarea cheii secrete pentru Groq
api_key = st.secrets.get("GROQ_API_KEY")

if not api_key:
    st.error("Fehler: Der API-Schlüssel fehlt in den Geheimhaltseinstellungen (Secrets) der App (GROQ_API_KEY).")
else:
    client = Groq(api_key=api_key)

    # Inițializarea stării
    if "form_submitted" not in st.session_state:
        st.session_state.form_submitted = False
    if "raport_text" not in st.session_state:
        st.session_state.raport_text = ""

    # Funcție sigură pentru generarea PDF-ului (evită caracterele dubioase/pătrățelele)
    def create_pdf(text):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()
        normal_style = styles['Normal']
        normal_style.fontSize = 10
        normal_style.leading = 14

        story = []
        story.append(Paragraph("<b>Kompetenzanalyse Bericht</b>", styles['Heading1']))
        story.append(Spacer(1, 12))

        for paragraph in text.split('\n'):
            if paragraph.strip():
                # Înlocuim caracterele problematice care generează erori de codare în PDF
                clean_p = paragraph.replace('■', '-').replace('–', '-')
                safe_text = html.escape(clean_p)
                safe_text = safe_text.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
                story.append(Paragraph(safe_text, normal_style))
                story.append(Spacer(1, 6))

        doc.build(story)
        buffer.seek(0)
        return buffer

    # Funcție pentru generarea documentului Word (.docx) curat cu structură pe tabele/paragrafe
    def create_word(text):
        doc = docx.Document()
        doc.add_heading("Kompetenzanalyse Bericht", level=1)
        
        for paragraph in text.split('\n'):
            if paragraph.strip():
                clean_p = paragraph.replace('■', '-')
                if any(clean_p.strip().startswith(prefix) for prefix in ["1.", "2.", "3.", "4.", "5."]):
                    doc.add_heading(clean_p.strip(), level=2)
                else:
                    doc.add_paragraph(clean_p.strip())
                    
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer

    # Secțiunea de Upload Documente
    st.subheader("📁 Dokumenten-Upload (Optional)")
    uploaded_files = st.file_uploader(
        "Laden Sie hier Lebensläufe, Zeugnisse, Zertifikate oder Empfehlungsschreiben hoch (PDF, Word, Bilder):",
        type=["pdf", "docx", "doc", "txt", "png", "jpg"],
        accept_multiple_files=True
    )
    
    uploaded_file_names = ""
    if uploaded_files:
        file_names_list = [file.name for file in uploaded_files]
        uploaded_file_names = ", ".join(file_names_list)
        st.success(f"Erfolgreich hochgeladene Dokumente: {uploaded_file_names}")

    st.divider()

    # Formularul de date (Fără st.form strict, editare fluidă la Enter)
    st.subheader("Daten des Teilnehmers / Bewerbers")
    
    domeniu = st.text_input("Grundbereich / Hauptberufserfahrung (z. B. Logistik, Management, IT):", value="")
    vechime = st.text_area("Berufserfahrung / Werdegang (detaillierte Stationen):", value="", height=100)
    educatie = st.text_input("Ausbildung, Qualifikationen & Zertifikate (z. B. IHK, Studium):", value="")
    obiective = st.text_area("Ziele (Berufliches Ziel / gewünschte Richtung, falls benötigt):", value="", height=80)
    observatii = st.text_area("Weitere Beobachtungen (Sozialkompetenzen, Barrieren, Sprachniveau):", value="", height=80)
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        submitted = st.button("Analyse generieren")
    with col_btn2:
        reset_btn = st.button("Zurücksetzen")

    if reset_btn:
        st.session_state.form_submitted = False
        st.session_state.raport_text = ""
        st.rerun()

    if submitted:
        if not domeniu:
            st.warning("Bitte füllen Sie mindestens den Grundbereich aus.")
        else:
            with st.spinner("Das Profil wird analysiert und der Bericht wird erstellt..."):
                
                system_prompt = """Sie sind ein KI-Assistent und Experte für Job Coaching auf dem deutschen Arbeitsmarkt, spezialisiert auf die Erstellung von Kompetenzanalysen für Teilnehmer von Integrations- und Qualifizierungsmaßnahmen.
                Generieren Sie einen strukturierten Bericht in deutscher Sprache mit exakt folgender Struktur (Vermeiden Sie Wiederholungen):
                1. ZUSAMMENFASSUNG DES PROFILS
                2. KOMPETENZANALYSE (Fachkompetenz, Methodenkompetenz, Sozialkompetenz, Personale Kompetenz)
                3. STÄRKEN-SCHWÄCHTE-ANALYSE & LÜCKEN (Bezug zum Arbeitsmarkt)
                4. ENTWICKLUNGS- UND HANDLUNGSEMPFEHLUNGEN für den Coach"""

                user_input = f"""
                Bereich: {domeniu}
                Berufserfahrung: {vechime}
                Ausbildung: {educatie}
                Hochgeladene Dokumente / Nachweise: {uploaded_file_names}
                Ziele: {obiective}
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
                    
                    st.session_state.raport_text = response.choices[0].message.content
                    st.session_state.form_submitted = True
                    
                except Exception as e:
                    st.error(f"Fehler bei der Generierung: {e}")

    # Afișarea rezultatului și a butoanelor de export
    if st.session_state.form_submitted and st.session_state.raport_text:
        st.success("Die Analyse wurde erfolgreich erstellt!")
        st.markdown("### 📄 Kompetenzanalyse Bericht")
        st.markdown(st.session_state.raport_text)
        
        st.divider()
        st.subheader("Export & Optionen")
        
        col_pdf, col_word = st.columns(2)
        
        with col_pdf:
            pdf_buffer = create_pdf(st.session_state.raport_text)
            st.download_button(
                label="📥 Als PDF herunterladen",
                data=pdf_buffer,
                file_name="Kompetenzanalyse_Bericht.pdf",
                mime="application/pdf"
            )
            
        with col_word:
            word_buffer = create_word(st.session_state.raport_text)
            st.download_button(
                label="📥 Als Word (.docx) herunterladen",
                data=word_buffer,
                file_name="Kompetenzanalyse_Bericht.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
