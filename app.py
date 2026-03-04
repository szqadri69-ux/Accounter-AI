import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
from PyPDF2 import PdfReader
from fpdf import FPDF

# --- CONFIG ---
st.set_page_config(page_title="Accounter-AI | High Density Mode", layout="wide")

if 'api_key' not in st.session_state:
    st.title("🔐 Login")
    api_key_input = st.text_input("Enter Gemini API Key:", type="password")
    if st.button("Login"):
        st.session_state['api_key'] = api_key_input
        st.rerun()
    st.stop()

genai.configure(api_key=st.session_state['api_key'])
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 1. LOCAL TEXT EXTRACTION (ROW-BY-ROW) ---
def get_pdf_text_structured(uploaded_file):
    reader = PdfReader(uploaded_file)
    structured_text = ""
    for i, page in enumerate(reader.pages):
        # Adding Page markers so AI doesn't mix data between pages
        structured_text += f"\n--- PAGE {i+1} START ---\n"
        structured_text += page.extract_text()
        structured_text += f"\n--- PAGE {i+1} END ---\n"
    return structured_text

# --- 2. MAIN UI ---
st.title("🚀 Accounter-AI: Pro Financial Auditor")
st.warning("Row-by-Row Mode Active: Har transaction ko scan karke tally kiya jayega.")

uploaded_file = st.file_uploader("Upload Full Statement (PDF)", type=['pdf'])

if uploaded_file:
    if st.button("📊 EXECUTE FULL AUDIT"):
        with st.spinner("Extracting text from PDF..."):
            raw_text = get_pdf_text_structured(uploaded_file)
            
            if len(raw_text.strip()) < 50:
                st.error("Text extract nahi ho paya. Shayad ye scan copy hai. Image Scan ki zaroorat hai.")
                st.stop()

        with st.spinner("AI is processing row-by-row..."):
            # Strict prompt to ensure AI returns one row per transaction
            prompt = f"""
            ACT AS A SENIOR BANK AUDITOR. 
            I am giving you text data from a bank statement with page markers.
            
            YOUR TASK: 
            Extract EVERY single transaction line. 
            Do NOT summarize. Do NOT skip any row.
            
            Return ONLY a CSV format with these 5 columns:
            Date, Description, Category, Type, Amount
            
            Rules:
            1. 'Type' must be 'Debit' or 'Credit'.
            2. 'Amount' must be numbers only (No symbols).
            3. If a row is unclear, still extract it and put 'CHECK' in category.
            
            DATA:
            {raw_text[:30000]}
            """
            
            try:
                response = model.generate_content(prompt)
                csv_output = response.text
                
                # Cleaning to ensure we only get CSV part
                if "Date," in csv_output:
                    start_idx = csv_output.find("Date,")
                    clean_csv = csv_output[start_idx:]
                    
                    df = pd.read_csv(io.StringIO(clean_csv), on_bad_lines='skip')
                    
                    # Data Cleaning & Serial Numbers
                    df['Amount'] = pd.to_numeric(df['Amount'].astype(str).str.replace('[^0-9.]', '', regex=True), errors='coerce').fillna(0)
                    df = df[df['Amount'] > 0]
                    df.insert(0, 'Sr. No.', range(1, 1 + len(df)))

                    # Sums
                    total_debit = df[df['Type'].str.contains('Debit', case=False, na=False)]['Amount'].sum()
                    total_credit = df[df['Type'].str.contains('Credit', case=False, na=False)]['Amount'].sum()

                    # Interface Results
                    st.success(f"Audit Complete! Total Transactions Found: {len(df)}")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Total Rows", len(df))
                    c2.metric("Total Expense", f"₹{total_debit:,.2f}")
                    c3.metric("Total Income", f"₹{total_credit:,.2f}")

                    # --- DUAL DOWNLOAD ---
                    st.divider()
                    down1, down2 = st.columns(2)
                    with down1:
                        excel_io = io.BytesIO()
                        df.to_excel(excel_io, index=False)
                        st.download_button("📥 Download Full Excel", data=excel_io.getvalue(), file_name="Full_Audit.xlsx", use_container_width=True)
                    
                    with down2:
                        pdf = FPDF()
                        pdf.add_page()
                        pdf.set_font("Arial", size=12)
                        pdf.cell(200, 10, txt="Financial Summary", ln=True, align='C')
                        pdf.cell(200, 10, txt=f"Total Transactions: {len(df)}", ln=True)
                        pdf.cell(200, 10, txt=f"Net Savings: {total_credit - total_debit}", ln=True)
                        pdf_data = pdf.output(dest='S').encode('latin-1')
                        st.download_button("📥 Download PDF Report", data=pdf_data, file_name="Report.pdf", use_container_width=True)

                    st.dataframe(df, use_container_width=True)
                else:
                    st.error("AI couldn't format the data. Check Raw Text.")
                    st.text(csv_output)
                    
            except Exception as e:
                st.error(f"Error: {e}")
