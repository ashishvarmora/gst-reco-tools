import streamlit as st
import pandas as pd
import plotly.express as px
import io
from datetime import datetime

def find_data_start(uploaded_file):
    df = pd.read_excel(uploaded_file)
    for i in range(len(df)):
        test_df = pd.read_excel(uploaded_file, skiprows=i)
        if len(test_df.columns) >= 5 and not test_df.empty:
            if test_df.iloc[0].count() >= 5:
                return i
    return 0

def comprehensive_reconciliation(purchase_df, gstr2b_df):
    matched = []
    mismatched = []
    not_in_gstr2b = []
    not_in_books = []
    
    for _, p_row in purchase_df.iterrows():
        match_found = False
        for _, g_row in gstr2b_df.iterrows():
            if (str(p_row['gstin']).strip() == str(g_row['supplier_gstin']).strip() and
                str(p_row['invoice_no']).strip() == str(g_row['invoice_no']).strip()):
                
                value_diff = float(p_row['taxable_value'] or 0) - float(g_row['taxable_value'] or 0)
                igst_diff = float(p_row['igst'] or 0) - float(g_row['igst'] or 0)
                cgst_diff = float(p_row['cgst'] or 0) - float(g_row['cgst'] or 0)
                sgst_diff = float(p_row['sgst'] or 0) - float(g_row['sgst'] or 0)
                cess_diff = float(p_row['cess'] or 0) - float(g_row['cess'] or 0)
                
                is_perfect_match = (abs(value_diff) < 0.01 and abs(igst_diff) < 0.01 and 
                                  abs(cgst_diff) < 0.01 and abs(sgst_diff) < 0.01 and abs(cess_diff) < 0.01)
                
                record = {
                    'GSTIN': p_row['gstin'],
                    'Name of Party': p_row['party_name'],
                    'State Name': p_row['state'],
                    'A/C Invoice No': p_row['invoice_no'],
                    'A/C Date': p_row['invoice_date'],
                    'A/C Rate': p_row['rate'],
                    'A/C Taxable Value': p_row['taxable_value'],
                    'A/C IGST': p_row['igst'],
                    'A/C CGST': p_row['cgst'],
                    'A/C SGST': p_row['sgst'],
                    'A/C CESS': p_row['cess'],
                    'GSTR 2B Invoice No': g_row['invoice_no'],
                    'GSTR 2B Date': g_row['invoice_date'],
                    'GSTR 2B Rate': g_row['rate'],
                    'GSTR 2B Taxable Value': g_row['taxable_value'],
                    'GSTR 2B IGST': g_row['igst'],
                    'GSTR 2B CGST': g_row['cgst'],
                    'GSTR 2B SGST': g_row['sgst'],
                    'GSTR 2B CESS': g_row['cess'],
                    'Differnce Record Value': value_diff,
                    'Differnce Record IGST': igst_diff,
                    'Differnce Record CGST': cgst_diff,
                    'Differnce Record SGST': sgst_diff,
                    'Differnce Record CESS': cess_diff,
                    'Status': 'Matched' if is_perfect_match else 'Mismatched',
                    'Reason': 'Perfect Match' if is_perfect_match else 'Value Difference',
                    'Accept / Reject': 'Accept' if is_perfect_match else 'Review Required',
                    'Remark 1': '' if is_perfect_match else 'Check value differences',
                    'ITC Claim Status': g_row.get('itc_availability', ''),
                    'ITC Claim Month': '',
                    'A/C Month': '',
                    'GSTR 2B Month': '',
                    'GSTR1 Filing Month': '',
                    'GSTR1 Filing Date': g_row.get('filing_date', ''),
                    'Remark 2': '',
                    'Remark 3': '',
                    'Eligibility For ITC Books': 'Yes',
                    'Eligibility For ITC 2B': g_row.get('itc_availability', ''),
                    'Section Name': '',
                    'A/C Reverse Charge': 'No',
                    'GSTR 2B Reverse Charge': g_row.get('reverse_charge', '')
                }
                
                if is_perfect_match:
                    matched.append(record)
                else:
                    mismatched.append(record)
                
                match_found = True
                break
        
        if not match_found:
            not_in_gstr2b.append({
                'GSTIN': p_row['gstin'],
                'Name of Party': p_row['party_name'],
                'State Name': p_row['state'],
                'A/C Invoice No': p_row['invoice_no'],
                'A/C Date': p_row['invoice_date'],
                'A/C Rate': p_row['rate'],
                'A/C Taxable Value': p_row['taxable_value'],
                'A/C IGST': p_row['igst'],
                'A/C CGST': p_row['cgst'],
                'A/C SGST': p_row['sgst'],
                'A/C CESS': p_row['cess'],
                'GSTR 2B Invoice No': '',
                'GSTR 2B Date': '',
                'GSTR 2B Rate': '',
                'GSTR 2B Taxable Value': '',
                'GSTR 2B IGST': '',
                'GSTR 2B CGST': '',
                'GSTR 2B SGST': '',
                'GSTR 2B CESS': '',
                'Status': 'Not in GSTR2B',
                'Reason': 'Missing in GSTR2B',
                'Accept / Reject': 'Reject',
                'Remark 1': 'Invoice not found in GSTR2B',
                'Eligibility For ITC Books': 'No',
                'A/C Reverse Charge': 'No'
            })
    
    for _, g_row in gstr2b_df.iterrows():
        match_found = False
        for _, p_row in purchase_df.iterrows():
            if (str(p_row['gstin']).strip() == str(g_row['supplier_gstin']).strip() and
                str(p_row['invoice_no']).strip() == str(g_row['invoice_no']).strip()):
                match_found = True
                break
        
        if not match_found:
            not_in_books.append({
                'GSTIN': g_row['supplier_gstin'],
                'Name of Party': g_row['supplier_name'],
                'State Name': '',
                'A/C Invoice No': '',
                'A/C Date': '',
                'A/C Rate': '',
                'A/C Taxable Value': '',
                'A/C IGST': '',
                'A/C CGST': '',
                'A/C SGST': '',
                'A/C CESS': '',
                'GSTR 2B Invoice No': g_row['invoice_no'],
                'GSTR 2B Date': g_row['invoice_date'],
                'GSTR 2B Rate': g_row['rate'],
                'GSTR 2B Taxable Value': g_row['taxable_value'],
                'GSTR 2B IGST': g_row['igst'],
                'GSTR 2B CGST': g_row['cgst'],
                'GSTR 2B SGST': g_row['sgst'],
                'GSTR 2B CESS': g_row['cess'],
                'Status': 'Not in Books',
                'Reason': 'Missing in Purchase Books',
                'Accept / Reject': 'Review Required',
                'Remark 1': 'Invoice not found in books',
                'ITC Claim Status': g_row.get('itc_availability', ''),
                'GSTR 2B Reverse Charge': g_row.get('reverse_charge', '')
            })
    
    return {
        'matched': pd.DataFrame(matched),
        'mismatched': pd.DataFrame(mismatched),
        'not_in_gstr2b': pd.DataFrame(not_in_gstr2b),
        'not_in_books': pd.DataFrame(not_in_books)
    }

def main():
    st.set_page_config(page_title="GST Reconciliation Dashboard", layout="wide")
    st.title("🧾 GST Reconciliation Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📁 Upload Purchase Excel")
        purchase_file = st.file_uploader("Choose Purchase Excel file", type=['xlsx', 'xls'], key="purchase")
    
    with col2:
        st.subheader("📁 Upload GSTR2B Excel")
        gstr2b_file = st.file_uploader("Choose GSTR2B Excel file", type=['xlsx', 'xls'], key="gstr2b")
    
    if purchase_file and gstr2b_file:
        if st.button("🔄 Process & Reconcile", type="primary"):
            with st.spinner("Processing files and performing reconciliation..."):
                try:
                    purchase_skip = find_data_start(purchase_file)
                    gstr2b_skip = find_data_start(gstr2b_file)
                    
                    purchase_df = pd.read_excel(purchase_file, skiprows=purchase_skip).dropna(how='all')
                    gstr2b_df = pd.read_excel(gstr2b_file, skiprows=gstr2b_skip).dropna(how='all')
                    
                    purchase_df.columns = ['gstin', 'party_name', 'state', 'invoice_no', 'invoice_date', 
                                          'rate', 'taxable_value', 'igst', 'cgst', 'sgst', 'cess', 'total_value']
                    
                    gstr2b_df.columns = ['supplier_gstin', 'supplier_name', 'invoice_no', 'invoice_type', 
                                        'invoice_date', 'invoice_value', 'place_of_supply', 'reverse_charge',
                                        'rate', 'taxable_value', 'igst', 'cgst', 'sgst', 'cess', 'period',
                                        'filing_date', 'itc_availability', 'reason', 'tax_rate_percent', 
                                        'source', 'irn_no', 'irn_date']
                    
                    results = comprehensive_reconciliation(purchase_df, gstr2b_df)
                    st.session_state.results = results
                    st.success("✅ Reconciliation completed successfully!")
                    
                except Exception as e:
                    st.error(f"❌ Error processing files: {str(e)}")
    
    if 'results' in st.session_state:
        results = st.session_state.results
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("✅ Matched", len(results['matched']))
        with col2:
            st.metric("⚠️ Mismatched", len(results['mismatched']))
        with col3:
            st.metric("❌ Not in GSTR2B", len(results['not_in_gstr2b']))
        with col4:
            st.metric("📋 Not in Books", len(results['not_in_books']))
        with col5:
            total = len(results['matched']) + len(results['mismatched']) + len(results['not_in_gstr2b']) + len(results['not_in_books'])
            st.metric("📊 Total Records", total)
        
        # One-click comprehensive Excel download
        st.subheader("📤 Complete Report Download")
        if st.button("🔽 Download Complete Excel Report (5 Sheets)", type="primary"):
            output = io.BytesIO()
            
            summary_data = {
                'Category': ['Matched', 'Mismatched', 'Not in GSTR2B', 'Not in Books', 'Total'],
                'Count': [len(results['matched']), len(results['mismatched']), len(results['not_in_gstr2b']), len(results['not_in_books']), total],
                'Percentage': [
                    f"{len(results['matched'])/total*100:.1f}%" if total > 0 else "0%",
                    f"{len(results['mismatched'])/total*100:.1f}%" if total > 0 else "0%",
                    f"{len(results['not_in_gstr2b'])/total*100:.1f}%" if total > 0 else "0%",
                    f"{len(results['not_in_books'])/total*100:.1f}%" if total > 0 else "0%",
                    "100%"
                ]
            }
            
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
                
                if not results['matched'].empty:
                    results['matched'].to_excel(writer, sheet_name='Matched', index=False)
                if not results['mismatched'].empty:
                    results['mismatched'].to_excel(writer, sheet_name='Mismatched', index=False)
                if not results['not_in_gstr2b'].empty:
                    results['not_in_gstr2b'].to_excel(writer, sheet_name='Not_in_GSTR2B', index=False)
                if not results['not_in_books'].empty:
                    results['not_in_books'].to_excel(writer, sheet_name='Not_in_Books', index=False)
            
            st.download_button(
                label="📥 Download Complete Report",
                data=output.getvalue(),
                file_name=f"GST_Reconciliation_Complete_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # Chart
        if total > 0:
            chart_data = pd.DataFrame({
                'Category': ['Matched', 'Mismatched', 'Not in GSTR2B', 'Not in Books'],
                'Count': [len(results['matched']), len(results['mismatched']), len(results['not_in_gstr2b']), len(results['not_in_books'])]
            })
            
            fig = px.pie(chart_data, values='Count', names='Category', 
                        color_discrete_map={'Matched': '#00ff00', 'Mismatched': '#ffaa00', 'Not in GSTR2B': '#ff6b6b', 'Not in Books': '#ffa500'})
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed results tabs
        tab1, tab2, tab3, tab4 = st.tabs(["✅ Matched", "⚠️ Mismatched", "❌ Not in GSTR2B", "📋 Not in Books"])
        
        with tab1:
            st.subheader(f"Matched Records ({len(results['matched'])})")
            if not results['matched'].empty:
                st.dataframe(results['matched'], use_container_width=True)
            else:
                st.info("No perfectly matched records found")
        
        with tab2:
            st.subheader(f"Mismatched Records ({len(results['mismatched'])})")
            if not results['mismatched'].empty:
                st.dataframe(results['mismatched'], use_container_width=True)
            else:
                st.info("No mismatched records found")
        
        with tab3:
            st.subheader(f"Not in GSTR2B ({len(results['not_in_gstr2b'])})")
            if not results['not_in_gstr2b'].empty:
                st.dataframe(results['not_in_gstr2b'], use_container_width=True)
            else:
                st.info("All purchase records found in GSTR2B")
        
        with tab4:
            st.subheader(f"Not in Books ({len(results['not_in_books'])})")
            if not results['not_in_books'].empty:
                st.dataframe(results['not_in_books'], use_container_width=True)
            else:
                st.info("All GSTR2B records found in books")

if __name__ == "__main__":
    main()