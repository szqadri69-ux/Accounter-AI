import streamlit as st
import pandas as pd
import pdfplumber
import io
from datetime import datetime

# --- 1. SYSTEM CONFIGURATION & BRANDING ---
st.set_page_config(
    page_title="Accounter-AI | Professional Financial Suite",
    page_icon="💼",
    layout="wide"
)

def apply_branding():
    st.markdown(
        """
        <div style='text-align: center; padding: 20px; border-radius: 12px; background-color: #f8f9fa; border-top: 5px solid #004aad; margin-top: 50px;'>
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

# --- 2. ADVANCED DATA EXTRACTION ENGINE ---
def extract_financial_data(files):
    all_dfs = []
    for f in files:
        try:
            df_temp = None
            f_type = f.name.lower().split('.')[-1]
            
            if f_type == 'pdf':
                with pdfplumber.open(f) as pdf:
                    pages_data = []
                    for page in pdf.pages:
                        # Professional Table Extraction Strategies
                        table = page.extract_table({
                            "vertical_strategy": "lines", 
                            "horizontal_strategy": "lines"
                        }) or page.extract_table()
                        
                        if table:
                            headers = [str(c).replace('\n', ' ').strip() for c in table[0]]
                            rows = [[str(cell).replace('\n', ' ').strip() if cell else "" for cell in row] for row in table[1:]]
                            pages_data.append(pd.DataFrame(rows, columns=headers))
                    
                    if pages_data:
                        df_temp = pd.concat(pages_data, axis=0, ignore_index=True)
            
            elif f_type in ['xls', 'xlsx']:
                df_temp = pd.read_excel(f)
            elif f_type == 'csv':
                df_temp = pd.read_csv(f)
            
            if df_temp is not None:
                df_temp.columns = [str(c).strip() for c in df_temp.columns]
                all_dfs.append(df_temp)
        except Exception as e:
            st.error(f"Error in {f.name}: {str(e)}")
    
    return pd.concat(all_dfs, ignore_index=True, sort=False) if all_dfs else None

# --- 3. MAIN INTERFACE ---
st.title("💼 Accounter-AI: Professional Auditor")
st.markdown("---")

# Session State Initialization
if 'ledgers' not in st.session_state:
    st.session_state['ledgers'] = ["Sales", "Purchase", "Rent", "Salary", "GST", "TDS", "Suspense A/c"]

if 'audit_df' not in st.session_state:
    st.session_state['audit_df'] = None

# Step 1: Upload
st.subheader("📂 Document Acquisition")
uploaded_files = st.file_uploader("Upload Statements", type=['pdf', 'xlsx', 'xls', 'csv'], accept_multiple_files=True)

if uploaded_files:
    if st.session_state['audit_df'] is None:
        if st.button("🚀 INITIATE SCAN", type="primary"):
            data = extract_financial_data(uploaded_files)
            if data is not None and not data.empty:
                data['Target Ledger'] = "Suspense A/c"
                data['Transaction Type'] = "Expense"
                data['Verified Amount'] = 0.0
                st.session_state['audit_df'] = data
                st.rerun()

# Step 2: Verification Grid & Footer Controls
if st.session_state['audit_df'] is not None:
    st.divider()
    st.subheader("📝 Audit Verification")
    
    # Professional Data Editor
    verified_data = st.data_editor(
        st.session_state['audit_df'],
        column_config={
            "Target Ledger": st.column_config.SelectboxColumn("Account Head", options=st.session_state['ledgers'], required=True),
            "Transaction Type": st.column_config.SelectboxColumn("Category", options=["Income", "Expense", "Transfer"]),
            "Verified Amount": st.column_config.NumberColumn("Final Value", format="₹%.2f")
        },
        use_container_width=True,
        num_rows="dynamic",
        key="main_editor"
    )

    # --- ROW CONTROLLER / LEDGER ADD (Exactly under the table) ---
    with st.container():
        c1, c2, c3 = st.columns([1, 1.5, 1])
        with c2:
            # Table ke niche ledger add karne ka simple integrated option
            new_ledger = st.text_input("Add New Ledger to Selection:", placeholder="Type ledger name here...", label_visibility="collapsed")
            if st.button("➕ Register New Ledger", use_container_width=True):
                if new_ledger and new_ledger not in st.session_state['ledgers']:
                    # Sync current table edits before refresh
                    if 'main_editor' in st.session_state and st.session_state['main_editor']:
                        edits = st.session_state['main_editor'].get('edited_rows', {})
                        for idx, changes in edits.items():
                            for col, val in changes.items():
                                st.session_state['audit_df'].at[int(idx), col] = val
                    
                    st.session_state['ledgers'].append(new_ledger)
                    st.toast(f"Ledger '{new_ledger}' added!")
                    st.rerun()

    # Step 3: Reporting
    if st.button("📊 GENERATE FINAL REPORT", type="primary", use_container_width=True):
        st.session_state['audit_df'] = verified_data
        
        income = pd.to_numeric(verified_data[verified_data['Transaction Type'] == "Income"]['Verified Amount']).sum()
        expense = pd.to_numeric(verified_data[verified_data['Transaction Type'] == "Expense"]['Verified Amount']).sum()
        
        st.markdown("### Executive Summary")
        m1, m2, m3 = st.columns(3)
        m1.metric("Gross Revenue", f"₹{income:,.2f}")
        m2.metric("Operating Expense", f"₹{expense:,.2f}")
        m3.metric("Net Position", f"₹{income - expense:,.2f}")

        csv = verified_data.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Audit Report (CSV)", csv, "Report.csv", use_container_width=True)

with st.sidebar:
    st.header("⚙️ Settings")
    if st.button("Reset Session", use_container_width=True):
        st.session_state.clear()
        st.rerun()

apply_branding()
