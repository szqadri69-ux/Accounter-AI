import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
from PyPDF2 import PdfReader
from fpdf import FPDF

# --- 1. GLOBAL SETTINGS ---
st.set_page_config(page_title="Accounter-AI | Enterprise Auditor", layout="wide")

if 'api_key' not in st.session_state:
    st.title("🔐 Secure Audit Login")
    api_key_input = st.text_input("Enter Gemini API Key:", type="password")
    if st.button("Initialize System"):
        st.session_state['api_key'] = api_key_input
        st.rerun()
    st.stop()

# --- 2. FIXED MODEL INITIALIZATION (Explicit Versioning) ---
try:
    # We use the most direct configuration to avoid the v1beta 404 error
    genai.configure(api_key=st.session_state['api_key'])
    
    # FIXED: Using the full model path which is recognized by all API versions
    model = genai.GenerativeModel(model_name='models/gemini-1.5-flash-latest')
except Exception as e:
    st.error(f"Configuration Error: {e}")

# --- 3. CORE LOGIC ---
def get_pdf_text_structured(uploaded_file):
    reader = PdfReader(uploaded_file)
    structured_text = ""
    for i, page in enumerate(reader.pages):
        # Adding Page markers to prevent data mixing
        structured_text += f"\n[PAGE {i+1}] " + (page.extract_text() or "")
    return structured_text

# --- 4. PROFESSIONAL INTERFACE ---
st.title("🚀 Accounter-AI: Enterprise Auditor")
st.info("System Status: Online | Model: Gemini-1.5-Flash (Stable) | Mode: Row-by-Row")

uploaded_file = st.file_uploader("Upload Financial Statement (PDF)", type=['pdf'])

if uploaded_file:
    if st.button("📊 EXECUTE AUDIT", type="primary", use_container_width=True):
        with st.spinner("Processing PDF Text..."):
            raw_text = get_pdf_text_structured(uploaded_file)
            
            if len(raw_text.strip()) < 20:
                st.error("Error: Could not extract text. PDF might be a flat image scan.")
                st.stop()

        with st.spinner("AI Analyzing Ledger..."):
            prompt = f"""
            Extract all transactions. Return ONLY CSV with headers: Date, Description, Category, Type, Amount.
            Ensure 'Type' is Credit or Debit. Ensure 'Amount' is numeric.
            DATA:
            {raw_text[:30000]}
            """
            
            try:
                # Direct call to the model
                response = model.generate_content(prompt)
                
                if response and response.text:
                    csv_raw = response.text
                    # Clean up markdown if AI includes it
                    csv_raw = csv_raw.replace('```csv', '').replace('```', '').strip()
                    
                    start_key = "Date,"
                    if start_key in csv_raw:
                        clean_csv = csv_raw[csv_raw.find(start_key):]
                        df = pd.read_csv(io.StringIO(clean_csv), on_bad_lines='skip')
                        
                        # Data Cleaning
                        df['Amount'] = pd.to_numeric(df['Amount'].astype(str).str.replace('[^0-9.]', '', regex=True), errors='coerce').fillna(0)
                        df = df[df['Amount'] > 0]
                        df.insert(0, 'Sr. No.', range(1, 1 + len(df)))

                        # Dashboard
                        total_dr = df[df['Type'].str.contains('Debit', case=False, na=False)]['Amount'].sum()
                        total_cr = df[df['Type'].str.contains('Credit', case=False, na=False)]['Amount'].sum()

                        st.success(f"Audit Successful: {len(df)} Records Captured.")
                        
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Total Expenses", f"₹{total_dr:,.2f}")
                        c2.metric("Total Income", f"₹{total_cr:,.2f}")
                        c3.metric("Net Balance", f"₹{total_cr - total_dr:,.2f}")

                        # Downloads
                        col_ex, col_pdf = st.columns(2)
                        with col_ex:
                            buf = io.BytesIO()
                            df.to_excel(buf, index=False)
                            st.download_button("📥 Download Excel Ledger", data=buf.getvalue(), file_name="Audit.xlsx", use_container_width=True)
                        with col_pdf:
                            pdf = FPDF()
                            pdf.add_page()
                            pdf.set_font("Arial", size=12)
                            pdf.cell(200, 10, txt=f"Total Transactions: {len(df)}", ln=True)
                            pdf_out = pdf.output(dest='S').encode('latin-1')
                            st.download_button("📥 Download PDF Summary", data=pdf_out, file_name="Summary.pdf", use_container_width=True)

                        st.dataframe(df, use_container_width=True)
                    else:
                        st.error("AI Error: Formatting issue. Try a clearer PDF.")
                else:
                    st.error("AI Error: Empty response. Check your API quota.")
            except Exception as e:
                st.error(f"Model Request Failed: {e}")
