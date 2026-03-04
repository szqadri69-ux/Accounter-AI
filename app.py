import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
from PyPDF2 import PdfReader

st.set_page_config(page_title="Accounter-AI | High Precision", layout="wide")

if 'api_key' not in st.session_state:
    st.title("🔐 Accounter-AI Login")
    api_key_input = st.text_input("Enter Gemini API Key:", type="password")
    if st.button("Login"):
        st.session_state['api_key'] = api_key_input
        st.rerun()
    st.stop()

# --- STABLE CONFIG ---
# transport='rest' ensures your new key works without 404 errors
genai.configure(api_key=st.session_state['api_key'], transport='rest')
model = genai.GenerativeModel('gemini-1.5-flash')

def extract_transactions(pdf_bytes):
    try:
        prompt = """
        ACT AS A PROFESSIONAL AUDITOR. 
        Extract EVERY transaction from this document. 
        Return ONLY a CSV table with headers: Date, Description, Type, Amount.
        Important: Type must be exactly 'Debit' or 'Credit'.
        Clean 'Amount' - Numbers only, no ₹ or commas.
        """
        response = model.generate_content([prompt, {"mime_type": "application/pdf", "data": pdf_bytes}])
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

st.title("🚀 Accounter-AI: High Precision Mode")

uploaded_file = st.file_uploader("Upload Bank Statement", type=['pdf'])

if uploaded_file:
    if st.button("📊 START DEEP CALCULATION", type="primary", use_container_width=True):
        with st.spinner("AI is reading and calculating..."):
            raw_data = extract_transactions(uploaded_file.getvalue())
            
            if "Error" in raw_data or not raw_data:
                st.error("AI couldn't find transactions.")
            else:
                try:
                    # Clean AI response
                    csv_start = raw_data.find("Date")
                    clean_csv = raw_data[csv_start:].replace('```csv', '').replace('```', '').strip()
                    
                    df = pd.read_csv(io.StringIO(clean_csv), on_bad_lines='skip')
                    
                    # 1. Clean Column Names (Removes hidden spaces)
                    df.columns = df.columns.str.strip()
                    
                    # 2. Clean 'Amount' column
                    df['Amount'] = pd.to_numeric(df['Amount'].astype(str).str.replace('[^0-9.]', '', regex=True), errors='coerce').fillna(0)
                    
                    # 3. Clean 'Type' column (Critical fix for Zero Calculation)
                    df['Type'] = df['Type'].astype(str).str.strip().str.capitalize()
                    
                    # 4. Filter and Calculate
                    df = df[df['Amount'] > 0]
                    total_debit = df[df['Type'] == 'Debit']['Amount'].sum()
                    total_credit = df[df['Type'] == 'Credit']['Amount'].sum()
                    
                    st.success(f"Calculated {len(df)} transactions!")
                    
                    # Results Display
                    c1, c2 = st.columns(2)
                    c1.metric("Total Expenses (Debit)", f"₹{total_debit:,.2f}")
                    c2.metric("Total Income (Credit)", f"₹{total_credit:,.2f}")
                    
                    st.dataframe(df, use_container_width=True)
                    
                    # Excel Download
                    excel_io = io.BytesIO()
                    df.to_excel(excel_io, index=False)
                    st.download_button("📥 Download Excel Report", data=excel_io.getvalue(), file_name="Audit_Report.xlsx")
                    
                except Exception as e:
                    st.error(f"Formatting error: {e}")
                    st.text(raw_data)
                    
