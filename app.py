import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
from PyPDF2 import PdfReader

# --- 1. APP CONFIG ---
st.set_page_config(page_title="Accounter-AI | Professional", layout="wide")

if 'api_key' not in st.session_state:
    st.title("🔐 Secure Audit Login")
    api_key_input = st.text_input("Enter Gemini API Key:", type="password")
    if st.button("Initialize"):
        st.session_state['api_key'] = api_key_input
        st.rerun()
    st.stop()

# --- 2. FORCING STABLE VERSION ---
try:
    # Yahan hum version="v1" force kar rahe hain taaki 404 error na aaye
    genai.configure(api_key=st.session_state['api_key'], transport='rest')
    model = genai.GenerativeModel(model_name='gemini-1.5-flash') 
except Exception as e:
    st.error(f"Setup Error: {e}")

# --- 3. MAIN INTERFACE ---
st.title("🚀 Accounter-AI: Enterprise Auditor")

uploaded_file = st.file_uploader("Upload Bank Statement (PDF)", type=['pdf'])

if uploaded_file:
    if st.button("📊 EXECUTE AUDIT", type="primary", use_container_width=True):
        with st.spinner("Step 1: Extracting Data..."):
            reader = PdfReader(uploaded_file)
            raw_text = "".join([p.extract_text() or "" for p in reader.pages])
            
            if not raw_text.strip():
                st.error("Text not found in PDF.")
                st.stop()

        with st.spinner("Step 2: AI Analyzing..."):
            # Simple Prompt to avoid data loss
            prompt = f"Extract all bank transactions as a CSV table (Date, Description, Type, Amount) from this text: {raw_text[:20000]}"
            
            try:
                # API Call
                response = model.generate_content(prompt)
                
                if response and response.text:
                    st.success("Audit Complete!")
                    csv_raw = response.text.replace('```csv', '').replace('```', '').strip()
                    
                    if "Date" in csv_raw:
                        df = pd.read_csv(io.StringIO(csv_raw[csv_raw.find("Date"):]), on_bad_lines='skip')
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.warning("AI couldn't format CSV. Raw text shown below:")
                        st.text(response.text)
                else:
                    st.error("No response from AI. Please check your API key quota.")
                    
            except Exception as e:
                # Yahan humein asli wajah pata chalegi agar 404 aata hai
                st.error(f"System Error: {e}")
                st.info("Tip: If error persists, delete this app from Streamlit and deploy it as a 'New App'.")
