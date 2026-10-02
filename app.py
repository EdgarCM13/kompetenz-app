import os
import streamlit as st
from groq import Groq
from io import BytesIO
import html
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

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

    # Funcție avansată pentru generarea PDF-ului care transformă tabelele Markdown în tabele grafice reale
    def create_pdf(text):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        styles = getSampleStyleSheet()
        
        normal_style = styles['Normal']
        normal_style.fontSize = 9
        normal_style.leading = 12

        table_style = ParagraphStyle(
            'TableText',
            parent=styles['Normal'],
            fontSize=8,
            leading=11
        )

        story = []
        story.append(Paragraph("<b>Kompetenzanalyse Bericht</b>", styles['Heading1']))
        story.append(Spacer(1, 10))

        lines = text.split('\n')
        table_data = []
        in_table = False

        for line in lines:
            stripped = line.strip()
            # Verificăm dacă linia face parte dintr-un tabel Markdown (conține |)
            if stripped.startswith('|') and stripped.endswith('|'):
                # Ignorăm rândurile de separație de tip |---|---|
                if '---' in stripped:
                    continue
                
                cols = [c.strip() for c in stripped.split('|')[1:-1]]
                # Creăm paragrafe pentru fiecare celulă pentru a permite wrap-text corect
                row_cells = [Paragraph(html.escape(c.replace('■', '-')), table_style) for c in cols]
                table_data.append(row_cells)
                in_table = True
            else:
                # Dacă tocmai am ieșit dici dintr-un tabel, îl adăugăm în document
                if in_table and table_data:
                    t = Table(table_data, colWidths=[130, 185, 185])
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
                    ]))
                    # Schimbăm culoarea textului din header în alb pentru vizibilitate
                    for i in range(len(table_data[0])):
                        table_data[0][i] = Paragraph(f"<b>{table_data[0][i].text}</b>", ParagraphStyle('H', parent=table_style, textColor=colors.white))
                    
                    story.append(t)
                    story.append(Spacer(1, 10))
                    table_data = []
                    in_table = False

                if stripped:
                    clean_line = stripped.replace('■', '-').replace('–', '-')
                    safe_text = html.escape(clean_line)
                    safe_text = safe_text.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
                    story.append(Paragraph(safe_text, normal_style))
                    story.append(Spacer(1, 4))

        # Dacă textul se termină cu un tabel
        if in_table and table_data:
            t = Table(table_data, colWidths=[130, 185, 185])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            story.append(t)

        doc.build(story)
        buffer.seek(0)
        return buffer

    # Secțiunea de Upload Documente (opțional)
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
                Generieren Sie einen strukturierten Bericht in deutscher Sprache mit exakt folgender Struktur und nutzen Sie saubere Markdown-Tabellen für die Kompetenzanalyse und Stärken-Schwächen-Analyse:
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
