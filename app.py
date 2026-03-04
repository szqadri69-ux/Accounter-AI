import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
from PyPDF2 import PdfReader
from fpdf import FPDF

# --- 1. GLOBAL SETTINGS ---
st.set_page_config(page_title="Accounter-AI | Professional Auditor", layout="wide")

if 'api_key' not in st.session_state:
    st.title("🔐 Secure Audit Login")
    api_key_input = st.text_input("Enter Gemini API Key:", type="password")
    if st.button("Initialize System"):
        st.session_state['api_key'] = api_key_input
        st.rerun()
    st.stop()

# --- 2. THE LEGACY FIX (Works on v1beta) ---
try:
    genai.configure(api_key=st.session_state['api_key'])
    # 'gemini-pro' is the universal legacy name for high-density auditing
    model = genai.GenerativeModel('gemini-pro') 
except Exception as e:
    st.error(f"Configuration Error: {e}")

# --- 3. CORE LOGIC ---
def get_pdf_text_structured(uploaded_file):
    reader = PdfReader(uploaded_file)
    structured_text = ""
    for i, page in enumerate(reader.pages):
        content = page.extract_text()
        if content:
            structured_text += f"\n--- [PAGE {i+1}] ---\n" + content
    return structured_text

# --- 4. PROFESSIONAL INTERFACE ---
st.title("🚀 Accounter-AI: Enterprise Auditor")
st.info("System Status: Online | Mode: Legacy Compatibility (v1beta-Safe)")

uploaded_file = st.file_uploader("Upload Bank Statement (PDF)", type=['pdf'])

if uploaded_file:
    if st.button("📊 EXECUTE AUDIT", type="primary", use_container_width=True):
        with st.spinner("Step 1: Extracting Ledger Data..."):
            raw_text = get_pdf_text_structured(uploaded_file)
            
            if not raw_text.strip():
                st.error("Error: Could not extract text. Please ensure the file is not a flat image.")
                st.stop()

        with st.spinner("Step 2: AI Analyzing Transactions..."):
            prompt = f"""
            ACT AS A SENIOR AUDITOR. 
            Extract all transactions from the following text. 
            Return ONLY a CSV table with headers: Date, Description, Category, Type, Amount.
            Categories: FOOD, TRAVEL, LOAN, MEDICINE, SALARY, or GENERAL.
            Type: Debit or Credit.
            
            DATA:
            {raw_text[:20000]}
            """
            
            try:
                response = model.generate_content(prompt)
                
                if response and response.text:
                    csv_raw = response.text
                    # Cleaning potential markdown
                    csv_raw = csv_raw.replace('```csv', '').replace('```', '').strip()
                    
                    if "Date" in csv_raw:
                        csv_body = csv_raw[csv_raw.find("Date"):]
                        df = pd.read_csv(io.StringIO(csv_body), on_bad_lines='skip')
                        
                        # Data Sanitization
                        df['Amount'] = pd.to_numeric(df['Amount'].astype(str).str.replace('[^0-9.]', '', regex=True), errors='coerce').fillna(0)
                        df = df[df['Amount'] > 0]
                        df.insert(0, 'Sr. No.', range(1, 1 + len(df)))

                        # Analytics
                        dr_total = df[df['Type'].str.contains('Debit', case=False, na=False)]['Amount'].sum()
                        cr_total = df[df['Type'].str.contains('Credit', case=False, na=False)]['Amount'].sum()

                        st.success(f"Audit Successful: {len(df)} Records Captured.")
                        
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Total Expenses", f"₹{dr_total:,.2f}")
                        m2.metric("Total Income", f"₹{cr_total:,.2f}")
                        m3.metric("Net Surplus", f"₹{cr_total - dr_total:,.2f}")

                        st.divider()
                        
                        # Export Logic
                        ex_col, pdf_col = st.columns(2)
                        with ex_col:
                            excel_io = io.BytesIO()
                            df.to_excel(excel_io, index=False)
                            st.download_button("📥 Export Excel Ledger", data=excel_io.getvalue(), file_name="Audit.xlsx", use_container_width=True)
                        with pdf_col:
                            pdf_doc = FPDF()
                            pdf_doc.add_page()
                            pdf_doc.set_font("Arial", size=12)
                            pdf_doc.cell(200, 10, txt=f"Total Records: {len(df)}", ln=True)
                            pdf_data = pdf_doc.output(dest='S').encode('latin-1')
                            st.download_button("📥 Export PDF Summary", data=pdf_data, file_name="Summary.pdf", use_container_width=True)

                        st.dataframe(df, use_container_width=True)
                    else:
                        st.error("AI Error: Formatting failed. Please ensure the PDF text is clear.")
                else:
                    st.error("Model Error: Empty response. Check your API key limits.")
            except Exception as e:
                st.error(f"Critical System Failure: {e}")
