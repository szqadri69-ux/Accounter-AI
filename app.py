import streamlit as st
import pandas as pd
import pdfplumber
import io
import re
from datetime import datetime

# --- 1. SETTINGS & BRANDING ---
st.set_page_config(page_title="Accounter-AI | Shehzaad Kutchi Memon", layout="wide")

def apply_branding():
    st.markdown(
        """
        <div style='text-align: center; padding: 20px; border-radius: 10px; background-color: #f1f3f6; border-top: 4px solid #1e88e5; margin-top: 50px;'>
            <p style='margin: 0; font-size: 1.2em; color: #1a237e;'>
                © 2026 | <b>All Rights Reserved by Shehzaad Kutchi Memon</b>
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )

# --- 2. DATA EXTRACTION LOGIC ---
def extract_data(files):
    all_dfs = []
    for f in files:
        try:
            if f.name.lower().endswith('.pdf'):
                with pdfplumber.open(f) as pdf:
                    for page in pdf.pages:
                        table = page.extract_table({"vertical_strategy": "text", "horizontal_strategy": "text"})
                        if table:
                            df = pd.DataFrame(table[1:], columns=[str(c).replace('\n',' ') for c in table[0]])
                            all_dfs.append(df)
            elif f.name.lower().endswith('.xls'):
                all_dfs.append(pd.read_excel(f, engine='xlrd'))
            elif f.name.lower().endswith('.xlsx'):
                all_dfs.append(pd.read_excel(f, engine='openpyxl'))
            else:
                all_dfs.append(pd.read_csv(f))
        except Exception as e:
            st.error(f"Error reading {f.name}: {e}")
    
    if all_dataframes := all_dfs:
        combined = pd.concat(all_dataframes, ignore_index=True, sort=False)
        combined.columns = [str(c).strip() for c in combined.columns]
        return combined.fillna("")
    return None

# --- 3. INTERFACE & WORKFLOW ---
st.title("🚀 Accounter-AI: Professional Financial Suite")
st.markdown("### Owner: Shehzaad Kutchi Memon")

# Sidebar for Ledger Management
with st.sidebar:
    st.header("⚙️ Ledger Settings")
    custom_ledgers = st.text_area("Add Custom Ledgers (Comma Separated)", 
                                 "Cash, Bank, Sales, Purchase, Rent Income, GST Income, Salary Expense, Office Rent, Other Income, Personal")
    ledger_list = [x.strip() for x in custom_ledgers.split(",")]
    
    st.divider()
    st.info("System Mode: Offline Logic Auditor")

uploaded_files = st.file_uploader("Upload Statements (PDF/Excel)", type=['pdf', 'xlsx', 'xls', 'csv'], accept_multiple_files=True)

if uploaded_files:
    if 'raw_audit_data' not in st.session_state:
        if st.button("🔍 Step 1: Scan & Fetch Entries", type="primary"):
            data = extract_data(uploaded_files)
            if data is not None:
                # Standardizing columns for P&L
                data['Account_Head'] = "Suspense A/c"
                data['Entry_Type'] = "Expense" # Default
                if 'Amount' not in data.columns:
                    data['Amount'] = 0.0
                st.session_state['raw_audit_data'] = data
                st.rerun()

if 'raw_audit_data' in st.session_state:
    st.divider()
    st.subheader("📝 Step 2: Auditor Recheck (Tally Style)")
    st.write("Har entry ke liye sahi Account Head select karein:")
    
    # Editable Grid
    edited_df = st.data_editor(
        st.session_state['raw_audit_data'],
        column_config={
            "Account_Head": st.column_config.SelectboxColumn(
                "Select Ledger",
                options=ledger_list + ["Suspense A/c"],
                required=True,
                width="medium"
            ),
            "Entry_Type": st.column_config.SelectboxColumn(
                "Income/Expense",
                options=["Income", "Expense", "Transfer"],
                required=True
            ),
            "Amount": st.column_config.NumberColumn("Amount (Final)", format="₹%.2f")
        },
        num_rows="dynamic",
        use_container_width=True
    )

    # --- 4. PROFIT & LOSS GENERATION ---
    if st.button("📈 Step 3: Generate Financial Report", type="primary"):
        st.session_state['final_verified'] = edited_df
        
        # P&L Calculation Logic
        try:
            df = edited_df.copy()
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
            
            income = df[df['Entry_Type'] == "Income"]['Amount'].sum()
            expense = df[df['Entry_Type'] == "Expense"]['Amount'].sum()
            net_profit = income - expense
            
            st.divider()
            st.header("📊 Profit & Loss Statement")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Income", f"₹{income:,.2f}")
            col2.metric("Total Expense", f"₹{expense:,.2f}")
            col3.metric("Net Profit/Loss", f"₹{net_profit:,.2f}", delta=float(net_profit))

            # Breakdown Table
            st.subheader("Ledger-wise Breakdown")
            breakdown = df.groupby(['Account_Head', 'Entry_Type'])['Amount'].sum().reset_index()
            st.table(breakdown)

            # Export Options
            st.subheader("📥 Export Final Report")
            export_col1, export_col2 = st.columns(2)
            
            # Excel Export
            with export_col1:
                output_excel = io.BytesIO()
                with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='All_Entries')
                    breakdown.to_excel(writer, index=False, sheet_name='Summary_PL')
                
                st.download_button(
                    label="Excel Report Download",
                    data=output_excel.getvalue(),
                    file_name=f"Financial_Report_Shehzaad_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            # CSV/Text Export (Simple PDF alternative for browser-based printing)
            with export_col2:
                report_text = f"FINANCIAL REPORT - SHEHZAAD KUTCHI MEMON\n"
                report_text += f"Date: {datetime.now().strftime('%d-%m-%Y')}\n"
                report_text += "="*40 + "\n"
                report_text += f"Total Income: {income}\n"
                report_text += f"Total Expense: {expense}\n"
                report_text += f"Net Profit: {net_profit}\n"
                report_text += "="*40 + "\n"
                report_text += breakdown.to_string()
                
                st.download_button(
                    label="Text/Print Report Download",
                    data=report_text,
                    file_name="Financial_Summary_Shehzaad.txt",
                    mime="text/plain"
                )
        except Exception as e:
            st.error(f"Report banane mein galti hui: {e}")

apply_branding()
