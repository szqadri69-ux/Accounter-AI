import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
from PyPDF2 import PdfReader

# --- 1. SETTINGS ---
st.set_page_config(page_title="Accounter-AI | Professional", layout="wide")

if 'api_key' not in st.session_state:
    st.title("🔐 Secure Audit Login")
    api_key_input = st.text_input("Enter New API Key (From New Project):", type="password")
    if st.button("Initialize"):
        st.session_state['api_key'] = api_key_input
        st.rerun()
    st.stop()

# --- 2. THE STABLE FIX ---
try:
    genai.configure(api_key=st.session_state['api_key'])
    # Updated to the latest stable model string
    model = genai.GenerativeModel('gemini-1.5-flash-latest') 
except Exception as e:
    st.error(f"Setup Error: {e}")

# --- 3. UI ---
st.title("🚀 Accounter-AI: Enterprise Auditor")
st.info("Status: Connected | Mode: Stable V1")

uploaded_file = st.file_uploader("Upload PDF Statement", type=['pdf'])

if uploaded_file:
    if st.button("📊 EXECUTE AUDIT", type="primary", use_container_width=True):
        with st.spinner("Step 1: Extracting Text..."):
            reader = PdfReader(uploaded_file)
            raw_text = ""
            for page in reader.pages:
                raw_text += (page.extract_text() or "")
            
            if not raw_text.strip():
                st.error("Could not read text from PDF.")
                st.stop()

        with st.spinner("Step 2: AI Auditing..."):
            prompt = f"Return ONLY CSV format with headers (Date, Description, Type, Amount) for transactions in this text: {raw_text[:25000]}"
            
            try:
                response = model.generate_content(prompt)
                
                if response and response.text:
                    st.success("Audit Successful!")
                    # Cleaning markdown
                    csv_data = response.text.replace('```csv', '').replace('```', '').strip()
                    
                    if "Date" in csv_data:
                        # Logic to find the table start
                        csv_body = csv_data[csv_data.find("Date"):]
                        df = pd.read_csv(io.StringIO(csv_body), on_bad_lines='skip')
                        
                        # Data Cleaning
                        df['Amount'] = pd.to_numeric(df['Amount'].astype(str).str.replace('[^0-9.]', '', regex=True), errors='coerce').fillna(0)
                        df = df[df['Amount'] > 0]
                        df.insert(0, 'Sr. No.', range(1, 1 + len(df)))

                        st.dataframe(df, use_container_width=True)
                        
                        # --- FIXED DOWNLOAD BUTTON ---
                        buf = io.BytesIO()
                        df.to_excel(buf, index=False)
                        st.download_button(
                            label="📥 Download Excel Ledger",
                            data=buf.getvalue(),
                            file_name="Audit_Report.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.error("AI could not format the table. Check raw response below.")
                        st.text(response.text)
                else:
                    st.error("AI returned an empty response.")
            except Exception as e:
                st.error(f"Model Failure: {e}")
