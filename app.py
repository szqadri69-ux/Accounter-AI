import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
from PyPDF2 import PdfReader

st.set_page_config(page_title="Accounter-AI | Enterprise", layout="wide")

if 'api_key' not in st.session_state:
    st.title("🔐 Secure Audit Login")
    api_key_input = st.text_input("Enter New API Key:", type="password")
    if st.button("Initialize"):
        st.session_state['api_key'] = api_key_input
        st.rerun()
    st.stop()

# --- THE FIX ---
try:
    genai.configure(api_key=st.session_state['api_key'])
    # Force direct model access
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
                response = model.generate_content(f"Extract transactions as CSV: {raw_text[:20000]}")
                if response and response.text:
                    st.success("Audit Complete!")
                    st.dataframe(pd.read_csv(io.StringIO(response.text.replace('```csv', '').replace('```', '').strip())), use_container_width=True)
            except Exception as e:
                st.error(f"System Error: {e}")
