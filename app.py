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
                df_temp = pd.read_excel(f)
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
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(190, 10, txt="FINANCIAL PROFIT & LOSS REPORT", ln=True, align='C')
    pdf.set_font("Helvetica", '', 12)
    pdf.cell(190, 10, txt=f"Owner: Shehzaad Kutchi Memon", ln=True, align='C')
    pdf.cell(190, 10, txt=f"Date: {datetime.now().strftime('%d-%m-%Y')}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(95, 10, "Description", 1, 0, 'L', True)
    pdf.cell(95, 10, "Amount (INR)", 1, 1, 'L', True)
    
    pdf.set_font("Helvetica", '', 12)
    pdf.cell(95, 10, "Total Income", 1)
    pdf.cell(95, 10, f"{income:,.2f}", 1, 1)
    pdf.cell(95, 10, "Total Expense", 1)
    pdf.cell(95, 10, f"{expense:,.2f}", 1, 1)
    
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(95, 10, "Net Profit/Loss", 1)
    pdf.cell(95, 10, f"{profit:,.2f}", 1, 1)
    pdf.ln(10)
    
    pdf.cell(190, 10, txt="Ledger-wise Breakdown:", ln=True)
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(90, 10, "Account Head", 1, 0, 'L', True)
    pdf.cell(50, 10, "Type", 1, 0, 'L', True)
    pdf.cell(50, 10, "Amount", 1, 1, 'L', True)
    
    pdf.set_font("Helvetica", '', 10)
    for _, row in breakdown_df.iterrows():
        pdf.cell(90, 10, str(row['Account_Head']), 1)
        pdf.cell(50, 10, str(row['Entry_Type']), 1)
        pdf.cell(50, 10, f"{row['Amount']:,.2f}", 1, 1)
        
    return pdf.output()

# --- 4. INTERFACE ---
st.title("🚀 Accounter-AI Professional")
st.markdown("##### Owner: Shehzaad Kutchi Memon")

# Session State
if 'ledgers' not in st.session_state:
    st.session_state['ledgers'] = ["Cash", "Bank", "Sales", "Purchase", "Rent Income", "Salary Expense", "GST Income", "Other Income", "Suspense A/c"]

# Sidebar Management
with st.sidebar:
    st.header("Settings")
    new_ledger = st.text_input("New Ledger Name:")
    if st.button("Add to List"):
        if new_ledger and new_ledger not in st.session_state['ledgers']:
            st.session_state['ledgers'].append(new_ledger)
            st.rerun()
    
    st.divider()
    if st.button("🔄 Reset System"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Step 1: Upload
uploaded_files = st.file_uploader("Upload Statements", type=['pdf', 'xlsx', 'xls', 'csv'], accept_multiple_files=True)

if uploaded_files:
    if 'raw_audit_data' not in st.session_state:
        if st.button("START AUDIT SCAN", type="primary", use_container_width=True):
            data = extract_data(uploaded_files)
            if data is not None:
                data['Select Ledger'] = "Suspense A/c"
                data['Income/Expense'] = "Expense"
                data['Amount (Final)'] = 0.0
                st.session_state['raw_audit_data'] = data
                st.rerun()

if 'raw_audit_data' in st.session_state:
    st.divider()
    
    # TABLE TOOLBAR AREA
    t_col1, t_col2 = st.columns([3, 1])
    with t_col1:
        st.subheader("Audit Worksheet")
    with t_col2:
        # Mini ledger manager tucked away near the table top
        quick_add = st.popover("⚙️ Manage Ledgers")
        q_name = quick_add.text_input("New Name:")
        if quick_add.button("Add"):
            if q_name and q_name not in st.session_state['ledgers']:
                st.session_state['ledgers'].append(q_name)
                st.rerun()

    # Editable Grid
    grid_key = f"audit_grid_{len(st.session_state['ledgers'])}"
    
    edited_df = st.data_editor(
        st.session_state['raw_audit_data'],
        column_config={
            "Select Ledger": st.column_config.SelectboxColumn(
                "Ledger",
                options=st.session_state['ledgers'],
                required=True,
                default="Suspense A/c"
            ),
            "Income/Expense": st.column_config.SelectboxColumn(
                "Type",
                options=["Income", "Expense", "Transfer"],
                required=True,
                default="Expense"
            ),
            "Amount (Final)": st.column_config.NumberColumn("Amount", format="₹%.2f", min_value=0)
        },
        num_rows="dynamic",
        use_container_width=True,
        key=grid_key
    )

    # Final Actions
    if st.button("GENERATE FINAL REPORT", type="primary", use_container_width=True):
        st.session_state['raw_audit_data'] = edited_df
        df = edited_df.copy()
        df['Amount (Final)'] = pd.to_numeric(df['Amount (Final)'], errors='coerce').fillna(0)
        
        income = df[df['Income/Expense'] == "Income"]['Amount (Final)'].sum()
        expense = df[df['Income/Expense'] == "Expense"]['Amount (Final)'].sum()
        profit = income - expense
        
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Income", f"₹{income:,.2f}")
        m2.metric("Expense", f"₹{expense:,.2f}")
        m3.metric("P&L", f"₹{profit:,.2f}", delta=float(profit))

        breakdown = df.groupby(['Select Ledger', 'Income/Expense'])['Amount (Final)'].sum().reset_index()
        breakdown.columns = ['Account_Head', 'Entry_Type', 'Amount']
        
        st.subheader("Summary Report")
        st.table(breakdown)

        ec1, ec2 = st.columns(2)
        with ec1:
            output_ex = io.BytesIO()
            with pd.ExcelWriter(output_ex, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Entries')
                breakdown.to_excel(writer, index=False, sheet_name='Summary')
            st.download_button("Excel Export", output_ex.getvalue(), "Report.xlsx")
        with ec2:
            pdf_output = create_pdf_report(income, expense, profit, breakdown)
            st.download_button("PDF Export", pdf_output, "Report.pdf")

apply_branding()
