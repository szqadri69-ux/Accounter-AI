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

def make_columns_unique(columns):
    """Duplicate column names ko uniquely rename karne ke liye function"""
    new_cols = []
    col_counts = {}
    for col in columns:
        col_str = str(col).strip() if col is not None else "Unnamed"
        if col_str in col_counts:
            col_counts[col_str] += 1
            new_cols.append(f"{col_str}_{col_counts[col_str]}")
        else:
            col_counts[col_str] = 0
            new_cols.append(col_str)
    return new_cols

# --- 2. LOGIC-BASED DATA PARSER (OPTIMIZED FOR HDFC & LARGE PDFS) ---

def extract_financial_data(files):
    """Bina internet ke files se data nikalne ka logic - Improved for Alignment"""
    all_dataframes = []
    status = st.empty()
    progress = st.progress(0)
    
    for idx, f in enumerate(files):
        try:
            status.text(f"Scanning: {f.name}...")
            df_temp = None
            
            if f.name.lower().endswith('.pdf'):
                with pdfplumber.open(f) as pdf:
                    pages_data = []
                    for page in pdf.pages:
                        table = page.extract_table({
                            "vertical_strategy": "lines", 
                            "horizontal_strategy": "lines",
                            "intersection_x_tolerance": 5
                        })
                        if not table:
                            # Try again without strict lines if no table found
                            table = page.extract_table()
                            
                        if table:
                            headers = table[0]
                            # Unique headers handle karein
                            unique_headers = make_columns_unique(headers)
                            p_df = pd.DataFrame(table[1:], columns=unique_headers)
                            # Remove rows that are completely empty
                            p_df = p_df.dropna(how='all')
                            pages_data.append(p_df)
                    
                    if pages_data:
                        df_temp = pd.concat(pages_data, ignore_index=True, sort=False)
            
            elif f.name.lower().endswith(('.xlsx', '.xls')):
                df_temp = pd.read_excel(f)
                df_temp.columns = make_columns_unique(df_temp.columns)
            
            elif f.name.lower().endswith('.csv'):
                df_temp = pd.read_csv(f)
                df_temp.columns = make_columns_unique(df_temp.columns)
            
            if df_temp is not None:
                # Fill missing data and clean strings
                df_temp = df_temp.fillna("")
                all_dataframes.append(df_temp)
            
            progress.progress((idx + 1) / len(files))
        except Exception as e:
            st.error(f"Error reading {f.name}: {str(e)}")
            
    status.text("Processing Complete!")
    
    if all_dataframes:
        # Final combine: axis=0 ensures rows are appended, sort=False maintains order
        return pd.concat(all_dataframes, axis=0, ignore_index=True, sort=False)
    return None

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
                # Fill empty cells
                data = data.fillna("")
                # Adding default Tally-style columns
                data['Target Ledger'] = "Suspense A/c"
                data['Voucher'] = "Journal"
                st.session_state['master_data'] = data
                st.rerun()

    # Phase 2: Auditor Recheck Mode
    if 'master_data' in st.session_state:
        st.divider()
        st.subheader("📝 Phase 2: Auditor Verification (Edit & Recheck)")
        st.info(f"Extracted {len(st.session_state['master_data'])} rows. Edit below if needed:")
        
        # Professional Grid Editor
        edited_df = st.data_editor(
            st.session_state['master_data'],
            column_config={
                "Target Ledger": st.column_config.SelectboxColumn(
                    "Target Ledger (Manual Edit)",
                    options=["Cash", "Bank", "Salary", "Purchase", "Sales", "GST", "Rent", "Suspense A/c"],
                    required=True,
                    width="medium"
                ),
                "Voucher": st.column_config.SelectboxColumn(
                    "Voucher",
                    options=["Payment (F5)", "Receipt (F6)", "Contra (F4)", "Journal (F7)"],
                    width="small"
                )
            },
            num_rows="dynamic",
            use_container_width=True,
            key="audit_grid_editor"
        )

        # Export Report
        if st.button("📈 Phase 3: Generate Final Financial Report", type="primary"):
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
