import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
from PyPDF2 import PdfReader
from fpdf import FPDF

# --- 1. SETTINGS ---
st.set_page_config(page_title="Accounter-AI | Enterprise", layout="wide")

if 'api_key' not in st.session_state:
    st.title("🔐 Secure Audit Login")
    api_key_input = st.text_input("Enter Gemini API Key:", type="password")
    if st.button("Initialize"):
        st.session_state['api_key'] = api_key_input
        st.rerun()
    st.stop()

# --- 2. THE FIX: VERSION-AGNOSTIC INITIALIZATION ---
try:
    genai.configure(api_key=st.session_state['api_key'])
    # 'gemini-1.5-pro' is the most compatible name across different API versions
    model = genai.GenerativeModel('gemini-1.5-pro') 
except Exception as e:
    st.error(f"Setup Error: {e}")

# --- 3. EXTRACTION ---
def get_pdf_text_structured(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for i, page in enumerate(reader.pages):
        content = page.extract_text()
        if content:
            # Adding markers to keep rows organized
            text += f"\n[P{i+1}]\n" + content
    return text

# --- 4. UI ---
st.title("🚀 Accounter-AI: Enterprise Auditor")
st.info("System: Professional Mode | Model: Gemini 1.5 Pro | Extraction: Row-by-Row")

uploaded_file = st.file_uploader("Upload PDF Statement", type=['pdf'])

if uploaded_file:
    if st.button("📊 EXECUTE AUDIT", type="primary", use_container_width=True):
        with st.spinner("Step 1: Extracting Ledger Text..."):
            raw_text = get_pdf_text_structured(uploaded_file)
            
            if not raw_text.strip():
                st.error("Text Error: Could not read the file. Please ensure it's a digital PDF, not a photo.")
                st.stop()

        with st.spinner("Step 2: AI Analyzing Transactions..."):
            # Refined prompt for 12,000+ transaction handling
            prompt = f"""
            ACT AS A SENIOR AUDITOR. Extract all bank transactions from this text. 
            Return ONLY a CSV table with headers: Date, Description, Category, Type, Amount.
            Categories: FOOD, TRAVEL, LOAN, MEDICINE, SALARY, or GENERAL.
            Type: Debit or Credit.
            
            TEXT DATA:
            {raw_text[:28000]}
            """
            
            try:
                response = model.generate_content(prompt)
                
                if response and response.text:
                    csv_data = response.text
                    # Cleaning markdown and extra text
                    csv_data = csv_data.replace('```csv', '').replace('```', '').strip()
                    
                    if "Date" in csv_data:
                        # Find exactly where CSV starts
                        csv_body = csv_data[csv_data.find("Date"):]
                        df = pd.read_csv(io.StringIO(csv_body), on_bad_lines='skip')
                        
                        # Professional Data Cleaning
                        df['Amount'] = pd.to_numeric(df['Amount'].astype(str).str.replace('[^0-9.]', '', regex=True), errors='coerce').fillna(0)
                        df = df[df['Amount'] > 0]
                        df.insert(0, 'Sr. No.', range(1, 1 + len(df)))

                        # Financial Calculations
                        dr_total = df[df['Type'].str.contains('Debit', case=False, na=False)]['Amount'].sum()
                        cr_total = df[df['Type'].str.contains('Credit', case=False, na=False)]['Amount'].sum()

                        st.success(f"Audit Complete: {len(df)} Records found.")
                        
                        # Metrics Dashboard
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Total Debit", f"₹{dr_total:,.2f}")
                        c2.metric("Total Credit", f"₹{cr_total:,.2f}")
                        c3.metric("Net Savings", f"₹{cr_total - dr_total:,.2f}")

                        # Pro Exports
                        st.divider()
                        d1, d2 = st.columns(2)
                        with d1:
                            excel_buf = io.BytesIO()
                            df.to_excel(excel_buf, index=False)
                            st.download_button("📥 Export Excel Ledger", data=excel_buf.getvalue(), file_name="Audit.xlsx", use_container_width=True)
                        with d2:
                            pdf = FPDF()
                            pdf.add_page()
                            pdf.set_font("Arial", size=12)
                            pdf.cell(200, 10, txt=f"Audit Summary - Net: {cr_total - dr_total}", ln=True)
                            pdf_data = pdf.output(dest='S').encode('latin-1')
                            st.download_button("📥 Export PDF Summary", data=pdf_data, file_name="Summary.pdf", use_container_width=True)

                        st.dataframe(df, use_container_width=True)
                    else:
                        st.error("Format Error: AI returned text instead of a table. Please retry.")
                else:
                    st.error("Connection Error: Model returned an empty response.")
            except Exception as e:
                st.error(f"Critical Model Failure: {e}")
                st.warning("Action Required: Please go to Google AI Studio and check if 'Gemini 1.5 Pro' is enabled for your API Key.")
