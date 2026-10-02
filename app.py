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

    # Funcție pentru curățarea caracterelor care generează pătrățele negre în PDF
    def clean_text(text):
        if not text:
            return ""
        for char in ['■', '–', '—', '•', '\u2010', '\u2011', '\u2012', '\u2013', '\u2014', '\u00a0']:
            text = text.replace(char, '-')
        return text

    # Funcție avansată pentru generarea PDF-ului cu încadrare strictă (540 pt)
    def create_pdf(text):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()
        
        normal_style = styles['Normal']
        normal_style.fontSize = 9
        normal_style.leading = 13

        table_text_style = ParagraphStyle(
            'TableText',
            parent=styles['Normal'],
            fontSize=8,
            leading=11
        )

        table_header_style = ParagraphStyle(
            'TableHeaderText',
            parent=table_text_style,
            textColor=colors.white,
            fontName='Helvetica-Bold'
        )

        story = []
        story.append(Paragraph("<b>Kompetenzanalyse Bericht</b>", styles['Heading1']))
        story.append(Spacer(1, 10))

        lines = text.split('\n')
        table_data = []
        in_table = False

        for line in lines:
            stripped = line.strip()
            # Preluăm corect liniile de tabel Markdown
            if stripped.startswith('|') and stripped.endswith('|'):
                if '---' in stripped:
                    continue
                cols = [c.strip() for c in stripped.split('|')[1:-1]]
                row_cells = [Paragraph(html.escape(clean_text(c)), table_text_style) for c in cols]
                table_data.append(row_cells)
                in_table = True
            else:
                if in_table and table_data:
                    num_cols = len(table_data[0])
                    # Setăm lățimi dinamice în funcție de numărul de coloane detectat (total 540 pt)
                    if num_cols == 4:
                        col_widths = [110, 140, 140, 150]
                    else:
                        col_widths = [110, 215, 215]

                    formatted_data = []
                    for r_idx, row in enumerate(table_data):
                        while len(row) < num_cols:
                            row.append(Paragraph("", table_text_style))
                        
                        new_row = []
                        for cell in row[:num_cols]:
                            if r_idx == 0:
                                new_row.append(Paragraph(cell.text, table_header_style))
                            else:
                                new_row.append(cell)
                        formatted_data.append(new_row)

                    t = Table(formatted_data, colWidths=col_widths)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('LEFTPADDING', (0, 0), (-1, -1), 4),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
                    ]))
                    story.append(t)
                    story.append(Spacer(1, 8))
                    table_data = []
                    in_table = False

                if stripped:
                    clean_line = clean_text(stripped)
                    safe_text = html.escape(clean_line)
                    safe_text = safe_text.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
                    story.append(Paragraph(safe_text, normal_style))
                    story.append(Spacer(1, 4))

        if in_table and table_data:
            num_cols = len(table_data[0])
            col_widths = [110, 140, 140, 150] if num_cols == 4 else [110, 215, 215]
            
            formatted_data = []
            for r_idx, row in enumerate(table_data):
                while len(row) < num_cols:
                    row.append(Paragraph("", table_text_style))
                new_row = []
                for cell in row[:num_cols]:
                    if r_idx == 0:
                        new_row.append(Paragraph(cell.text, table_header_style))
                    else:
                        new_row.append(cell)
                formatted_data.append(new_row)

            t = Table(formatted_data, colWidths=col_widths)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
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
                
                # Promptul tău original complet
                system_prompt = """Sie sind ein KI-Assistent und Experte für Job Coaching auf dem deutschen Arbeitsmarkt, spezialisiert auf die Erstellung von Kompetenzanalysen für Teilnehmer von Integrationsmaßnahmen.
                Generieren Sie einen detaillierten, strukturierten Bericht in deutscher Sprache mit exakt folgender Struktur (verwenden Sie für die Überschriften normale Groß- und Kleinschreibung, nicht nur Majuskeln):
                1. Zusammenfassung des Profils
                2. Kompetenzanalyse (Fachkompetenz, Methodenkompetenz, Sozialkompetenz, Personale Kompetenz)
                3. Stärken-Schwächen-Analyse & Lücken (Stärken, Defizite/Lücken im Bezug zum aktuellen Arbeitsmarkt)
                4. Entwicklungs- und Handlungsempfehlungen (Konkrete Handlungsempfehlungen für den Coach)"""
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
