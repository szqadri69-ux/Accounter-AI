import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import io

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Accounter-AI | Professional Edition", layout="centered")

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

# Configure AI Model
genai.configure(api_key=st.session_state['api_key'])
model = genai.GenerativeModel('gemini-1.5-flash')

# File Uploader Component
uploaded_docs = st.file_uploader("Upload Financial Documents (PDF, JPG, PNG)", 
                                type=['jpg', 'jpeg', 'png', 'pdf'], 
                                accept_multiple_files=True)

# --- DISPLAY FILE METADATA (NAME & SIZE) ---
if uploaded_docs:
    st.markdown("### 📄 Uploaded Documents Information:")
    for doc in uploaded_docs:
        # Calculate file size for professional display
        size_kb = doc.size / 1024
        size_str = f"{size_kb/1024:.2f} MB" if size_kb > 1024 else f"{size_kb:.2f} KB"
        
        # Displaying File Name and Size clearly
        st.success(f"✔️ **Document Name:** {doc.name} | **File Size:** `{size_str}`")
    
    st.divider()

    # --- ACTION BUTTON (Active when files are present) ---
    if st.button("🚀 SCAN & GENERATE FINANCIAL REPORT", type="primary", use_container_width=True):
        final_reports = []
        
        for doc in uploaded_docs:
            # PROFESSIONAL STATUS INDICATOR
            with st.spinner("Waiting... AI is processing your file"):
                try:
                    # AI Analysis Prompt
                    prompt = """
                    Act as a Senior Financial Auditor. Analyze the provided document:
                    1. Categorize the transaction as: LOAN, MEDICINE, or GENERAL EXPENSE.
                    2. Extract key data: Date, Vendor/Party Name, and Total Amount.
                    3. Identify any applicable Tax or GST components.
                    4. Provide a brief professional summary.
                    Present the final data in a structured Markdown Table.
                    """
                    
                    if doc.type == "application/pdf":
                        response = model.generate_content([prompt, {"mime_type": "application/pdf", "data": doc.getvalue()}])
                    else:
                        img = Image.open(doc)
                        response = model.generate_content([prompt, img])
                    
                    # Displaying the Result per file
                    st.subheader(f"📊 Financial Analysis: {doc.name}")
                    st.markdown(response.text)
                    final_reports.append({"Document": doc.name, "Analysis_Summary": response.text})
                    st.divider()
                    
                except Exception as e:
                    st.error(f"Error processing {doc.name}: {str(e)}")

        # --- EXPORT OPTIONS ---
        if final_reports:
            st.success("Analysis Completed Successfully.")
            df_export = pd.DataFrame(final_reports)
            
            # Prepare Excel Buffer
            excel_io = io.BytesIO()
            df_export.to_excel(excel_io, index=False)
            excel_io.seek(0)
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 Download Excel Report", 
                    data=excel_io, 
                    file_name="Accounter_AI_Report.xlsx", 
                    use_container_width=True
                )
            with col2:
                # Text-based PDF Representation
                report_content = "\n\n".join([f"DOC: {r['Document']}\n{r['Analysis_Summary']}" for r in final_reports])
                st.download_button(
                    label="📥 Download PDF Report", 
                    data=report_content, 
                    file_name="Accounter_AI_Report.pdf", 
                    use_container_width=True
                )

else:
    # Button remains disabled until files are uploaded
    st.button("Scan Now (Waiting for file...)", disabled=True, use_container_width=True)
    st.info("Please upload one or more files to enable the scanning process.")

# Logout Functionality
if st.sidebar.button("Log Out"):
    st.session_state.clear()
    st.rerun()
