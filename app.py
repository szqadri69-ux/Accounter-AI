import streamlit as st
import pandas as pd
import pdfplumber
import io
import re

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
        col_str = str(col).strip() if col is not None and str(col).strip() != "" else "Unnamed"
        if col_str in col_counts:
            col_counts[col_str] += 1
            new_cols.append(f"{col_str}_{col_counts[col_str]}")
        else:
            col_counts[col_str] = 0
            new_cols.append(col_str)
    return new_cols

# --- 2. ADVANCED DATA PARSER (SPECIAL FOR HDFC & ALIGNMENT ISSUES) ---

def extract_financial_data(files):
    """HDFC aur complex bank statements ke liye optimized parser"""
    all_dataframes = []
    status = st.empty()
    progress = st.progress(0)
    
    for idx, f in enumerate(files):
        try:
            status.text(f"Deep Scanning: {f.name}...")
            df_temp = None
            
            if f.name.lower().endswith('.pdf'):
                with pdfplumber.open(f) as pdf:
                    pages_data = []
                    for page in pdf.pages:
                        # Try Multiple Strategies for Bank Alignment
                        # Strategy 1: Text-based (Best for HDFC/Standard Banks)
                        table = page.extract_table({
                            "vertical_strategy": "text", 
                            "horizontal_strategy": "text",
                            "snap_tolerance": 3,
                        })
                        
                        if not table or len(table) < 2:
                            # Strategy 2: Line-based (Fallback)
                            table = page.extract_table()
                            
                        if table:
                            headers = [str(h).replace('\n', ' ') for h in table[0]]
                            unique_headers = make_columns_unique(headers)
                            
                            # Data Cleaning: Remove internal newlines that cause "stretching"
                            cleaned_rows = []
                            for row in table[1:]:
                                cleaned_row = [str(cell).replace('\n', ' ').strip() if cell else "" for cell in row]
                                # Sirf wo rows lein jisme kuch data ho
                                if any(cleaned_row):
                                    cleaned_rows.append(cleaned_row)
                            
                            p_df = pd.DataFrame(cleaned_rows, columns=unique_headers)
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
                # Basic cleaning
                df_temp = df_temp.fillna("")
                all_dataframes.append(df_temp)
            
            progress.progress((idx + 1) / len(files))
        except Exception as e:
            st.error(f"Error reading {f.name}: {str(e)}")
            
    status.text("Audit Processing Complete!")
    
    if all_dataframes:
        return pd.concat(all_dataframes, axis=0, ignore_index=True, sort=False)
    return None

# --- 3. PROFESSIONAL INTERFACE ---

st.title("🚀 Accounter-AI: Enterprise Auditor")
st.markdown("<h3 style='color: #2c3e50;'>All Rights Reserved by Shehzaad Kutchi Memon</h3>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("Software Control")
    st.info("Status: Local Processing Enabled")
    st.write("**Owner:** Shehzaad Kutchi Memon")
    st.write("**Engine:** High-Volume Parser v2.1")
    st.divider()
    st.write("© 2026 | All Rights Reserved")

# File Upload Section
uploaded_files = st.file_uploader(
    "Upload Bank Statements (HDFC, Paytm, SBI, etc.)", 
    type=['pdf', 'xlsx', 'xls', 'csv'], 
    accept_multiple_files=True
)

if uploaded_files:
    if 'master_data' not in st.session_state:
        if st.button("📊 START DEEP CALCULATION", type="primary"):
            data = extract_financial_data(uploaded_files)
            if data is not None and not data.empty:
                data = data.fillna("")
                # Add Auditor Columns
                data['Target Ledger'] = "Suspense A/c"
                data['Voucher'] = "Journal"
                st.session_state['master_data'] = data
                st.rerun()
            else:
                st.error("AI ne koi entry fetch nahi ki. Kripya file check karein.")

    # Phase 2: Auditor Recheck Mode
    if 'master_data' in st.session_state:
        st.divider()
        st.subheader("📝 Phase 2: Auditor Verification (Edit & Recheck)")
        st.write("Original Narrations dekh kar entries finalize karein:")
        
        # Professional Grid Editor
        edited_df = st.data_editor(
            st.session_state['master_data'],
            column_config={
                "Target Ledger": st.column_config.SelectboxColumn(
                    "Target Ledger",
                    options=["Cash", "Bank", "Salary", "Purchase", "Sales", "GST", "Rent", "Suspense A/c"],
                    required=True
                ),
                "Voucher": st.column_config.SelectboxColumn(
                    "Voucher",
                    options=["Payment (F5)", "Receipt (F6)", "Contra (F4)", "Journal (F7)"]
                )
            },
            num_rows="dynamic",
            use_container_width=True,
            key="audit_grid_v2"
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
