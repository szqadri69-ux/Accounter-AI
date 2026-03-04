import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import io

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Accounter-AI | Professional", layout="centered")

# --- 2. LOGIN SYSTEM ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.title("🔐 Accounter-AI Login")
    api_key_input = st.text_input("Enter your Gemini API Key:", type="password")
    if st.button("Login"):
        if api_key_input:
            st.session_state['api_key'] = api_key_input
            st.session_state['authenticated'] = True
            st.rerun()
    st.stop()

# --- 3. MAIN APPLICATION ---
st.title("🚀 Accounter-AI")
st.subheader("Automated Financial Document Analysis")

# --- FIXED MODEL NAME TO AVOID 404 ERROR ---
try:
    genai.configure(api_key=st.session_state['api_key'])
    # Correct naming: no prefix 'models/' needed here
    model = genai.GenerativeModel('gemini-1.5-flash') 
except Exception as e:
    st.error(f"Configuration Error: {e}")

# File Uploader with unique state key
uploaded_docs = st.file_uploader("Upload Financial Documents (PDF, JPG, PNG)", 
                                type=['jpg', 'jpeg', 'png', 'pdf'], 
                                accept_multiple_files=True,
                                key="app_uploader")

# --- SHOWING FILE NAME & SIZE IMMEDIATELY ---
if uploaded_docs:
    st.markdown("### 📄 Uploaded Documents Information:")
    for doc in uploaded_docs:
        size_kb = doc.size / 1024
        size_str = f"{size_kb/1024:.2f} MB" if size_kb > 1024 else f"{size_kb:.2f} KB"
        # Immediate display of metadata as requested
        st.success(f"✔️ **Document Name:** {doc.name} | **File Size:** `{size_str}`")
    
    st.divider()

    # --- ACTION BUTTON ---
    if st.button("🚀 SCAN & GENERATE FINANCIAL REPORT", type="primary", use_container_width=True):
        final_reports = []
        
        for doc in uploaded_docs:
            # PROFESSIONAL LOADING SPINNER
            with st.spinner("Waiting... AI is processing your file"):
                try:
                    prompt = """
                    Act as a Senior Financial Auditor. Analyze the document:
                    1. Categorize as: LOAN, MEDICINE, or GENERAL EXPENSE.
                    2. Extract Date, Party Name, and Total Amount.
                    3. Identify Tax/GST components.
                    Present data in a structured Markdown Table.
                    """
                    
                    if doc.type == "application/pdf":
                        response = model.generate_content([prompt, {"mime_type": "application/pdf", "data": doc.getvalue()}])
                    else:
                        img = Image.open(doc)
                        response = model.generate_content([prompt, img])
                    
                    st.subheader(f"📊 Analysis: {doc.name}")
                    st.markdown(response.text)
                    final_reports.append({"Document": doc.name, "Analysis": response.text})
                    st.divider()
                    
                except Exception as e:
                    st.error(f"Error in {doc.name}: {str(e)}")

        # --- EXPORT SECTION ---
        if final_reports:
            df = pd.DataFrame(final_reports)
            excel_io = io.BytesIO()
            df.to_excel(excel_io, index=False)
            excel_io.seek(0)
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("📥 Download Excel", data=excel_io, file_name="Report.xlsx", use_container_width=True)
            with col2:
                report_txt = "\n\n".join([f"DOC: {r['Document']}\n{r['Analysis']}" for r in final_reports])
                st.download_button("📥 Download PDF", data=report_txt, file_name="Report.pdf", use_container_width=True)

else:
    # Button state when no file is present
    st.button("Scan Now (Waiting for file...)", disabled=True, use_container_width=True)
    st.info("Please upload files to enable the scanning process.")

# Sidebar Logout
if st.sidebar.button("Log Out"):
    st.session_state.clear()
    st.rerun()
