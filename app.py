import streamlit as st
import pandas as pd
import google.generativeai as genai
import io

st.set_page_config(page_title="Accounter-AI | Tally Edition", layout="wide")

# Standard Accounting Categories
STANDARD_LEDGERS = ["Suspense A/c", "Sales", "Purchase", "Food Exp", "Rent", "Salary", "Electricity", "Conveyance"]
VOUCHERS = ["Payment (F5)", "Receipt (F6)", "Contra (F4)", "Journal (F7)"]

if 'api_key' in st.session_state:
    genai.configure(api_key=st.session_state['api_key'], transport='rest')
    model = genai.GenerativeModel('gemini-1.5-flash')

st.title("📂 Accounter-AI: Enterprise Audit System")

uploaded_file = st.file_uploader("Upload Bank/Credit Card Statement", type=['pdf'])

if uploaded_file:
    if 'audit_df' not in st.session_state:
        if st.button("🔍 Step 1: Scan & Extract Transactions"):
            with st.spinner("AI is reading Date, Bank, and Card details..."):
                # Detailed Prompt for Bank & Last 4 Digits
                prompt = """
                Extract transactions into CSV format. 
                Columns: Date, Transaction_Details, Bank_Name, Last_4_Digits, Type (Debit/Credit), Amount.
                - Bank_Name: Name of bank or Credit Card (e.g. SBI, HDFC).
                - Last_4_Digits: Last 4 digits of the account/card used.
                - Date: Transaction date.
                Return CSV only.
                """
                res = model.generate_content([prompt, {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}])
                
                # Cleaning & Loading
                csv_data = res.text.split("Date")[-1]
                df = pd.read_csv(io.StringIO("Date" + csv_data))
                df.columns = df.columns.str.strip()
                df['Amount'] = pd.to_numeric(df['Amount'].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
                
                # Adding Ledger and Voucher for Manual Edit
                df['Ledger'] = "Suspense A/c"
                df['Voucher'] = df['Type'].apply(lambda x: 'Payment (F5)' if 'Debit' in str(x) else 'Receipt (F6)')
                
                st.session_state['audit_df'] = df
                st.rerun()

    if 'audit_df' in st.session_state:
        st.subheader("📝 Step 2: Review Transactions (Manual Edit)")
        st.write("Aap niche table mein Date, Bank Name, ya Ledger manually change kar sakte hain:")

        # Tally-style Editable Grid
        final_df = st.data_editor(
            st.session_state['audit_df'],
            column_config={
                "Date": st.column_config.TextColumn("Date"),
                "Bank_Name": st.column_config.TextColumn("Bank/Card"),
                "Last_4_Digits": st.column_config.TextColumn("Last 4 Digits"),
                "Ledger": st.column_config.SelectboxColumn("Ledger", options=STANDARD_LEDGERS),
                "Voucher": st.column_config.SelectboxColumn("Voucher", options=VOUCHERS),
                "Amount": st.column_config.NumberColumn("Amount", format="₹%.2f")
            },
            num_rows="dynamic",
            use_container_width=True
        )

        if st.button("📊 Step 3: Finalize & Generate Financial Report", type="primary"):
            st.divider()
            st.header("⚖️ Financial Summary")
            
            dr = final_df[final_df['Type'].str.contains('Debit', na=False)]['Amount'].sum()
            cr = final_df[final_df['Type'].str.contains('Credit', na=False)]['Amount'].sum()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Expenses", f"₹{dr:,.2f}")
            c2.metric("Total Income", f"₹{cr:,.2f}")
            c3.metric("Net Flow", f"₹{cr - dr:,.2f}")

            st.subheader("Trial Balance (Ledger-wise)")
            st.table(final_df.groupby('Ledger')['Amount'].sum())
            
