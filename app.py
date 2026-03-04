import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import io

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Accounter-AI", layout="centered")

# --- 2. LOGIN FLOW ---
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

# --- 3. MAIN APP ---
st.title("🚀 Accounter-AI")

# ERROR FIX: Yahan model name ko ekdum correct kiya hai taaki 404 error na aaye
try:
    genai.configure(api_key=st.session_state['api_key'])
    # Free Tier ke liye ye model sabse best hai
    model = genai.GenerativeModel('gemini-1.5-flash') 
except Exception as e:
    st.error(f"Configuration Error: {e}")

# File Uploader: Naam aur Size dikhayega
uploaded_docs = st.file_uploader("Upload Documents (PDF/JPG/PNG)", 
                                type=['jpg', 'jpeg', 'png', 'pdf'], 
                                accept_multiple_files=True)

if uploaded_docs:
    st.info(f"📁 {len(uploaded_docs)} file(s) ready for analysis.")
    
    # SCAN BUTTON
    if st.button("🚀 SCAN & GENERATE REPORT", type="primary", use_container_width=True):
        final_results = []
        
        for doc in uploaded_docs:
            # --- ONLY WAITING MESSAGE ---
            with st.spinner("Waiting... AI is processing your file"):
                try:
                    # AI ko instructions: Loan, Expense, Medicine ko alag kare
                    prompt = """Analyze this document as a Financial Auditor. 
                    1. Categorize strictly as: LOAN, MEDICINE, or EXPENSE.
                    2. Extract Date, Party Name, and Total Amount.
                    3. Calculate Tax Liability.
                    4. Give a summary of the financial impact.
                    Show the output in a clean Table."""
                    
                    if doc.type == "application/pdf":
                        response = model.generate_content([prompt, {"mime_type": "application/pdf", "data": doc.read()}])
                    else:
                        img = Image.open(doc)
                        response = model.generate_content([prompt, img])
                    
                    # Screen par result
                    st.subheader(f"✅ Report: {doc.name}")
                    st.markdown(response.text)
                    
                    # Data collect for Excel
                    final_results.append({"File": doc.name, "Analysis": response.text})
                    st.divider()
                    
                except Exception as e:
                    st.error(f"Error processing {doc.name}: {e}. Try refreshing your API key.")

        # --- DOWNLOAD SECTION (EXCEL & PDF) ---
        if final_results:
            st.success("Analysis Complete!")
            col1, col2 = st.columns(2)
            
            # Excel Generator
            df_final = pd.DataFrame(final_results)
            excel_buffer = io.BytesIO()
            df_final.to_excel(excel_buffer, index=False)
            excel_buffer.seek(0)
            
            with col1:
                st.download_button(label="📥 Download Excel Report", 
                                 data=excel_buffer, 
                                 file_name="Financial_Report.xlsx", 
                                 mime="application/vnd.ms-excel",
                                 use_container_width=True)
            
            with col2:
                # Text based PDF content
                pdf_content = "\n\n".join([f"FILE: {r['File']}\n{r['Analysis']}" for r in final_results])
                st.download_button(label="📥 Download PDF Report", 
                                 data=pdf_content, 
                                 file_name="Financial_Report.pdf", 
                                 mime="application/pdf",
                                 use_container_width=True)
else:
    # Button blur rahega jab tak file na ho
    st.button("Scan Now", disabled=True, use_container_width=True)

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()
    
