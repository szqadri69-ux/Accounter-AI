import streamlit as st
import pandas as pd
import pdfplumber
import io

# --- 1. SETTINGS & BRANDING (SHEHZAAD KUTCHI MEMON) ---
st.set_page_config(
    page_title="Accounter-AI | Shehzaad Kutchi Memon", 
    layout="wide"
)

def apply_branding():
    """Professional Footer with All Rights Reserved Branding"""
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style='text-align: center; padding: 25px; border-radius: 15px; background-color: #f8f9fa; border-top: 4px solid #007bff;'>
            <p style='margin: 0; font-size: 1.3em; color: #2c3e50; font-family: sans-serif;'>
                © 2026 | <b>All Rights Reserved by Shehzaad Kutchi Memon</b>
            </p>
            <p style='font-size: 0.9em; color: #6c757d; margin-top: 8px;'>
                Professional Enterprise Auditing System | 100% Secure Offline Logic Engine
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )

# --- 2. LOGIC-BASED DATA PARSER (NO AI) ---

def extract_financial_data(files):
    """Bina internet ke files se data nikalne ka logic"""
    all_dataframes = []
    status = st.empty()
    progress = st.progress(0)
    
    for idx, f in enumerate(files):
        try:
            status.text(f"Scanning: {f.name}...")
            if f.name.lower().endswith('.pdf'):
                with pdfplumber.open(f) as pdf:
                    for i, page in enumerate(pdf.pages):
                        table = page.extract_table()
                        if table:
                            df = pd.DataFrame(table[1:], columns=table[0])
                            all_dataframes.append(df)
            elif f.name.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(f)
                all_dataframes.append(df)
            elif f.name.lower().endswith('.csv'):
                df = pd.read_csv(f)
                all_dataframes.append(df)
            
            progress.progress((idx + 1) / len(files))
        except Exception as e:
            st.error(f"Error reading {f.name}: {str(e)}")
            
    status.text("Processing Complete!")
    return pd.concat(all_dataframes, ignore_index=True) if all_dataframes else None

# --- 3. PROFESSIONAL INTERFACE ---

st.title("🚀 Accounter-AI: Enterprise Auditor")
st.markdown("<h3 style='color: #2c3e50;'>All Rights Reserved by Shehzaad Kutchi Memon</h3>", unsafe_allow_html=True)
st.write("System Mode: **Professional Offline Logic (No AI Dependency)**")

# Sidebar
with st.sidebar:
    st.header("Software Control")
    st.info("Status: Local Processing Enabled")
    st.write("**Owner:** Shehzaad Kutchi Memon")
    st.write("**Engine:** High-Volume Parser")
    st.divider()
    st.write("© 2026 | All Rights Reserved")

# File Upload Section
uploaded_files = st.file_uploader(
    "Upload Financial Statements (PDF, Excel, CSV)", 
    type=['pdf', 'xlsx', 'xls', 'csv'], 
    accept_multiple_files=True
)

if uploaded_files:
    if 'master_data' not in st.session_state:
        if st.button("📊 INITIATE AUDIT SCAN", type="primary"):
            data = extract_financial_data(uploaded_files)
            if data is not None:
                # Adding default Tally-style columns
                data['Ledger_Account'] = "Suspense A/c"
                data['Voucher_Type'] = "Journal"
                st.session_state['master_data'] = data
                st.rerun()

    # Phase 2: Auditor Recheck Mode
    if 'master_data' in st.session_state:
        st.divider()
        st.subheader("📝 Phase 2: Auditor Verification (Tally Mode)")
        st.info(f"Extracted {len(st.session_state['master_data'])} rows from files. Assign Ledgers below:")
        
        # Professional Grid Editor
        edited_df = st.data_editor(
            st.session_state['master_data'],
            column_config={
                "Ledger_Account": st.column_config.SelectboxColumn(
                    "Assign Ledger",
                    options=["Cash", "Bank", "Salary", "Purchase", "Sales", "GST", "Rent", "Suspense A/c"],
                    required=True
                ),
                "Voucher_Type": st.column_config.SelectboxColumn(
                    "Voucher",
                    options=["Payment (F5)", "Receipt (F6)", "Contra (F4)", "Journal (F7)"]
                )
            },
            num_rows="dynamic",
            use_container_width=True
        )

        # Export Report
        if st.button("📈 GENERATE FINAL FINANCIAL REPORT", type="primary"):
            st.success("Analysis Complete!")
            
            # Export to Excel
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                edited_df.to_excel(writer, index=False, sheet_name='Verified_Audit')
            
            st.download_button(
                label="📥 Download Tally-Ready Excel",
                data=buf.getvalue(),
                file_name="Audit_Report_Shehzaad.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

apply_branding()
