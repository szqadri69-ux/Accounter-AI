import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import io
import concurrent.futures
import time
from PyPDF2 import PdfReader, PdfWriter
from fpdf import FPDF

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Accounter-AI | Pro Audit", layout="wide")

if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.title("🔐 Accounter-AI Login")
    api_key_input = st.text_input("Enter Gemini API Key:", type="password")
    if st.button("Login"):
        if api_key_input:
            st.session_state['api_key'] = api_key_input
            st.session_state['authenticated'] = True
            st.rerun()
    st.stop()

# --- 2. AI CONFIG ---
genai.configure(api_key=st.session_state['api_key'])
model = genai.GenerativeModel('gemini-1.5-flash')

def process_chunk_ca(pdf_bytes, chunk_id):
    try:
        # Improved Prompt for better extraction from UPI Statements
        prompt = """
        ACT AS A SENIOR AUDITOR. Extract EVERY transaction from this statement.
        Output ONLY in this CSV format:
        Date,Description,Category,Type,Amount
        
        Rules:
        1. Date should be in DD/MM/YYYY.
        2. Type must be exactly 'Debit' or 'Credit'.
        3. Amount must be a clean number (no symbols like ₹ or commas).
        4. Category should be: LOAN, MEDICINE, TRAVEL, FOOD, or GENERAL.
        5. If a transaction is split across lines, merge it.
        """
        response = model.generate_content([prompt, {"mime_type": "application/pdf", "data": pdf_bytes}])
        return response.text if (response.text and "," in response.text) else ""
    except:
        return ""

def generate_pdf_report(df, summary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Financial Audit Summary Report", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Total Entries: {summary['total_rows']}", ln=True)
    pdf.cell(200, 10, txt=f"Total Expenses (Debit): {summary['debit']:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Total Income (Credit): {summary['credit']:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Final Net Balance: {summary['net']:.2f}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- 3. MAIN UI ---
st.title("🚀 Accounter-AI: Pro Financial Reporter")

uploaded_file = st.file_uploader("Upload 60-Page Statement", type=['pdf'])

if uploaded_file:
    if st.button("⚡ GENERATE COMPLETE AUDIT REPORT", type="primary", use_container_width=True):
        reader = PdfReader(uploaded_file)
        total_pages = len(reader.pages)
        
        # 3-page chunks for precision
        chunks = []
        for i in range(0, total_pages, 3):
            writer = PdfWriter()
            for p in range(i, min(i + 3, total_pages)):
                writer.add_page(reader.pages[p])
            chunk_io = io.BytesIO()
            writer.write(chunk_io)
            chunks.append(chunk_io.getvalue())

        progress = st.progress(0)
        status = st.empty()
        combined_csv = "Date,Description,Category,Type,Amount\n"

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(process_chunk_ca, c, i) for i, c in enumerate(chunks)]
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                res = f.result()
                # Filtering out noise
                lines = [l.strip() for l in res.split('\n') if ',' in l and 'Date' not in l.lower()]
                combined_csv += "\n".join(lines) + "\n"
                progress.progress((i + 1) / len(chunks))
                status.text(f"Scanning Batch {i+1}/{len(chunks)}...")

        try:
            # Load and clean data
            df = pd.read_csv(io.StringIO(combined_csv), on_bad_lines='skip')
            df['Amount'] = pd.to_numeric(df['Amount'].astype(str).str.replace('[^0-9.]', '', regex=True), errors='coerce').fillna(0)
            
            # Remove empty rows
            df = df[df['Amount'] > 0]
            df.insert(0, 'Sr. No.', range(1, 1 + len(df)))

            # Summary Calcs
            total_debit = df[df['Type'].str.contains('Debit', case=False, na=False)]['Amount'].sum()
            total_credit = df[df['Type'].str.contains('Credit', case=False, na=False)]['Amount'].sum()
            
            summary_stats = {'total_rows': len(df), 'credit': total_credit, 'debit': total_debit, 'net': total_credit - total_debit}

            st.divider()
            col1, col2 = st.columns(2)
            col1.metric("Total Debit (Expense)", f"₹{total_debit:,.2f}")
            col2.metric("Net Balance", f"₹{summary_stats['net']:,.2f}")

            # Download buttons
            c_ex, c_pdf = st.columns(2)
            with c_ex:
                excel_io = io.BytesIO()
                df.to_excel(excel_io, index=False)
                st.download_button("📥 Download Full Excel", data=excel_io.getvalue(), file_name="Full_Audit.xlsx")
            with c_pdf:
                pdf_data = generate_pdf_report(df, summary_stats)
                st.download_button("📥 Download PDF Summary", data=pdf_data, file_name="Summary.pdf")

            st.subheader("Preview (First 100 Rows)")
            st.dataframe(df, use_container_width=True)

        except Exception as e:
            st.error(f"Audit Error: No transactions found. Try again or check file quality.")

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()
