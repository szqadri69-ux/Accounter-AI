import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import io

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Accounter-AI | Smart Vision", layout="centered")

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

# Model Configuration (404 Error Fix)
genai.configure(api_key=st.session_state['api_key'])
model = genai.GenerativeModel('gemini-1.5-flash')

# File Uploader with 'key' for better tracking
uploaded_docs = st.file_uploader("Upload Documents (PDF/JPG/PNG)", 
                                type=['jpg', 'jpeg', 'png', 'pdf'], 
                                accept_multiple_files=True,
                                key="my_uploader")

# --- FILE DETAILS LOGIC (Jo aapne maanga tha) ---
if uploaded_docs:
    st.markdown("### 📁 Selected Files Details:")
    for doc in uploaded_docs:
        # Size Calculation (KB/MB)
        size_kb = doc.size / 1024
        size_str = f"{size_kb/1024:.2f} MB" if size_kb > 1024 else f"{size_kb:.2f} KB"
        
        # Displaying File Name and Size
        st.success(f"📄 **Name:** {doc.name} | **Size:** `{size_str}` | **Status:** Ready")
    
    st.divider()

    # --- THE SCAN BUTTON (Ab ye tabhi active hoga jab file hogi) ---
    if st.button("🚀 SCAN & GENERATE REPORT", type="primary", use_container_width=True):
        final_results = []
        
        for doc in uploaded_docs:
            # WAITING SPINNER (User ko message dikhane ke liye)
            with st.spinner("Waiting... AI is processing your file"):
                try:
                    prompt = """
                    Act as an expert Financial Analyst. Analyze this document and:
                    1. Categorize strictly into: LOAN, MEDICINE, or EXPENSE.
                    2. Extract Date, Party Name, and Total Amount.
                    3. Calculate Tax Liability.
                    Show output in a clean Table.
                    """
                    
                    if doc.type == "application/pdf":
                        response = model.generate_content([prompt, {"mime_type": "application/pdf", "data": doc.read()}])
                    else:
                        img = Image.open(doc)
                        response = model.generate_content([prompt, img])
                    
                    st.subheader(f"✅ Report for: {doc.name}")
                    st.markdown(response.text)
                    final_results.append({"File": doc.name, "Analysis": response.text})
                    st.divider()
                    
                except Exception as e:
                    st.error(f"Error in {doc.name}: {e}")

        # --- DOWNLOAD OPTIONS ---
        if final_results:
            st.subheader("📥 Download Reports")
            df_export = pd.DataFrame(final_results)
            
            # Excel Buffer
            excel_io = io.BytesIO()
            df_export.to_excel(excel_io, index=False)
            excel_io.seek(0)
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("📊 Download Excel", data=excel_io, file_name="Financial_Report.xlsx", use_container_width=True)
            with col2:
                pdf_text = "\n\n".join([f"{res['File']}\n{res['Analysis']}" for res in final_results])
                st.download_button("📄 Download PDF Report", data=pdf_text, file_name="Financial_Report.pdf", use_container_width=True)

else:
    # AGAR FILE NAHI HAI TOH BUTTON BLUR (Disabled) RAHEGA
    st.button("Scan Now (Waiting for file...)", disabled=True, use_container_width=True)
    st.warning("Pehle 'Browse files' par click karke file select karein.")

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()
    
