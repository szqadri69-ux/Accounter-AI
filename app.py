import streamlit as st
import pandas as pd
import pdfplumber
import io

# --- 1. SYSTEM CONFIGURATION & BRANDING ---
st.set_page_config(
    page_title="Accounter-AI | Professional Financial Suite",
    page_icon="💼",
    layout="wide"
)

def apply_branding():
    st.markdown(
        """
        <div style='text-align: center; padding: 25px; border-radius: 12px; background-color: #f8f9fa; border-top: 5px solid #004aad; margin-top: 60px;'>
            <p style='margin: 0; font-size: 1.1em; color: #1c1c1c; font-weight: 500;'>
                © 2026 | <b>Accounter-AI Enterprise</b>
            </p>
            <p style='margin: 0; font-size: 0.9em; color: #666;'>
                Proprietor: Shehzaad Kutchi Memon
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )

# --- 2. DATA EXTRACTION ENGINE ---
def extract_financial_data(files):
    """
    Extracted data from multiple formats (PDF, Excel, CSV)
    """
    all_dfs = []
    for f in files:
        try:
            df_temp = None
            if f.name.lower().endswith('.pdf'):
                with pdfplumber.open(f) as pdf:
                    pages_data = []
                    for page in pdf.pages:
                        table = page.extract_table()
                        if table:
                            # Clean headers and rows
                            headers = [str(c).strip() for c in table[0]]
                            rows = table[1:]
                            pages_data.append(pd.DataFrame(rows, columns=headers))
                    if pages_data:
                        df_temp = pd.concat(pages_data, axis=0, ignore_index=True)
            elif f.name.lower().endswith(('.xls', '.xlsx')):
                df_temp = pd.read_excel(f)
            elif f.name.lower().endswith('.csv'):
                df_temp = pd.read_csv(f)
            
            if df_temp is not None:
                all_dfs.append(df_temp)
        except Exception as e:
            st.error(f"Error processing {f.name}: {str(e)}")
    
    return pd.concat(all_dfs, ignore_index=True) if all_dfs else None

# --- 3. CORE APPLICATION INTERFACE ---
st.title("💼 Accounter-AI: Professional Financial Auditor")
st.markdown("---")

# Initialize Session State
if 'ledgers' not in st.session_state:
    st.session_state['ledgers'] = ["Sales", "Purchase", "Rent", "Salary", "GST", "TDS", "Suspense A/c"]

if 'audit_df' not in st.session_state:
    st.session_state['audit_df'] = None

# Sidebar: Ledger & System Controls
with st.sidebar:
    st.header("⚙️ System Controls")
    with st.expander("Ledger Management", expanded=False):
        new_ledger = st.text_input("Add New Ledger:")
        if st.button("Register Ledger", use_container_width=True):
            if new_ledger and new_ledger not in st.session_state['ledgers']:
                # Sync current edits before refresh
                if 'main_editor' in st.session_state and st.session_state['main_editor']:
                    edits = st.session_state['main_editor'].get('edited_rows', {})
                    for idx, changes in edits.items():
                        for col, val in changes.items():
                            st.session_state['audit_df'].at[int(idx), col] = val
                
                st.session_state['ledgers'].append(new_ledger)
                st.toast(f"Ledger '{new_ledger}' registered.")
                st.rerun()
    
    st.divider()
    if st.button("Reset Session", type="secondary", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# Step 1: Document Acquisition
st.subheader("📂 Document Acquisition")
uploaded_files = st.file_uploader(
    "Upload Financial Statements (PDF, XLSX, CSV)", 
    type=['pdf', 'xlsx', 'xls', 'csv'], 
    accept_multiple_files=True
)

if uploaded_files:
    if st.session_state['audit_df'] is None:
        if st.button("🚀 INITIATE DATA EXTRACTION", type="primary"):
            with st.spinner("Extracting transactional data..."):
                data = extract_financial_data(uploaded_files)
                if data is not None:
                    # Append Professional Audit Columns
                    data['Target Ledger'] = "Suspense A/c"
                    data['Transaction Type'] = "Expense"
                    data['Verified Amount'] = 0.0
                    st.session_state['audit_df'] = data
                    st.rerun()

# Step 2: Professional Verification Grid
if st.session_state['audit_df'] is not None:
    st.divider()
    st.subheader("📝 Financial Verification & Audit")
    
    # Audit Grid Configuration
    verified_data = st.data_editor(
        st.session_state['audit_df'],
        column_config={
            "Target Ledger": st.column_config.SelectboxColumn(
                "Account Head", 
                options=st.session_state['ledgers'], 
                required=True
            ),
            "Transaction Type": st.column_config.SelectboxColumn(
                "Category", 
                options=["Income", "Expense", "Transfer"]
            ),
            "Verified Amount": st.column_config.NumberColumn(
                "Final Value (INR)", 
                format="₹%.2f",
                min_value=0
            )
        },
        use_container_width=True,
        num_rows="dynamic",
        key="main_editor"
    )

    # Step 3: Reporting & Analytics
    if st.button("📊 GENERATE CONSOLIDATED REPORT", type="primary", use_container_width=True):
        st.session_state['audit_df'] = verified_data
        
        # Calculate Analytics
        income = pd.to_numeric(verified_data[verified_data['Transaction Type'] == "Income"]['Verified Amount']).sum()
        expense = pd.to_numeric(verified_data[verified_data['Transaction Type'] == "Expense"]['Verified Amount']).sum()
        net_position = income - expense
        
        st.markdown("### Executive Summary")
        m1, m2, m3 = st.columns(3)
        m1.metric("Gross Revenue", f"₹{income:,.2f}")
        m2.metric("Total Operating Expense", f"₹{expense:,.2f}")
        m3.metric("Net Financial Position", f"₹{net_position:,.2f}", delta=float(net_position))

        # Secure Export
        st.divider()
        csv_report = verified_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Verified Audit Report (CSV)", 
            data=csv_report, 
            file_name=f"Audit_Report_{datetime.now().strftime('%Y%m%d')}.csv", 
            use_container_width=True
        )

apply_branding()
