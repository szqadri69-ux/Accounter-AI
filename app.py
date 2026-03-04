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

# --- ERROR FIXING MODEL CONFIGURATION ---
try:
    genai.configure(api_key=st.session_state['api_key'])
    # Correct model naming convention to avoid 404 error
    model = genai.GenerativeModel('gemini-1.5-flash') 
except Exception as e:
    st.error(f"Configuration Error: {e}")

# File Uploader
uploaded_docs = st.file_uploader("Upload Financial Documents (PDF, JPG, PNG)", 
                                type=['jpg', 'jpeg', 'png', 'pdf'], 
                                accept_multiple_files=True,
                                key="uploader_main")

# --- DISPLAYING UPLOADED FILES (AS REQUESTED) ---
if uploaded_docs:
    st.markdown("### 📄 Uploaded Documents Information:")
    for doc in uploaded_docs:
        size_kb = doc.size / 1024
        size_str = f"{size_kb/1024:.2f} MB" if size_kb > 1024 else f"{size_kb:.2f} KB"
        # Green box to show file name and size instantly
        st.success(f"✔️ **Document Name:** {doc.name} | **File Size:** `{size_str}`")
    
    st.divider()

    # --- SCAN ACTION ---
    if st.button("🚀 SCAN & GENERATE FINANCIAL REPORT", type="primary", use_container_width=True):
        final_results = []
        
        for doc in uploaded_docs:
            # LOADING SPINNER
            with st.spinner("Waiting... AI is processing your file"):
                try:
                    # Professional Audit Prompt
                    prompt = """
                    Act as a Senior Financial Auditor. Analyze the provided document:
                    1. Categorize strictly as: LOAN, MEDICINE, or GENERAL EXPENSE.
                    2. Extract Date, Party Name, and Total Amount.
                    3. Calculate applicable Tax/GST.
                    4. Give a professional audit summary.
                    Present the final result in a structured Markdown Table.
                    """
                    
                    if doc.type == "application/pdf":
                        # Standard PDF processing
                        response = model.generate_content([prompt, {"mime_type": "application/pdf", "data": doc.getvalue()}])
                    else:
                        # Image processing
                        img = Image.open(doc)
                        response = model.generate_content([prompt, img])
                    
                    # Output per file
                    st.subheader(f"📊 Analysis Result: {doc.name}")
                    st.markdown(response.text)
                    final_results.append({"Document": doc.name, "Analysis": response.text})
                    st.divider()
                    
                except Exception as e:
                    # Catching specific API errors
                    st.error(f"Processing Error for {doc.name}: {str(e)}")

        # --- EXPORT SECTION ---
        if final_results:
            st.success("All documents analyzed successfully.")
            df_export = pd.DataFrame(final_results)
            
            # Excel Buffer
            excel_io = io.BytesIO()
            df_export.to_excel(excel_io, index=False)
            excel_io.seek(0)
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("📥 Download Excel", data=excel_io, file_name="Financial_Report.xlsx", use_container_width=True)
            with col2:
                report_text = "\n\n".join([f"DOC: {r['Document']}\n{r['Analysis']}" for r in final_results])
                st.download_button("📥 Download PDF", data=report_text, file_name="Financial_Report.pdf", use_container_width=True)

else:
    # Placeholder while no files are uploaded
    st.button("Scan Now (Waiting for file...)", disabled=True, use_container_width=True)
    st.info("Please upload files to enable the scanning process.")

# Logout
if st.sidebar.button("Log Out"):
    st.session_state.clear()
    st.rerun()
