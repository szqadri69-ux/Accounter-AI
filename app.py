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
    
    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True, sort=False)
        combined.columns = [str(c).strip() for c in combined.columns]
        return combined.fillna("")
    return None

# --- 3. PDF REPORT GENERATOR ---
def create_pdf_report(income, expense, profit, breakdown_df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(200, 10, txt="FINANCIAL PROFIT & LOSS REPORT", ln=True, align='C')
    pdf.set_font("Helvetica", '', 12)
    pdf.cell(200, 10, txt=f"Owner: Shehzaad Kutchi Memon", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%d-%m-%Y')}", ln=True, align='C')
    pdf.ln(10)
    
    # Summary Table
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(60, 10, "Description", 1)
    pdf.cell(60, 10, "Amount (INR)", 1)
    pdf.ln()
    pdf.set_font("Helvetica", '', 12)
    pdf.cell(60, 10, "Total Income", 1)
    pdf.cell(60, 10, f"{income:,.2f}", 1)
    pdf.ln()
    pdf.cell(60, 10, "Total Expense", 1)
    pdf.cell(60, 10, f"{expense:,.2f}", 1)
    pdf.ln()
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(60, 10, "Net Profit/Loss", 1)
    pdf.cell(60, 10, f"{profit:,.2f}", 1)
    pdf.ln(15)
    
    # Breakdown Table
    pdf.cell(200, 10, txt="Ledger-wise Breakdown:", ln=True)
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(70, 10, "Account Head", 1)
    pdf.cell(40, 10, "Type", 1)
    pdf.cell(40, 10, "Amount", 1)
    pdf.ln()
    pdf.set_font("Helvetica", '', 10)
    for index, row in breakdown_df.iterrows():
        pdf.cell(70, 10, str(row['Account_Head']), 1)
        pdf.cell(40, 10, str(row['Entry_Type']), 1)
        pdf.cell(40, 10, f"{row['Amount']:,.2f}", 1)
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1')

# --- 4. INTERFACE ---
st.title("🚀 Accounter-AI: Enterprise Financial Suite")
st.markdown("### Powered by Shehzaad Kutchi Memon")

# Ledger Management in Sidebar
if 'ledgers' not in st.session_state:
    st.session_state['ledgers'] = ["Cash", "Bank", "Sales", "Purchase", "Rent Income", "Salary Expense", "Suspense A/c"]

with st.sidebar:
    st.header("⚙️ Ledger Management")
    new_ledger = st.text_input("Add New Ledger Name:")
    if st.button("➕ Add to List"):
        if new_ledger and new_ledger not in st.session_state['ledgers']:
            st.session_state['ledgers'].append(new_ledger)
            st.success(f"Added: {new_ledger}")
    
    st.divider()
    st.write("**Current Ledgers:**")
    st.write(", ".join(st.session_state['ledgers']))

uploaded_files = st.file_uploader("Upload Statements (PDF/Excel)", type=['pdf', 'xlsx', 'xls', 'csv'], accept_multiple_files=True)

if uploaded_files:
    if 'raw_audit_data' not in st.session_state:
        if st.button("🔍 Step 1: Scan & Fetch Entries", type="primary"):
            data = extract_data(uploaded_files)
            if data is not None:
                data['Account_Head'] = "Suspense A/c"
                data['Entry_Type'] = "Expense"
                if 'Amount' not in data.columns:
                    data['Amount'] = 0.0
                st.session_state['raw_audit_data'] = data
                st.rerun()

if 'raw_audit_data' in st.session_state:
    st.divider()
    st.subheader("📝 Step 2: Auditor Review (Editable Grid)")
    
    # Editable Grid with Dynamic Ledgers
    edited_df = st.data_editor(
        st.session_state['raw_audit_data'],
        column_config={
            "Account_Head": st.column_config.SelectboxColumn(
                "Select Ledger",
                options=st.session_state['ledgers'],
                required=True
            ),
            "Entry_Type": st.column_config.SelectboxColumn(
                "Income/Expense",
                options=["Income", "Expense", "Transfer"],
                required=True
            ),
            "Amount": st.column_config.NumberColumn("Amount", format="₹%.2f")
        },
        num_rows="dynamic",
        use_container_width=True
    )

    # --- 5. FINANCIAL REPORTS ---
    if st.button("📈 Step 3: Generate Final Financial Report", type="primary"):
        try:
            df = edited_df.copy()
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
            
            income = df[df['Entry_Type'] == "Income"]['Amount'].sum()
            expense = df[df['Entry_Type'] == "Expense"]['Amount'].sum()
            profit = income - expense
            
            st.divider()
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Income", f"₹{income:,.2f}")
            col2.metric("Total Expense", f"₹{expense:,.2f}")
            col3.metric("Net Profit", f"₹{profit:,.2f}", delta=float(profit))

            breakdown = df.groupby(['Account_Head', 'Entry_Type'])['Amount'].sum().reset_index()
            st.table(breakdown)

            st.subheader("📥 Download Professional Reports")
            dl_col1, dl_col2 = st.columns(2)
            
            # Excel Download
            with dl_col1:
                output_excel = io.BytesIO()
                with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Audit_Details')
                    breakdown.to_excel(writer, index=False, sheet_name='PL_Summary')
                st.download_button("📥 Download Excel Report", output_excel.getvalue(), "Financial_Audit.xlsx")

            # PDF Download
            with dl_col2:
                pdf_data = create_pdf_report(income, expense, profit, breakdown)
                st.download_button("📥 Download PDF Report", pdf_data, "Financial_Report_Shehzaad.pdf", "application/pdf")
                
        except Exception as e:
            st.error(f"Error: {e}")

apply_branding()
