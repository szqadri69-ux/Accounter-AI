import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image

# --- PAGE SETUP ---
st.set_page_config(page_title="Accounter-AI", layout="centered")

# --- 1. LOGIN SCREEN (API KEY) ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.title("🔐 Accounter-AI Login")
    api_key_input = st.text_input("Enter your Gemini API Key to access:", type="password")
    if st.button("Login"):
        if api_key_input:
            st.session_state['api_key'] = api_key_input
            st.session_state['authenticated'] = True
            st.rerun()
        else:
            st.error("Please enter a valid key.")
    st.stop() # App yahan ruk jayegi jab tak login na ho

# --- 2. MAIN APP INTERFACE (Login ke baad) ---
st.title("🚀 Accounter-AI")

# API Setup
genai.configure(api_key=st.session_state['api_key'])
model = genai.GenerativeModel('gemini-1.5-flash')

# Tabs for organization
tab1, tab2 = st.tabs(["📄 Document Scanner", "📊 Statement Analyst"])

with tab1:
    # Multiple files select karne ka option
    uploaded_docs = st.file_uploader("Upload Files (JPG, PNG, PDF)", 
                                    type=['jpg', 'jpeg', 'png', 'pdf'], 
                                    accept_multiple_files=True)
    
    if uploaded_docs:
        # File counter
        st.info(f"📁 {len(uploaded_docs)} File(s) selected. You can add more.")
        
        # 3. SUBMIT BUTTON
        if st.button("Submit & Scan Now"):
            for doc in uploaded_docs:
                with st.spinner(f"Processing {doc.name}..."):
                    try:
                        prompt = "Extract Date, Vendor, GSTIN, Total, and Tally Ledger Group into a table."
                        if doc.type == "application/pdf":
                            response = model.generate_content([prompt, {"mime_type": "application/pdf", "data": doc.read()}])
                        else:
                            img = Image.open(doc)
                            response = model.generate_content([prompt, img])
                        
                        st.subheader(f"Results: {doc.name}")
                        st.markdown(response.text)
                        st.divider()
                    except Exception as e:
                        st.error(f"Error in {doc.name}: {e}")

with tab2:
    uploaded_statement = st.file_uploader("Upload Bank Statement (Excel/CSV)", type=['csv', 'xlsx'])
    
    if uploaded_statement:
        st.success(f"✅ {uploaded_statement.name} ready for analysis.")
        
        if st.button("Submit Statement"):
            with st.spinner("Analyzing..."):
                df = pd.read_csv(uploaded_statement) if uploaded_statement.name.endswith('.csv') else pd.read_excel(uploaded_statement)
                st.write("Data Summary:")
                st.dataframe(df.head(10))
                # Logic to check 1Cr limit
                amount_col = next((c for c in df.columns if 'amount' in c.lower() or 'total' in c.lower()), None)
                if amount_col:
                    total = pd.to_numeric(df[amount_col], errors='coerce').sum()
                    if total > 10000000:
                        st.error(f"🚨 ALERT: Turnover ₹{total:,.2f} exceeds 1 Crore. Audit Required!")
                    else:
                        st.success(f"Turnover: ₹{total:,.2f} (Under Limit)")

# Logout option
if st.sidebar.button("Logout / Change Key"):
    st.session_state['authenticated'] = False
    st.rerun()
