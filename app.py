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
                        df_temp = pd.concat(pages_data, axis=0, ignore_index=True, sort=False)
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
st.title("🚀 Accounter-AI: Professional Financial Suite")
st.markdown("### Owner: Shehzaad Kutchi Memon")

# Ledger state initialization
if 'ledgers' not in st.session_state:
    st.session_state['ledgers'] = ["Cash", "Bank", "Sales", "Purchase", "Rent Income", "Salary Expense", "GST Income", "Other Income", "Suspense A/c"]

# Software Control Sidebar
with st.sidebar:
    st.header("Software Control")
    st.success("Status: Local Processing Enabled")
    st.info("Engine: High-Volume Parser v2.5")
    if st.button("🔄 Reset All Data"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Step 1: Upload
uploaded_files = st.file_uploader("Upload Bank Statements (HDFC, Paytm, SBI, etc.)", type=['pdf', 'xlsx', 'xls', 'csv'], accept_multiple_files=True)

if uploaded_files:
    if 'raw_audit_data' not in st.session_state:
        if st.button("🔍 Step 1: Scan & Fetch Entries", type="primary"):
            data = extract_data(uploaded_files)
            if data is not None:
                # Add columns if missing
                if 'Account_Head' not in data.columns: data['Account_Head'] = "Suspense A/c"
                if 'Entry_Type' not in data.columns: data['Entry_Type'] = "Expense"
                if 'Amount' not in data.columns: data['Amount'] = 0.0
                st.session_state['raw_audit_data'] = data
                st.rerun()

if 'raw_audit_data' in st.session_state:
    st.divider()
    
    # NEW: Ledger Management INSIDE main screen to avoid refresh issues
    with st.expander("➕ Add New Ledgers (Manage List)", expanded=False):
        col_l1, col_l2 = st.columns([3, 1])
        new_l_name = col_l1.text_input("Enter New Ledger Name:", key="new_l_input")
        if col_l2.button("Add Ledger", use_container_width=True):
            if new_l_name and new_l_name not in st.session_state['ledgers']:
                st.session_state['ledgers'].append(new_l_name)
                st.toast(f"Ledger '{new_l_name}' added successfully!")
                st.rerun()
        st.write("**Current Ledgers:** " + ", ".join(st.session_state['ledgers']))

    st.subheader("📝 Step 2: Auditor Verification (Edit & Recheck)")
    
    # Editable Grid
    # We use a key that includes the length of ledgers so it updates when a ledger is added
    grid_key = f"audit_grid_{len(st.session_state['ledgers'])}"
    
    edited_df = st.data_editor(
        st.session_state['raw_audit_data'],
        column_config={
            "Account_Head": st.column_config.SelectboxColumn(
                "Select Ledger",
                options=st.session_state['ledgers'],
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
        use_container_width=True,
        key=grid_key
    )

    # Step 3: Financial Report
    if st.button("📊 Step 3: Generate Financial Profit & Loss Report", type="primary"):
        try:
            # Save the edits back to session state to prevent loss
            st.session_state['raw_audit_data'] = edited_df
            
            df = edited_df.copy()
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
            
            income = df[df['Entry_Type'] == "Income"]['Amount'].sum()
            expense = df[df['Entry_Type'] == "Expense"]['Amount'].sum()
            profit = income - expense
            
            st.divider()
            st.header("📊 Profit & Loss Summary")
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Income", f"₹{income:,.2f}")
            c2.metric("Total Expense", f"₹{expense:,.2f}")
            c3.metric("Net Profit/Loss", f"₹{profit:,.2f}", delta=float(profit))

            # Table Breakdown
            st.subheader("Ledger Summary")
            breakdown = df.groupby(['Account_Head', 'Entry_Type'])['Amount'].sum().reset_index()
            st.table(breakdown)

            # Export Buttons
            st.subheader("📥 Export Financial Documents")
            ec1, ec2 = st.columns(2)
            
            with ec1:
                output_ex = io.BytesIO()
                with pd.ExcelWriter(output_ex, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='All_Entries')
                    breakdown.to_excel(writer, index=False, sheet_name='PL_Summary')
                st.download_button("📥 Download Excel Report", output_ex.getvalue(), "Financial_Report.xlsx")

            with ec2:
                pdf_output = create_pdf_report(income, expense, profit, breakdown)
                st.download_button("📥 Download PDF Report", pdf_output, "Financial_Report.pdf", "application/pdf")
                
        except Exception as e:
            st.error(f"Error generating report: {e}")

apply_branding()
