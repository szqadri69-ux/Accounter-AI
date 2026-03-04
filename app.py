import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import io

# 1. Page Configuration
st.set_page_config(page_title="Accounter-AI", layout="wide")

# 2. Sidebar for API Key
st.sidebar.title("🔐 Settings")
user_api_key = st.sidebar.text_input("Please enter your Gemini API Key:", type="password")

final_api_key = user_api_key if user_api_key else st.secrets.get("GEMINI_API_KEY", "")

if not final_api_key:
    st.sidebar.warning("⚠️ API Key missing! Enter it in the sidebar to start.")

# 3. Main UI
st.title("🚀 Accounter-AI: Autonomous Accounting")
st.info("Scan bills, upload PDF statements or Excel files for instant accounting.")

tab1, tab2 = st.tabs(["📸 Bill & PDF Scanner", "📊 Excel/CSV Statement"])

with tab1:
    st.write("### Bill & PDF Analysis")
    # PDF aur Images dono ka option
    uploaded_doc = st.file_uploader("Upload Bill or PDF Statement", type=['jpg', 'jpeg', 'png', 'pdf'])
    
    if uploaded_doc and final_api_key:
        if st.button("Analyze Document"):
            with st.spinner("AI is processing the file..."):
                try:
                    genai.configure(api_key=final_api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # Agar file PDF hai
                    if uploaded_doc.type == "application/pdf":
                        pdf_data = uploaded_doc.read()
                        doc_parts = [{"mime_type": "application/pdf", "data": pdf_data}]
                        prompt = "Analyze this PDF statement/bill. Extract all transactions, dates, and amounts into a professional table. Identify if any tax audit is needed."
                        response = model.generate_content([prompt, doc_parts[0]])
                    
                    # Agar file Image hai
                    else:
                        img = Image.open(uploaded_doc)
                        prompt = "Extract Date, Vendor, Total, and GST from this bill. Suggest accounting head."
                        response = model.generate_content([prompt, img])
                    
                    st.success("Analysis Complete!")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Error: {e}")

with tab2:
    st.write("### Structured Data Analysis (Excel/CSV)")
    uploaded_file = st.file_uploader("Upload Structured Statement", type=['csv', 'xlsx'])
    
    if uploaded_file and final_api_key:
        try:
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            st.write("Preview:")
            st.dataframe(df.head(10))
            
            if 'Amount' in df.columns:
                total_turnover = df['Amount'].sum()
                st.metric("Total Turnover", f"₹{total_turnover:,.2f}")
                if total_turnover > 10000000:
                    st.error("🚨 ALERT: Turnover limit exceeded (Sec 44AB). CA Audit Required!")
        except Exception as e:
            st.error(f"File processing error: {e}")

st.divider()
st.caption("Developed by Shehzaad Kutchi Memon")
