import streamlit as st
import pandas as pd
import google.generativeai as genai
import io

# --- 1. PAGE CONFIG & BRANDING ---
st.set_page_config(page_title="Accounter-AI | Shehzaad Kutchi Memon", layout="wide")

# --- 2. SECURE LOGIN ---
if 'api_key' not in st.session_state:
    st.title("🔐 Accounter-AI Secure Login")
    api_key_input = st.text_input("Enter Gemini API Key:", type="password")
    if st.button("Initialize System"):
        st.session_state['api_key'] = api_key_input
        st.rerun()
    st.stop()

# --- 3. STABLE API CONFIG ---
genai.configure(api_key=st.session_state['api_key'], transport='rest')
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 4. APP INTERFACE ---
st.title("🚀 Accounter-AI: Professional Auditor")
st.markdown("### Vision: AI Scan → Auditor Review → Financial Reports")

uploaded_file = st.file_uploader("Upload Bank Statement (PDF)", type=['pdf'])

if uploaded_file:
    # PHASE 1: EXTRACTION
    if 'audit_df' not in st.session_state:
        if st.button("🔍 Phase 1: Scan & Extract Transactions"):
            with st.spinner("AI Original Data extract kar raha hai..."):
                prompt = """
                Extract ALL transactions as CSV. 
                Columns: Date, Original_Narration, Your_Account, Type, Amount.
                - Keep 'Original_Narration' EXACTLY as in PDF.
                - 'Your_Account' should show Bank Name and Last 4 digits.
                Return CSV only.
                """
                res = model.generate_content([prompt, {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}])
                
                try:
                    csv_raw = res.text.split("Date")[-1]
                    df = pd.read_csv(io.StringIO("Date" + csv_raw))
                    df.columns = df.columns.str.strip()
                    df['Amount'] = pd.to_numeric(df['Amount'].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
                    
                    # Default Ledger & Voucher for Auditor
                    df['Ledger_Account'] = "Suspense A/c"
                    df['Voucher_Type'] = df['Type'].apply(lambda x: 'Payment (F5)' if 'Debit' in str(x) else 'Receipt (F6)')
                    
                    st.session_state['audit_df'] = df
                    st.rerun()
                except:
                    st.error("Format Error. Please try again.")

    # PHASE 2: AUDITOR REVIEW
    if 'audit_df' in st.session_state:
        st.subheader("📝 Phase 2: Auditor Verification (Manual Edit)")
        
        final_df = st.data_editor(
            st.session_state['audit_df'],
            column_config={
                "Original_Narration": st.column_config.TextColumn("Original Narration", width="large"),
                "Your_Account": st.column_config.TextColumn("Bank / Card Detail"),
                "Ledger_Account": st.column_config.TextColumn("Ledger (Manual Edit)"),
                "Voucher_Type": st.column_config.SelectboxColumn("Voucher", options=["Payment (F5)", "Receipt (F6)", "Contra (F4)", "Journal (F7)"]),
                "Amount": st.column_config.NumberColumn("Amount", format="₹%.2f")
            },
            num_rows="dynamic",
            use_container_width=True
        )

        # PHASE 3: FINANCIALS
        if st.button("📊 Phase 3: Generate Final Financial Report", type="primary"):
            st.divider()
            dr = final_df[final_df['Type'].str.contains('Debit', na=False)]['Amount'].sum()
            cr = final_df[final_df['Type'].str.contains('Credit', na=False)]['Amount'].sum()
            
            st.header("⚖️ Final Audit Summary")
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Debits", f"₹{dr:,.2f}")
            c2.metric("Total Credits", f"₹{cr:,.2f}")
            c3.metric("Net Balance", f"₹{cr - dr:,.2f}")
            
            st.subheader("Ledger-wise Trial Balance")
            st.table(final_df.groupby('Ledger_Account')['Amount'].sum())

# --- 5. FOOTER & BRANDING ---
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: grey;'>
        <p>© 2026 | <b>All Rights Reserved by Shehzaad Kutchi Memon</b></p>
    </div>
    """, 
    unsafe_allow_html=True
)
