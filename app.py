import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
import concurrent.futures

# --- 1. CONFIG & BRANDING ---
st.set_page_config(page_title="Accounter-AI | Shehzaad Kutchi Memon", layout="wide")

if 'api_key' not in st.session_state:
    st.title("🔐 Accounter-AI Secure Login")
    api_key_input = st.text_input("Enter Gemini API Key:", type="password")
    if st.button("Connect & Initialize"):
        st.session_state['api_key'] = api_key_input
        st.rerun()
    st.stop()

genai.configure(api_key=st.session_state['api_key'], transport='rest')
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. UNIVERSAL FETCH FUNCTION (FIXED FOR EXCEL/PDF) ---
def deep_fetch_data(uploaded_file):
    try:
        m_type = uploaded_file.type
        # AI ko strictly instruct karna ki blank response na de
        prompt = """
        IMPORTANT: EXTRACT ALL TRANSACTIONS. 
        Format as CSV ONLY with these exact columns: Date, Narration, Bank_Account, Type, Amount.
        - Date: DD/MM/YYYY
        - Narration: Original transaction name.
        - Type: Must be 'Debit' or 'Credit'.
        - Amount: Clean numbers only.
        If it's an Excel or PDF, read every row. Do not return empty.
        """
        response = model.generate_content([prompt, {"mime_type": m_type, "data": uploaded_file.getvalue()}])
        return response.text
    except Exception as e:
        return f"Error reading file: {str(e)}"

# --- 3. UI ---
st.title("🚀 Accounter-AI: High Precision Mode")
st.markdown("### Vision: AI Scan → Auditor Review → Financial Reports")

uploaded_files = st.file_uploader(
    "Upload Statements (PDF, Excel, Images)", 
    type=['pdf', 'xlsx', 'xls', 'csv', 'png', 'jpg'],
    accept_multiple_files=True
)

if uploaded_files:
    if 'audit_df' not in st.session_state:
        if st.button("📊 START DEEP CALCULATION", type="primary"):
            with st.spinner("AI entries fetch kar raha hai..."):
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    results = list(executor.map(deep_fetch_data, uploaded_files))
                
                # Combine results logic
                combined_csv = "Date,Narration,Bank_Account,Type,Amount\n"
                for res in results:
                    if "Date" in res:
                        # Sirf CSV wala part nikaalna
                        clean_part = res.split("Date")[-1].replace("```csv", "").replace("```", "").strip()
                        combined_csv += clean_part + "\n"
                
                try:
                    df = pd.read_csv(io.StringIO(combined_csv), on_bad_lines='skip')
                    df.columns = df.columns.str.strip()
                    
                    # Amount cleaning formula (Zero/Blank Fix)
                    df['Amount'] = pd.to_numeric(df['Amount'].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
                    df = df[df['Amount'] > 0]
                    
                    if df.empty:
                        st.error("AI ne koi entry fetch nahi ki. Kripya file check karein.")
                    else:
                        df['Ledger'] = "Suspense A/c"
                        df['Voucher'] = df['Type'].apply(lambda x: 'Payment (F5)' if 'Debit' in str(x) else 'Receipt (F6)')
                        st.session_state['audit_df'] = df
                        st.rerun()
                except Exception as e:
                    st.error(f"Processing Error: {e}")
                    st.text("Raw Data received: " + combined_csv)

    # --- PHASE 2: MANUAL EDIT (AUDITOR VIEW) ---
    if 'audit_df' in st.session_state:
        st.subheader("📝 Phase 2: Auditor Verification")
        
        final_df = st.data_editor(
            st.session_state['audit_df'],
            column_config={
                "Narration": st.column_config.TextColumn("Original Narration", width="large"),
                "Ledger": st.column_config.TextColumn("Ledger Account"),
                "Voucher": st.column_config.SelectboxColumn("Voucher", options=["Payment (F5)", "Receipt (F6)", "Contra (F4)", "Journal (F7)"]),
                "Amount": st.column_config.NumberColumn("Amount", format="₹%.2f")
            },
            num_rows="dynamic",
            use_container_width=True
        )

        if st.button("📈 Phase 3: Finalize Financial Report"):
            st.divider()
            dr = final_df[final_df['Type'].str.contains('Debit', na=False)]['Amount'].sum()
            cr = final_df[final_df['Type'].str.contains('Credit', na=False)]['Amount'].sum()
            
            st.header("⚖️ Accounting Summary")
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Expenses", f"₹{dr:,.2f}")
            c2.metric("Total Income", f"₹{cr:,.2f}")
            c3.metric("Net Flow", f"₹{cr - dr:,.2f}")
            
            st.subheader("Trial Balance")
            st.table(final_df.groupby('Ledger')['Amount'].sum())

# --- FOOTER ---
st.divider()
st.markdown("<div style='text-align: center; color: grey;'>© 2026 | <b>All Rights Reserved by Shehzaad Kutchi Memon</b></div>", unsafe_allow_html=True)
            
