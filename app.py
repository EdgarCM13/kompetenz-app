import os
import streamlit as st
from groq import Groq
from io import BytesIO
import html
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Setările paginii web
st.set_page_config(page_title="Kompetenzanalyse", page_icon="📊", layout="centered")

st.title("📊 Kompetenzanalyse")
st.markdown("Kostenloses digitales Instrument zur professionellen Kompetenzanalyse und Erstellung des Handlungsplans.")

# Accesarea cheii secrete pentru Groq
api_key = st.secrets.get("GROQ_API_KEY")

if not api_key:
    st.error("Fehler: Der API-Schlüssel fehlt in den Geheimhaltseinstellungen (Secrets) der App (GROQ_API_KEY).")
else:
    client = Groq(api_key=api_key)

    # Inițializarea stării pentru resetare curată a formularului
    if "form_submitted" not in st.session_state:
        st.session_state.form_submitted = False
    if "raport_text" not in st.session_state:
        st.session_state.raport_text = ""

    # Funcție sigură pentru generarea PDF-ului (curăță caracterele dubioase și liniile de tabel)
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
                # Eliminăm caracterele problematice și liniile de tabel Markdown care strică aspectul PDF-ului
                clean_line = paragraph.replace('■', '-').replace('–', '-')
                if clean_line.strip().startswith('|') and clean_line.strip().endswith('|'):
                    # Transformăm liniile de tabel într-un format text mai prietenos pentru PDF
                    clean_line = clean_line.replace('|', ' | ')
                
                safe_text = html.escape(clean_line)
                safe_text = safe_text.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
                
                story.append(Paragraph(safe_text, normal_style))
                story.append(Spacer(1, 6))

        doc.build(story)
        buffer.seek(0)
        return buffer

    # Secțiunea de Upload Documente (opțional, integrată curat)
    st.subheader("📁 Dokumenten-Upload (Optional)")
    uploaded_files = st.file_uploader(
        "Laden Sie hier Lebensläufe, Zeugnisse, Zertifikate oder Empfehlungsschreiben hoch:",
        type=["pdf", "docx", "doc", "txt", "png", "jpg"],
        accept_multiple_files=True
    )
    
    uploaded_file_names = ""
    if uploaded_files:
        file_names_list = [file.name for file in uploaded_files]
        uploaded_file_names = ", ".join(file_names_list)
        st.success(f"Erfolgreich hochgeladene Dokumente: {uploaded_file_names}")

    st.divider()

    # Formularul pentru introducerea datelor
    with st.form("client_form"):
        st.subheader("Daten des Teilnehmers / Bewerbers")
        
        domeniu = st.text_input("Grundbereich / Hauptberufserfahrung (z. B. Logistik, Management, IT):")
        vechime = st.text_input("Berufserfahrung / Werdegang:")
        educatie = st.text_input("Ausbildung, Qualifikationen & Zertifikate (z. B. IHK, Studium):")
        obiective = st.text_area("Berufliches Ziel oder gewünschte Richtung des Teilnehmers:")
        observatii = st.text_area("Weitere Beobachtungen (Sozialkompetenzen, Barrieren, Sprachniveau):")
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Analyse generieren")
        with col2:
            reset_btn = st.form_submit_button("Zurücksetzen")

    if reset_btn:
        st.session_state.form_submitted = False
        st.session_state.raport_text = ""
        st.rerun()

    if submitted:
        if not domeniu or not obiective:
            st.warning("Bitte füllen Sie mindestens den Grundbereich und das berufliche Ziel aus.")
        else:
            with st.spinner("Das Profil wird analysiert und der Bericht wird erstellt..."):
                
                system_prompt = """Sie sind ein KI-Assistent und Experte für Job Coaching auf dem deutschen Arbeitsmarkt, spezialisiert auf die Erstellung von Kompetenzanalysen für Teilnehmer von Integrations- und Qualifizierungsmaßnahmen.
                Generieren Sie einen strukturierten Bericht in deutscher Sprache mit exakt folgender Struktur, ohne komplexe Markdown-Tabellen (verwenden Sie stattdessen übersichtliche Aufzählungen oder Fließtext, damit es in Dokumenten sauber lesbar ist):
                1. ZUSAMMENFASSUNG DES PROFILS
                2. KOMPETENZANALYSE (Fachkompetenz, Methodenkompetenz, Sozialkompetenz, Personale Kompetenz)
                3. STÄRKEN-SCHWÄCHTE-ANALYSE & LÜCKEN (Bezug zum Arbeitsmarkt)
                4. ENTWICKLUNGS- UND HANDLUNGSEMPFEHLUNGEN für den Coach"""

                user_input = f"""
                Bereich: {domeniu}
                Berufserfahrung: {vechime}
                Ausbildung: {educatie}
                Hochgeladene Dokumente: {uploaded_file_names}
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
        
        col_pdf, col_word, col_reset = st.columns(3)
        
        with col_pdf:
            pdf_buffer = create_pdf(st.session_state.raport_text)
            st.download_button(
                label="📥 Als PDF herunterladen",
                data=pdf_buffer,
                file_name="Kompetenzanalyse_Bericht.pdf",
                mime="application/pdf"
            )
            
        with col_word:
            st.download_button(
                label="📥 Als Word (.doc) speichern",
                data=st.session_state.raport_text,
                file_name="Kompetenzanalyse_Bericht.doc",
                mime="text/plain"
            )
            
        with col_reset:
            if st.button("🔄 Neue Analyse / Reset"):
                st.session_state.form_submitted = False
                st.session_state.raport_text = ""
                st.rerun()
