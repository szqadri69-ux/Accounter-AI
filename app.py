import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
from PyPDF2 import PdfReader

st.set_page_config(page_title="Accounter-AI", layout="wide")

if 'api_key' not in st.session_state:
    st.title("🔐 Login")
    api_key_input = st.text_input("Enter API Key:", type="password")
    if st.button("Connect"):
        st.session_state['api_key'] = api_key_input
        st.rerun()
    st.stop()

try:
    genai.configure(api_key=st.session_state['api_key'], transport='rest')
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Setup Error: {e}")

st.title("🚀 Accounter-AI")

uploaded_file = st.file_uploader("Upload PDF Statement", type=['pdf'])

if uploaded_file:
    if st.button("EXECUTE AUDIT", type="primary", use_container_width=True):
        with st.spinner("Processing..."):
            reader = PdfReader(uploaded_file)
            raw_text = "".join([p.extract_text() or "" for p in reader.pages])
            
            try:
                prompt = f"Extract bank transactions as CSV (Date, Description, Type, Amount). Only return CSV data: {raw_text[:20000]}"
                response = model.generate_content(prompt)
                
                if response and response.text:
                    st.success("Audit Complete!")
                    csv_data = response.text.replace('```csv', '').replace('```', '').strip()
                    
                    if "Date" in csv_data:
                        df = pd.read_csv(io.StringIO(csv_data[csv_data.find("Date"):]), on_bad_lines='skip')
                        st.dataframe(df, use_container_width=True)
                        
                        buf = io.BytesIO()
                        df.to_excel(buf, index=False)
                        st.download_button(
                            label="📥 Download Excel Report",
                            data=buf.getvalue(),
                            file_name="Audit_Report.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.error("Format Error. Please try again.")
                else:
                    st.error("No response from AI.")
            except Exception as e:
                st.error(f"Error: {e}")
