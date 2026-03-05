import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
import concurrent.futures

# --- 1. CONFIG & BRANDING ---
st.set_page_config(page_title="Accounter-AI | Shehzaad Kutchi Memon", layout="wide")

# --- 2. SECURE LOGIN ---
if 'api_key' not in st.session_state:
    st.title("🔐 Accounter-AI Secure Login")
    api_key_input = st.text_input("Enter Gemini API Key:", type="password")
    if st.button("Login"):
        st.session_state['api_key'] = api_key_input
        st.rerun()
    st.stop()

# Configure with 'transport=rest' for stability
genai.configure(api_key=st.session_state['api_key'], transport='rest')
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. POWERFUL EXTRACTION FUNCTION (Multimodal) ---
def extract_transactions(uploaded_file):
    try:
        mime_type = uploaded_file.type
        prompt = """
        ACT AS A PROFESSIONAL AUDITOR. 
        Extract EVERY transaction. 
        Format as CSV ONLY with: Date, Original_Narration, Bank_Detail, Type (Debit/Credit), Amount.
        Keep 'Original_Narration' EXACTLY as in document.
        'Bank_Detail' should show Bank Name and Last 4 digits.
        Clean 'Amount' - Numbers only, remove symbols.
        """
        response = model.generate_content([prompt, {"mime_type": mime_type, "data": uploaded_file.getvalue()}])
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# --- 4. UI ---
st.title("🚀 Accounter-AI: High Precision Mode")
st.info("Vision: AI Scan → Auditor Review → Financial Reports")

# Multiple File Upload Support (PDF, Excel, Word, Images, CSV, Text)
uploaded_files = st.file_uploader(
    "Upload Statements (Any Format)", 
    type=['pdf', 'xlsx', 'xls', 'csv', 'txt', 'png', 'jpg', 'doc', 'docx'],
    accept_multiple_files=True
)

if uploaded_files:
    # Phase 1: AI Reading
    if 'audit_df' not in st.session_state:
        if st.button("📊 START DEEP CALCULATION", type="primary"):
            with st.spinner(f"AI is reading {len(uploaded_files)} files... Please wait."):
                
                # Using ThreadPool for faster processing of multiple files
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    results = list(executor.map(extract_transactions, uploaded_files))
                
                combined_csv = "Date,Original_Narration,Bank_Detail,Type,Amount\n" + "\n".join([r.split("Date")[-1] for r in results if "Date" in r])
                
                try:
                    df = pd.read_csv(io.StringIO(combined_csv), on_bad_lines='skip')
                    df.columns = df.columns.str.strip()
                    # Clean Amount Formula
                    df['Amount'] = pd.to_numeric(df['Amount'].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
                    
                    # Tally Style Columns for Manual Review
                    df['Ledger_Account'] = "Suspense A/c"
                    df['Voucher_Type'] = df['Type'].apply(lambda x: 'Payment (F5)' if 'Debit' in str(x) else 'Receipt (F6)')
                    
                    st.session_state['audit_df'] = df
                    st.rerun()
                except Exception as e:
                    st.error(f"Formatting error: {e}")
                    st.text(combined_csv)

    # Phase 2: Manual Auditor Review
    if 'audit_df' in st.session_state:
        st.subheader("📝 Phase 2: Auditor Verification (Edit & Recheck)")
        st.write("Original Narrations dekh kar entries finalize karein:")
        
        # Tally/Kuber Style Editable Grid
        final_df = st.data_editor(
            st.session_state['audit_df'],
            column_config={
                "Original_Narration": st.column_config.TextColumn("Narration (Original)", width="large"),
                "Bank_Detail": st.column_config.TextColumn("Bank/Card Info"),
                "Ledger_Account": st.column_config.TextColumn("Target Ledger (Manual Edit)"),
                "Voucher_Type": st.column_config.SelectboxColumn("Voucher", options=["Payment (F5)", "Receipt (F6)", "Contra (F4)", "Journal (F7)"]),
                "Amount": st.column_config.NumberColumn("Amount", format="₹%.2f")
            },
            num_rows="dynamic",
            use_container_width=True
        )

        # Phase 3: Final Reports
        if st.button("📈 Phase 3: Generate Final Financial Report", type="primary"):
            st.divider()
            dr = final_df[final_df['Type'].str.contains('Debit', na=False)]['Amount'].sum()
            cr = final_df[final_df['Type'].str.contains('Credit', na=False)]['Amount'].sum()
            
            st.header("⚖️ Final Accounting Summary")
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Expenses (Dr)", f"₹{dr:,.2f}")
            c2.metric("Total Income (Cr)", f"₹{cr:,.2f}")
            c3.metric("Net Flow (P&L)", f"₹{cr - dr:,.2f}")

            # Trial Balance Table
            st.subheader("Final Trial Balance (Ledger-wise)")
            trial = final_df.groupby('Ledger_Account')['Amount'].sum().reset_index()
            st.table(trial)
            
            # Download Button
            buf = io.BytesIO()
            final_df.to_excel(buf, index=False)
            st.download_button("📥 Download Verified Excel", data=buf.getvalue(), file_name="Verified_Audit_Report.xlsx")

# --- FOOTER & BRANDING ---
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: grey;'>
        <p>© 2026 | <b>All Rights Reserved by Shehzaad Kutchi Memon</b></p>
    </div>
    """, 
    unsafe_allow_html=True
)
