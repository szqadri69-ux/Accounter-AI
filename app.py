import streamlit as st
import pandas as pd
import pdfplumber
import io
from datetime import datetime
from fpdf import FPDF

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

def make_columns_unique(columns):
    new_cols = []
    col_counts = {}
    for col in columns:
        col_str = str(col).strip() if col else "Unnamed"
        if col_str in col_counts:
            col_counts[col_str] += 1
            new_cols.append(f"{col_str}_{col_counts[col_str]}")
        else:
            col_counts[col_str] = 0
            new_cols.append(col_str)
    return new_cols

# --- 2. DATA EXTRACTION LOGIC ---
def extract_data(files):
    all_dfs = []
    for f in files:
        try:
            df_temp = None
            if f.name.lower().endswith('.pdf'):
                with pdfplumber.open(f) as pdf:
                    pages_data = []
                    for page in pdf.pages:
                        table = page.extract_table({"vertical_strategy": "text", "horizontal_strategy": "text"})
                        if table and len(table) > 1:
                            headers = make_columns_unique([str(c).replace('\n',' ') for c in table[0]])
                            rows = [[str(cell).replace('\n', ' ').strip() if cell else "" for cell in row] for row in table[1:]]
                            p_df = pd.DataFrame(rows, columns=headers)
                            pages_data.append(p_df)
                    if pages_data:
                        df_temp = pd.concat(pages_data, axis=0, ignore_index=True)
            elif f.name.lower().endswith(('.xls', '.xlsx')):
                try:
                    df_temp = pd.read_excel(f, engine='openpyxl')
                except:
                    df_temp = pd.read_excel(f, engine='xlrd')
            elif f.name.lower().endswith('.csv'):
                df_temp = pd.read_csv(f)
            
            if df_temp is not None:
                df_temp.columns = make_columns_unique(df_temp.columns)
                all_dfs.append(df_temp)
        except Exception as e:
            st.error(f"Error reading {f.name}: {e}")
    
    if all_dfs:
        combined = pd.concat(all_dfs, axis=0, ignore_index=True, sort=False)
        return combined.fillna("")
    return None

# --- 3. PDF REPORT GENERATOR ---
def create_pdf_report(income, expense, profit, breakdown_df):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Helvetica", 'B', 16)
    pdf.set_text_color(30, 136, 229)
    pdf.cell(190, 10, txt="FINANCIAL PROFIT & LOSS STATEMENT", ln=True, align='C')
    
    pdf.set_font("Helvetica", '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 7, txt=f"Proprietor: Shehzaad Kutchi Memon", ln=True, align='C')
    pdf.cell(190, 7, txt=f"Report Generated: {datetime.now().strftime('%d-%m-%Y %H:%M')}", ln=True, align='C')
    pdf.ln(10)
    
    # Summary Box (Automatic Calculations)
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(95, 10, "Component", 1, 0, 'C', True)
    pdf.cell(95, 10, "Total Amount (INR)", 1, 1, 'C', True)
    
    pdf.set_font("Helvetica", '', 11)
    pdf.cell(95, 10, "Total Income", 1)
    pdf.cell(95, 10, f"{income:,.2f}", 1, 1, 'R')
    pdf.cell(95, 10, "Total Expenses", 1)
    pdf.cell(95, 10, f"{expense:,.2f}", 1, 1, 'R')
    
    pdf.set_font("Helvetica", 'B', 12)
    if profit >= 0:
        pdf.set_text_color(0, 128, 0)
        label = "NET PROFIT"
    else:
        pdf.set_text_color(255, 0, 0)
        label = "NET LOSS"
        
    pdf.cell(95, 10, label, 1)
    pdf.cell(95, 10, f"{profit:,.2f}", 1, 1, 'R')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    
    # Breakdown Table
    pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(190, 10, txt="Detailed Ledger Breakdown:", ln=True)
    
    pdf.set_fill_color(240, 245, 255)
    pdf.set_font("Helvetica", 'B', 9)
    pdf.cell(80, 8, "Ledger Account", 1, 0, 'L', True)
    pdf.cell(50, 8, "Category", 1, 0, 'C', True)
    pdf.cell(60, 8, "Amount", 1, 1, 'C', True)
    
    pdf.set_font("Helvetica", '', 9)
    for _, row in breakdown_df.iterrows():
        pdf.cell(80, 8, str(row['Account_Head']), 1)
        pdf.cell(50, 8, str(row['Entry_Type']), 1, 0, 'C')
        pdf.cell(60, 8, f"{row['Amount']:,.2f}", 1, 1, 'R')
        
    return pdf.output()

# --- 4. INTERFACE ---
st.title("💼 Accounter-AI Professional")
st.markdown("##### Developed for: Shehzaad Kutchi Memon")

if 'ledgers' not in st.session_state:
    st.session_state['ledgers'] = ["Sales", "Purchase", "Rent", "Salary", "Bank Interest", "Commission", "Electricity", "Suspense A/c"]

# Sidebar settings
with st.sidebar:
    st.header("Ledger Management")
    l_name = st.text_input("New Ledger Name:")
    if st.button("Add Ledger"):
        if l_name and l_name not in st.session_state['ledgers']:
            st.session_state['ledgers'].append(l_name)
            st.rerun()
    st.divider()
    if st.button("Reset All Data"):
        st.session_state.clear()
        st.rerun()

# Step 1: Upload
st.subheader("📁 Step 1: Upload PDF/Excel Data")
files = st.file_uploader("Upload bank statements or accounting files", type=['pdf', 'xlsx', 'xls', 'csv'], accept_multiple_files=True)

if files:
    if 'audit_df' not in st.session_state:
        if st.button("🚀 FETCH & SCAN DATA", type="primary", use_container_width=True):
            data = extract_data(files)
            if data is not None:
                # Default categorizations for the auditor to check
                data['Select Ledger'] = "Suspense A/c"
                data['Entry Type'] = "Expense"
                data['Final Amount'] = 0.0
                st.session_state['audit_df'] = data
                st.rerun()

# Step 2: Categorize Entries
if 'audit_df' in st.session_state:
    st.divider()
    st.subheader("📝 Step 2: Set Ledger & Classification")
    st.caption("Entries verify karein aur Category set karein.")
    
    verified_data = st.data_editor(
        st.session_state['audit_df'],
        column_config={
            "Select Ledger": st.column_config.SelectboxColumn("Ledger Head", options=st.session_state['ledgers'], required=True),
            "Entry Type": st.column_config.SelectboxColumn("Category", options=["Income", "Expense", "Transfer"]),
            "Final Amount": st.column_config.NumberColumn("Confirmed Amount", format="₹%.2f")
        },
        use_container_width=True,
        num_rows="dynamic"
    )

    # Step 3: Result & Automatic Calculation
    if st.button("📊 GENERATE FINAL REPORT", type="primary", use_container_width=True):
        # 1. Automatic Calculation Logic
        st.session_state['audit_df'] = verified_data
        df = verified_data.copy()
        df['Final Amount'] = pd.to_numeric(df['Final Amount'], errors='coerce').fillna(0)
        
        total_income = df[df['Entry Type'] == "Income"]['Final Amount'].sum()
        total_expense = df[df['Entry Type'] == "Expense"]['Final Amount'].sum()
        net_profit = total_income - total_expense
        
        # 2. Display Dashboard
        st.success("Calculations Completed Successfully!")
        st.markdown("### 📈 Professional Profit & Loss Dashboard")
        m1, m2, m3 = st.columns(3)
        m1.metric("Gross Income", f"₹{total_income:,.2f}")
        m2.metric("Total Operating Expenses", f"₹{total_expense:,.2f}")
        m3.metric("Net Profit / Loss", f"₹{net_profit:,.2f}", delta=float(net_profit))

        # 3. Automatic Ledger Grouping
        breakdown = df.groupby(['Select Ledger', 'Entry Type'])['Final Amount'].sum().reset_index()
        breakdown.columns = ['Account_Head', 'Entry_Type', 'Amount']

        st.subheader("Automatic Ledger Summary")
        st.dataframe(breakdown, use_container_width=True)

        # 4. Final Export Options
        st.divider()
        st.subheader("📥 Download Final Report")
        col_ex, col_pdf = st.columns(2)
        
        with col_ex:
            # Automatic Excel Export
            ex_io = io.BytesIO()
            with pd.ExcelWriter(ex_io, engine='xlsxwriter') as writer:
                verified_data.to_excel(writer, index=False, sheet_name='Detailed_Entries')
                breakdown.to_excel(writer, index=False, sheet_name='Summary_Report')
            st.download_button(
                label="📥 Download Excel Report",
                data=ex_io.getvalue(),
                file_name=f"Accounting_Report_{datetime.now().strftime('%d%m%Y')}.xlsx",
                use_container_width=True
            )
            
        with col_pdf:
            # Automatic PDF Generation
            pdf_bytes = create_pdf_report(total_income, total_expense, net_profit, breakdown)
            st.download_button(
                label="📥 Download PDF Statement",
                data=pdf_bytes,
                file_name=f"PL_Statement_{datetime.now().strftime('%d%m%Y')}.pdf",
                use_container_width=True
            )

apply_branding()
