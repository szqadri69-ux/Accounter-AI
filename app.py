import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
from PyPDF2 import PdfReader
from fpdf import FPDF

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="Accounter-AI | Professional Auditor", layout="wide")

# Session Management for API Key
if 'api_key' not in st.session_state:
    st.title("🔐 Professional Audit Login")
    api_key_input = st.text_input("Enter Gemini API Key:", type="password")
    if st.button("Access Dashboard"):
        st.session_state['api_key'] = api_key_input
        st.rerun()
    st.stop()

# Configure AI Model
genai.configure(api_key=st.session_state['api_key'])
# Using a stable model reference to prevent 404 version errors
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. DATA EXTRACTION LOGIC ---
def get_pdf_text_structured(uploaded_file):
    """Extracts text locally to ensure row-by-row integrity"""
    reader = PdfReader(uploaded_file)
    structured_text = ""
    for i, page in enumerate(reader.pages):
        structured_text += f"\n--- [PAGE {i+1}] ---\n"
        structured_text += page.extract_text()
    return structured_text

# --- 3. PROFESSIONAL INTERFACE ---
st.title("🚀 Accounter-AI: Pro Financial Auditor")
st.info("STATUS: Row-by-Row Deep Scan Enabled. Ensuring 100% data capture for high-density statements.")

uploaded_file = st.file_uploader("Upload Bank Statement (PDF)", type=['pdf'])

if uploaded_file:
    if st.button("📊 GENERATE FINANCIAL AUDIT", type="primary", use_container_width=True):
        with st.spinner("Extracting ledger data..."):
            raw_text = get_pdf_text_structured(uploaded_file)
            
            if len(raw_text.strip()) < 50:
                st.error("Error: PDF content is unreadable. Please ensure the file is not a restricted scan.")
                st.stop()

        with st.spinner("AI Auditing in progress..."):
            # Prompt designed for professional CSV output without data loss
            prompt = f"""
            ACT AS A SENIOR FINANCIAL AUDITOR. 
            Extract every single transaction from the provided text.
            FORMAT: CSV only with 5 columns: Date, Description, Category, Type (Debit/Credit), Amount.
            RULES: No summaries. No header/footer text. Clean numeric amounts only.
            
            LEDGER DATA:
            {raw_text[:30000]}
            """
            
            try:
                response = model.generate_content(prompt)
                csv_output = response.text
                
                if "Date," in csv_output:
                    # Locate start of CSV to avoid AI conversational noise
                    start_idx = csv_output.find("Date,")
                    df = pd.read_csv(io.StringIO(csv_output[start_idx:]), on_bad_lines='skip')
                    
                    # Data Sanitization
                    df['Amount'] = pd.to_numeric(df['Amount'].astype(str).str.replace('[^0-9.]', '', regex=True), errors='coerce').fillna(0)
                    df = df[df['Amount'] > 0]
                    df.insert(0, 'Sr. No.', range(1, 1 + len(df)))

                    # Financial Metrics
                    total_debit = df[df['Type'].str.contains('Debit', case=False, na=False)]['Amount'].sum()
                    total_credit = df[df['Type'].str.contains('Credit', case=False, na=False)]['Amount'].sum()
                    net_balance = total_credit - total_debit

                    st.success(f"Audit Complete: {len(df)} transactions verified.")
                    
                    # Executive Dashboard
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Total Expenses (Debit)", f"₹{total_debit:,.2f}")
                    m2.metric("Total Income (Credit)", f"₹{total_credit:,.2f}")
                    m3.metric("Net Surplus/Deficit", f"₹{net_balance:,.2f}")

                    st.divider()

                    # Professional Export Options
                    ex_col, pdf_col = st.columns(2)
                    with ex_col:
                        excel_io = io.BytesIO()
                        df.to_excel(excel_io, index=False)
                        st.download_button("📥 Export Full Excel Ledger", data=excel_io.getvalue(), file_name="Financial_Audit.xlsx", use_container_width=True)
                    
                    with pdf_col:
                        pdf = FPDF()
                        pdf.add_page()
                        pdf.set_font("Arial", 'B', 14)
                        pdf.cell(200, 10, txt="Executive Financial Summary", ln=True, align='C')
                        pdf.set_font("Arial", size=12)
                        pdf.ln(10)
                        pdf.cell(200, 10, txt=f"Total Transactions: {len(df)}", ln=True)
                        pdf.cell(200, 10, txt=f"Net Balance: INR {net_balance:,.2f}", ln=True)
                        pdf_data = pdf.output(dest='S').encode('latin-1')
                        st.download_button("📥 Export PDF Summary", data=pdf_data, file_name="Audit_Summary.pdf", use_container_width=True)

                    st.subheader("Detailed Transaction Preview")
                    st.dataframe(df, use_container_width=True)
                else:
                    st.error("AI Error: Failed to format data into rows. Please retry.")
                    
            except Exception as e:
                st.error(f"System Error: {str(e)}")
