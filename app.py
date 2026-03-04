import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import io

# --- PAGE SETUP ---
st.set_page_config(page_title="Accounter-AI | Financial Reports", layout="centered")

# --- LOGIN SYSTEM ---
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

genai.configure(api_key=st.session_state['api_key'])
model = genai.GenerativeModel('gemini-1.5-flash')

uploaded_docs = st.file_uploader("Upload Documents (PDF/JPG/PNG)", 
                                type=['jpg', 'jpeg', 'png', 'pdf'], 
                                accept_multiple_files=True)

if uploaded_docs:
    st.write(f"📁 {len(uploaded_docs)} file(s) ready.")
    
    if st.button("🚀 SCAN & GENERATE REPORT", type="primary", use_container_width=True):
        all_results = []
        
        for doc in uploaded_docs:
            with st.spinner("Waiting... AI is processing your file"):
                try:
                    prompt = """
                    Act as a Senior Financial Consultant. Analyze this document:
                    1. List all transactions.
                    2. Categorize each into: LOAN, MEDICINE, or EXPENSE.
                    3. Extract Date, Party Name, GST, and Total Amount.
                    4. Calculate Total Tax Liability.
                    Show result in a clear Table.
                    """
                    
                    if doc.type == "application/pdf":
                        response = model.generate_content([prompt, {"mime_type": "application/pdf", "data": doc.read()}])
                    else:
                        img = Image.open(doc)
                        response = model.generate_content([prompt, img])
                    
                    st.subheader(f"✅ Financial Report: {doc.name}")
                    st.markdown(response.text)
                    
                    # Data for Export (Simulated)
                    all_results.append({"File": doc.name, "Analysis": response.text})
                    st.divider()
                    
                except Exception as e:
                    st.error(f"Error: {e}")

        # --- DOWNLOAD OPTIONS ---
        if all_results:
            st.subheader("📥 Download Your Report")
            col1, col2 = st.columns(2)
            
            # Excel Export
            df = pd.DataFrame(all_results)
            excel_data = io.BytesIO()
            df.to_excel(excel_data, index=False)
            excel_data.seek(0)
            
            with col1:
                st.download_button(
                    label="📊 Download Excel",
                    data=excel_data,
                    file_name="Financial_Report.xlsx",
                    mime="application/vnd.ms-excel",
                    use_container_width=True
                )
            
            with col2:
                # PDF Placeholder (Text based)
                pdf_data = "\n".join([f"{res['File']}\n{res['Analysis']}" for res in all_results])
                st.download_button(
                    label="📄 Download PDF",
                    data=pdf_data,
                    file_name="Financial_Report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
else:
    st.button("Scan Now", disabled=True, use_container_width=True)

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()
    
