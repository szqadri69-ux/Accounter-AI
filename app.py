import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image

# 1. Page Configuration
st.set_page_config(page_title="Accounter-AI", layout="wide")

# 2. Sidebar for API Key
st.sidebar.title("🔐 Settings")
user_api_key = st.sidebar.text_input("Please enter your Gemini API Key:", type="password")

# API Key check logic
final_api_key = user_api_key if user_api_key else st.secrets.get("GEMINI_API_KEY", "")

if not final_api_key:
    st.sidebar.warning("⚠️ API Key missing! Enter it in the sidebar to start.")

# 3. Main UI
st.title("🚀 Accounter-AI: Autonomous Accounting")
st.info("Scan bills or upload statements for instant accounting classification.")

tab1, tab2 = st.tabs(["📸 Bill Scanner", "📊 Bank Statement"])

with tab1:
    st.write("### Live Bill Scanner")
    show_camera = st.checkbox("Turn on Camera")
    
    # Camera or File Upload
    img_file = st.camera_input("Scan Bill") if show_camera else st.file_uploader("Upload Bill Image", type=['jpg', 'jpeg', 'png'])
    
    if img_file and final_api_key:
        if st.button("Analyze with AI"):
            with st.spinner("AI is reading the bill..."):
                try:
                    genai.configure(api_key=final_api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    img = Image.open(img_file)
                    
                    prompt = "Extract Date, Vendor Name, Total Amount, and GST from this bill. Suggest accounting head (Asset/Expense)."
                    response = model.generate_content([prompt, img])
                    
                    st.success("Analysis Complete!")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Error: {e}")

with tab2:
    st.write("### Statement Analysis")
    uploaded_file = st.file_uploader("Upload Bank Statement (CSV/Excel)", type=['csv', 'xlsx'])
    
    if uploaded_file and final_api_key:
        try:
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            st.write("Preview of Transactions:")
            st.dataframe(df.head(10))
            
            # Turnover Alert Logic (Assuming 'Amount' column exists)
            if 'Amount' in df.columns:
                total_turnover = df['Amount'].sum()
                st.metric("Total Turnover", f"₹{total_turnover:,.2f}")
                if total_turnover > 10000000:
                    st.error("🚨 ALERT: Turnover limit exceeded (Sec 44AB). CA Audit & Signature Required!")
        except Exception as e:
            st.error(f"File processing error: {e}")

st.divider()
st.caption("Developed by Shehzaad Kutchi Memon")
           
