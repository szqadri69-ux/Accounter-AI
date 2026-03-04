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

# --- 2. UNIVERSAL MODEL INITIALIZATION ---
try:
    genai.configure(api_key=st.session_state['api_key'])
    # Using 'gemini-pro' as it is the most stable name across v1 and v1beta
    model = genai.GenerativeModel('gemini-pro') 
except Exception as e:
    st.error(f"Setup Error: {e}")

# --- 3. EXTRACTION ---
def get_pdf_text_structured(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for i, page in enumerate(reader.pages):
        content = page.extract_text()
        if content:
            text += f"\n[PAGE {i+1}]\n" + content
    return text

# --- 4. UI ---
st.title("🚀 Accounter-AI: Enterprise Auditor")

uploaded_file = st.file_uploader("Upload PDF Statement", type=['pdf'])

if uploaded_file:
    if st.button("📊 EXECUTE AUDIT", type="primary", use_container_width=True):
        with st.spinner("Reading PDF..."):
            raw_text = get_pdf_text_structured(uploaded_file)
            
            if not raw_text.strip():
                st.error("Could not read text. Is this a scanned image PDF?")
                st.stop()

        with st.spinner("Analyzing Transactions..."):
            prompt = f"""
            Extract all bank transactions from this text. 
            Return ONLY a CSV table with: Date, Description, Category, Type, Amount.
            Ensure 'Type' is Debit or Credit.
            
            DATA:
            {raw_text[:25000]}
            """
            
            try:
                # Standard call
                response = model.generate_content(prompt)
                
                if response and response.text:
                    csv_data = response.text
                    # Remove markdown wrappers if present
                    csv_data = csv_data.replace('```csv', '').replace('```', '').strip()
                    
                    if "Date" in csv_data:
                        df = pd.read_csv(io.StringIO(csv_data[csv_data.find("Date"):]), on_bad_lines='skip')
                        
                        # Data Polish
                        df['Amount'] = pd.to_numeric(df['Amount'].astype(str).str.replace('[^0-9.]', '', regex=True), errors='coerce').fillna(0)
                        df = df[df['Amount'] > 0]
                        df.insert(0, 'Sr. No.', range(1, 1 + len(df)))

                        # Results
                        dr = df[df['Type'].str.contains('Debit', case=False, na=False)]['Amount'].sum()
                        cr = df[df['Type'].str.contains('Credit', case=False, na=False)]['Amount'].sum()

                        st.success(f"Audit Complete: {len(df)} Records found.")
                        st.metric("Total Expenses", f"₹{dr:,.2f}")
                        st.dataframe(df, use_container_width=True)
                        
                        # Simple Export
                        buf = io.BytesIO()
                        df.to_excel(buf, index=False)
                        st.download_button("📥 Download Excel", data=buf.getvalue(), file_name="Audit.xlsx")
                    else:
                        st.error("AI couldn't format the table. Check raw output below.")
                        st.text(csv_data)
                else:
                    st.error("Model returned an empty response.")
            except Exception as e:
                st.error(f"Final Model Attempt Failed: {e}")
                st.info("Check if your API Key is restricted to specific models in Google AI Studio.")
