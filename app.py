import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import io
import concurrent.futures
import time
from PyPDF2 import PdfReader, PdfWriter
from fpdf import FPDF # PDF generation ke liye

# --- 1. SETUP ---
st.set_page_config(page_title="Accounter-AI | Professional Audit", layout="wide")

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
        prompt = """
        ACT AS A SENIOR CHARTERED ACCOUNTANT. Extract EVERY single transaction.
        Format as CSV: Date, Description, Category, Type (Credit/Debit), Amount.
        Categories: LOAN, MEDICINE, TRAVEL, FOOD, SALARY, INVESTMENT, GENERAL.
        Clean 'Amount' - Numbers only. Do not skip any row.
        """
        response = model.generate_content([prompt, {"mime_type": "application/pdf", "data": pdf_bytes}])
        return response.text if (response.text and "," in response.text) else ""
    except:
        return ""

# --- 3. PDF REPORT GENERATOR FUNCTION ---
def generate_pdf_report(df, summary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Financial Audit Report", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    
    # Summary Section
    pdf.cell(200, 10, txt=f"Total Transactions: {summary['total_rows']}", ln=True)
    pdf.cell(200, 10, txt=f"Total Income (Credit): {summary['credit']:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Total Expense (Debit): {summary['debit']:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Net Balance: {summary['net']:.2f}", ln=True)
    pdf.ln(10)
    
    # Table Header
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(30, 10, "Date", 1, 0, 'C', True)
    pdf.cell(80, 10, "Description", 1, 0, 'C', True)
    pdf.cell(40, 10, "Category", 1, 0, 'C', True)
    pdf.cell(40, 10, "Amount", 1, 1, 'C', True)
    
    # Table Data (Showing first 50 for preview in PDF, rest in Excel)
    pdf.set_font("Arial", size=9)
    for i, row in df.head(50).iterrows():
        pdf.cell(30, 8, str(row['Date']), 1)
        pdf.cell(80, 8, str(row['Description'])[:40], 1)
        pdf.cell(40, 8, str(row['Category']), 1)
        pdf.cell(40, 8, str(row['Amount']), 1, 1)
    
    if len(df) > 50:
        pdf.ln(5)
        pdf.cell(200, 10, txt="... (Detailed ledger available in Excel file)", ln=True)
        
    return pdf.output(dest='S').encode('latin-1')

# --- 4. MAIN INTERFACE ---
st.title("🚀 Accounter-AI: Pro Financial Reporter")

uploaded_file = st.file_uploader("Upload 60-Page Statement", type=['pdf'])

if uploaded_file:
    if st.button("📊 GENERATE COMPLETE AUDIT REPORT", type="primary", use_container_width=True):
        reader = PdfReader(uploaded_file)
        total_pages = len(reader.pages)
        
        chunks = []
        for i in range(0, total_pages, 3):
            writer = PdfWriter()
            for p in range(i, min(i + 3, total_pages)):
                writer.add_page(reader.pages[p])
            chunk_io = io.BytesIO()
            writer.write(chunk_io)
            chunks.append(chunk_io.getvalue())

        progress = st.progress(0)
        combined_csv = "Date,Description,Category,Type,Amount\n"

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(process_chunk_ca, c, i) for i, c in enumerate(chunks)]
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                res = f.result()
                lines = [l for l in res.split('\n') if ',' in l and 'Date' not in l]
                combined_csv += "\n".join(lines) + "\n"
                progress.progress((i + 1) / len(chunks))

        try:
            df = pd.read_csv(io.StringIO(combined_csv))
            df['Amount'] = pd.to_numeric(df['Amount'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            df.insert(0, 'Sr. No.', range(1, 1 + len(df)))

            # Summary Calcs
            total_debit = df[df['Type'].str.contains('Debit', case=False, na=False)]['Amount'].sum()
            total_credit = df[df['Type'].str.contains('Credit', case=False, na=False)]['Amount'].sum()
            net_balance = total_credit - total_debit
            
            summary_stats = {
                'total_rows': len(df),
                'credit': total_credit,
                'debit': total_debit,
                'net': net_balance
            }

            # Display Stats
            st.success(f"Audit Complete: {len(df)} transactions processed.")
            st.metric("Total Debit (Expense)", f"₹{total_debit:,.2f}")
            st.metric("Net Balance", f"₹{net_balance:,.2f}")

            st.divider()
            
            # --- DOWNLOAD OPTIONS ---
            col_ex, col_pdf = st.columns(2)
            
            with col_ex:
                excel_io = io.BytesIO()
                with pd.ExcelWriter(excel_io, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='All_Transactions', index=False)
                st.download_button("📥 Download Full Excel", data=excel_io.getvalue(), 
                                 file_name="CA_Audit_Full.xlsx", use_container_width=True)
            
            with col_pdf:
                pdf_data = generate_pdf_report(df, summary_stats)
                st.download_button("📥 Download PDF Summary Report", data=pdf_data, 
                                 file_name="Financial_Summary.pdf", use_container_width=True)

            st.subheader("Preview (First 100 Rows)")
            st.dataframe(df.head(100), use_container_width=True)

        except Exception as e:
            st.error(f"Reporting failed: {e}")

# Logout
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()
