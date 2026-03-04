import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import io

# --- PAGE SETUP ---
st.set_page_config(page_title="Accounter-AI | Report Generator", layout="centered")

# --- LOGIN ---
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

# --- MAIN APP ---
st.title("🚀 Accounter-AI")

# ERROR FIX: Yahan model ka naam update kiya hai
genai.configure(api_key=st.session_state['api_key'])
model = genai.GenerativeModel('gemini-1.5-flash-latest') # 'latest' add karne se 404 error nahi aayega

uploaded_docs = st.file_uploader("Upload Documents (PDF/JPG/PNG)", 
                                type=['jpg', 'jpeg', 'png', 'pdf'], 
                                accept_multiple_files=True)

if uploaded_docs:
    st.write(f"📁 {len(uploaded_docs)} file(s) ready.")
    
    if st.button("🚀 SCAN & GENERATE REPORT", type="primary", use_container_width=True):
        final_report_list = []
        
        for doc in uploaded_docs:
            # WAITING MESSAGE
            with st.spinner("Waiting... AI is processing your file"):
                try:
                    # PROMPT: Loan, Medicine, Expense categorization
                    prompt = """Analyze this document as a Professional Auditor:
                    1. Identify if it's a LOAN statement, MEDICINE bill, or GENERAL EXPENSE.
                    2. List all transactions with Date, Name, and Total Amount.
                    3. Calculate total Tax/GST Liability.
                    4. Give a final summary of the financial status.
                    Show output in a clear Table."""
                    
                    if doc.type == "application/pdf":
                        response = model.generate_content([prompt, {"mime_type": "application/pdf", "data": doc.read()}])
                    else:
                        img = Image.open(doc)
                        response = model.generate_content([prompt, img])
                    
                    st.subheader(f"📊 Report: {doc.name}")
                    st.markdown(response.text)
                    
                    # Collecting data for download
                    final_report_list.append({"File": doc.name, "Analysis": response.text})
                    st.divider()
                    
                except Exception as e:
                    st.error(f"Error in {doc.name}: {e}")

        # --- DOWNLOAD SECTION ---
        if final_report_list:
            st.success("✅ Financial Report Complete!")
            
            # Excel Logic
            df_report = pd.DataFrame(final_report_list)
            output_excel = io.BytesIO()
            with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
                df_report.to_excel(writer, index=False, sheet_name='Financial_Report')
            output_excel.seek(0)
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(label="📥 Download Excel Report", 
                                 data=output_excel, 
                                 file_name="Accounter_AI_Report.xlsx", 
                                 mime="application/vnd.ms-excel",
                                 use_container_width=True)
            
            with col2:
                # Text PDF Logic
                report_text = "\n\n".join([f"FILE: {r['File']}\n{r['Analysis']}" for r in final_report_list])
                st.download_button(label="📥 Download PDF Report", 
                                 data=report_text, 
                                 file_name="Accounter_AI_Report.pdf", 
                                 mime="application/pdf",
                                 use_container_width=True)
else:
    st.button("Scan Now", disabled=True, use_container_width=True)

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()
        
