import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import io

# 1. Page Configuration
st.set_page_config(page_title="Accounter-AI | Smart Tally Assistant", layout="wide")

# 2. Sidebar for API Key & Limits
st.sidebar.title("🔐 Settings")
user_api_key = st.sidebar.text_input("Please enter your Gemini API Key:", type="password")

# API Logic
final_api_key = user_api_key if user_api_key else st.secrets.get("GEMINI_API_KEY", "")

st.sidebar.divider()
st.sidebar.info("""
**System Limits:**
- Max File Size: 200MB
- Supported: JPG, PNG, PDF, CSV, XLSX
- Multi-file: Yes (Select multiple files to add more)
""")

if not final_api_key:
    st.sidebar.warning("⚠️ API Key missing! Sidebar mein key bharein.")

# 3. Main UI
st.title("🚀 Accounter-AI: Zero-Manual Tally Assistant")
st.subheader("Manual entry bhool jaiye, AI se minto mein accounting karwayein.")

tab1, tab2 = st.tabs(["📄 Bill/PDF to Tally", "📊 Bank Statement Analysis"])

with tab1:
    st.write("### 📸 Scan Bills or PDF Documents")
    # Multi-file support enabled
    uploaded_docs = st.file_uploader("Upload Files (JPG, PNG, PDF) - Add more by selecting multiple", 
                                    type=['jpg', 'jpeg', 'png', 'pdf'], 
                                    accept_multiple_files=True)
    
    if uploaded_docs:
        st.success(f"✅ {len(uploaded_docs)} File(s) Uploaded Successfully!")
        
        if final_api_key:
            if st.button("🚀 Scan Now & Auto-Categorize (Tally Ready)"):
                for uploaded_doc in uploaded_docs:
                    with st.spinner(f"Processing: {uploaded_doc.name}..."):
                        try:
                            genai.configure(api_key=final_api_key)
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            
                            prompt = """
                            Act as an expert Indian Accountant. Extract data from this document and 
                            provide a table with: Date, Vendor, GSTIN, Total Amount, Tax Rate.
                            CRITICAL: Suggest the 'Tally Ledger Group' (e.g., Indirect Expenses, 
                            Purchase A/c, Fixed Assets) so it can be entered in Tally in minutes.
                            """
                            
                            if uploaded_doc.type == "application/pdf":
                                pdf_data = uploaded_doc.read()
                                response = model.generate_content([prompt, {"mime_type": "application/pdf", "data": pdf_data}])
                            else:
                                img = Image.open(uploaded_doc)
                                response = model.generate_content([prompt, img])
                            
                            st.write(f"**Results for {uploaded_doc.name}:**")
                            st.markdown(response.text)
                            st.divider()
                        except Exception as e:
                            st.error(f"Error processing {uploaded_doc.name}: {e}")

with tab2:
    st.write("### 📊 Bulk Statement Analysis (Excel/CSV)")
    uploaded_file = st.file_uploader("Choose Bank Statement", type=['csv', 'xlsx'])
    
    if uploaded_file:
        st.success("✅ Statement Uploaded Successfully!")
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        st.write("Data Preview:")
        st.dataframe(df.head(5))

        if st.button("🔍 Scan Now & Check Audit Limits"):
            if final_api_key:
                try:
                    # Turnover Calculation
                    amount_col = next((c for c in df.columns if any(x in c.lower() for x in ['amount', 'credit', 'total'])), None)
                    if amount_col:
                        total = pd.to_numeric(df[amount_col], errors='coerce').sum()
                        st.metric("Total Turnover (FY)", f"₹{total:,.2f}")
                        
                        if total > 10000000:
                            st.error("🚨 AUDIT ALERT: Section 44AB ke tehat CA Audit zaroori hai (Turnover > 1Cr).")
                        else:
                            st.success("✅ Turnover limit ke andar hai.")
                    
                    st.info("AI is now categorizing transactions for Tally import...")
                    genai.configure(api_key=final_api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content(f"Analyze these transactions and group them for Tally entry: {df.head(15).to_string()}")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Calculation Error: {e}")

st.divider()
st.caption("Developed by Shehzaad Kutchi Memon | The Future of Automated Accounting")
                                      
