import streamlit as st
import pandas as pd
import google.generativeai as genai
import io

st.set_page_config(page_title="Accounter-AI | Audit Mode", layout="wide")

# Standard Ledgers for Dropdown (Aap edit kar sakte hain)
LEDGER_LIST = ["Suspense A/c", "Direct Expenses", "Indirect Expenses", "Sales", "Purchase", "Food & Staff", "Conveyance", "Electricity/Bills", "Bank Transfer", "Personal"]

if 'api_key' in st.session_state:
    genai.configure(api_key=st.session_state['api_key'], transport='rest')
    model = genai.GenerativeModel('gemini-1.5-flash')

st.title("📂 Accounter-AI: Auditor Verification System")
st.write("Flow: AI Extract -> Auditor Recheck/Edit -> Final Financials")

uploaded_file = st.file_uploader("Upload PDF Statement", type=['pdf'])

if uploaded_file:
    # --- PHASE 1: EXTRACTION ---
    if 'audit_df' not in st.session_state:
        if st.button("🔍 Phase 1: Scan PDF for Transactions"):
            with st.spinner("Original data extract ho raha hai..."):
                prompt = """
                Extract ALL transactions as CSV. 
                Columns: Date, Original_Narration, Bank_Account, Type, Amount.
                - Keep 'Original_Narration' exactly as written in PDF.
                - 'Bank_Account' should show Bank Name and Last 4 digits (e.g. SBI-43).
                - Amount should be clean numbers.
                Return CSV only.
                """
                res = model.generate_content([prompt, {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}])
                
                try:
                    csv_raw = res.text.split("Date")[-1]
                    df = pd.read_csv(io.StringIO("Date" + csv_raw))
                    df.columns = df.columns.str.strip()
                    df['Amount'] = pd.to_numeric(df['Amount'].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
                    
                    # Default Ledger & Voucher for CA to review
                    df['Target_Ledger'] = "Suspense A/c"
                    df['Voucher_Type'] = df['Type'].apply(lambda x: 'Payment (F5)' if 'Debit' in str(x) else 'Receipt (F6)')
                    
                    st.session_state['audit_df'] = df
                    st.rerun()
                except:
                    st.error("AI Response format error. Please try again.")

    # --- PHASE 2: AUDITOR RECHECK (The Editable Grid) ---
    if 'audit_df' in st.session_state:
        st.subheader("📝 Phase 2: Auditor Review (Edit & Verify)")
        st.info("Aap Original Narration dekh kar sahi Ledger select karein. Galti hone par yahin sudhar lein.")

        # Editable Table like Tally/Kuber
        updated_df = st.data_editor(
            st.session_state['audit_df'],
            column_config={
                "Date": st.column_config.TextColumn("Date"),
                "Original_Narration": st.column_config.TextColumn("Original Narration (Bank Record)", width="large"),
                "Bank_Account": st.column_config.TextColumn("Bank/Card (Ref)"),
                "Target_Ledger": st.column_config.SelectboxColumn("Ledger Name", options=LEDGER_LIST),
                "Voucher_Type": st.column_config.SelectboxColumn("Voucher Type", options=["Payment (F5)", "Receipt (F6)", "Contra (F4)", "Journal (F7)"]),
                "Amount": st.column_config.NumberColumn("Amount", format="₹%.2f")
            },
            num_rows="dynamic",
            use_container_width=True,
            key="audit_grid"
        )

        # --- PHASE 3: FINAL REPORTS ---
        if st.button("📊 Phase 3: Finalize & Generate Financial Report", type="primary", use_container_width=True):
            st.session_state['final_verified_df'] = updated_df
            st.divider()
            
            # P&L and Trial Balance Calculation
            dr = updated_df[updated_df['Type'].str.contains('Debit', na=False)]['Amount'].sum()
            cr = updated_df[updated_df['Type'].str.contains('Credit', na=False)]['Amount'].sum()
            
            st.header("⚖️ Final Audit Summary")
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Expenses (Verified)", f"₹{dr:,.2f}")
            c2.metric("Total Income (Verified)", f"₹{cr:,.2f}")
            c3.metric("Net Surplus/Deficit", f"₹{cr - dr:,.2f}")

            # Trial Balance Table
            st.subheader("Final Trial Balance (Ledger-wise)")
            trial = updated_df.groupby('Target_Ledger')['Amount'].sum().reset_index()
            st.table(trial)
            
            # Export to Excel for Tally Import
            buf = io.BytesIO()
            updated_df.to_excel(buf, index=False)
            st.download_button("📥 Download Verified Audit File", data=buf.getvalue(), file_name="Verified_Audit_Report.xlsx")
            
