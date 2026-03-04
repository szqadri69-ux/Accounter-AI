import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
from PyPDF2 import PdfReader

st.set_page_config(page_title="Accounter-AI | Pro", layout="wide")

if 'api_key' not in st.session_state:
    st.title("🔐 Secure Audit Login")
    api_key_input = st.text_input("Enter Gemini API Key:", type="password")
    if st.button("Initialize"):
        st.session_state['api_key'] = api_key_input
        st.rerun()
    st.stop()

# --- FORCING STABLE CONNECTION ---
try:
    # 'rest' transport v1beta error ko khatam kar deta hai
    genai.configure(api_key=st.session_state['api_key'], transport='rest')
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Setup Error: {e}")

st.title("🚀 Accounter-AI: Enterprise Auditor")

uploaded_file = st.file_uploader("Upload PDF Statement", type=['pdf'])

if uploaded_file:
    if st.button("📊 EXECUTE AUDIT", type="primary", use_container_width=True):
        with st.spinner("Processing..."):
            reader = PdfReader(uploaded_file)
            raw_text = "".join([p.extract_text() or "" for p in reader.pages])
            
            try:
                # Direct prompt for stable output
                response = model.generate_content(f"Extract transactions as CSV: {raw_text[:20000]}")
                if response and response.text:
                    st.success("Audit Complete!")
                    csv_clean = response.text.replace('```csv', '').replace('```', '').strip()
                    df = pd.read_csv(io.StringIO(csv_clean[csv_clean.find("Date"):]), on_bad_lines='skip')
                    st.dataframe(df, use_container_width=True)
                else:
                    st.error("No data returned from AI.")
            except Exception as e:
                st.error(f"System Error: {e}")
