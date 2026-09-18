import os
import streamlit as st
from groq import Groq

# Setările paginii web
st.set_page_config(page_title="Kompetenzanalyse", page_icon="📊", layout="centered")

st.title("📊 Kompetenzanalyse")
st.markdown("Instrument digital gratuit pentru analiza avansată a competențelor și generarea planului de acțiune profesională.")

# Accesarea cheii secrete pentru Groq
api_key = st.secrets.get("GROQ_API_KEY")

if not api_key:
    st.error("Eroare: Cheia API lipseste din setarile secrete ale aplicatiei (GROQ_API_KEY).")
else:
    client = Groq(api_key=api_key)

    # Formularul pentru introducerea datelor
    with st.form("client_form"):
        st.subheader("Datele Beneficiarului / Candidatului")
        
        domeniu = st.text_input("Domeniul de bază / Experiența principală (ex: Logistică, Management, IT):")
        vechime = st.text_input("Vechime în muncă / Istoric profesional:")
        educatie = st.text_input("Educație, calificări și certificări (ex: IHK, studii superioare):")
        obiective = st.text_area("Obiectivul profesional sau direcția dorită a clientului:")
        observatii = st.text_area("Alte observații (competențe sociale, bariere, nivel lingvistic):")
        
        submitted = st.form_submit_button("Generează Analiza")

    if submitted:
        if not domeniu or not obiective:
            st.warning("Te rog să completezi cel puțin domeniul și obiectivul profesional.")
        else:
            with st.spinner("Se analizează profilul și se generează raportul..."):
                
                system_prompt = """Ești un asistent AI expert în Job Coaching și orientat spre piața muncii din Germania, specializat în realizarea de "Kompetenzanalyse" (analize de competențe) pentru beneficiarii programelor de integrare profesională. 
                Generează un raport structurat în limba română (folosind și termeni germani relevanți, ex: Fachkompetenz, Sozialkompetenz), respectând exact această structură:
                1. ZUSAMMENFASSUNG DES PROFILS (Scurtă sinteză)
                2. KOMPETENZANALYSE (Fachkompetenz, Methodenkompetenz, Sozialkompetenz, Personale Kompetenz)
                3. STÄRKEN-SCHWÄCHTE-ANALYSE & LÜCKEN (Puncte forte, defizite/lücken față de piața muncii)
                4. ENTWICKLUNGS- UND HANDLUNGSEMPFEHLUNGEN (Recomandări de acțiune pentru Coach)"""

                user_input = f"""
                Domeniu: {domeniu}
                Vechime: {vechime}
                Educație: {educatie}
                Obiectiv: {obiective}
                Observații: {observatii}
                """

                try:
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_input}
                        ],
                        temperature=0.3
                    )
                    
                    raport = response.choices[0].message.content
                    
                    st.success("Analiza a fost generată cu succes!")
                    st.markdown("### 📄 Raportul de Kompetenzanalyse")
                    st.markdown(raport)
                    
                except Exception as e:
                    st.error(f"A apărut o eroare la generare: {e}")