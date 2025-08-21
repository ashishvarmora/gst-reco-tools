import pandas as pd
import sqlite3
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

class GSTReconciliation:
    def __init__(self):
        self.setup_databases()
    
    def setup_databases(self):
        # Read and process purchase data
        purchase_df = pd.read_excel('purchase.xlsx', skiprows=6)
        purchase_df = purchase_df.dropna(how='all')
        purchase_df.columns = ['gstin', 'party_name', 'state', 'invoice_no', 'invoice_date', 
                              'rate', 'taxable_value', 'igst', 'cgst', 'sgst', 'cess', 'total_value']
        
        # Read and process gstr2b data
        gstr2b_df = pd.read_excel('gstr2b.xlsx', skiprows=6)
        gstr2b_df = gstr2b_df.dropna(how='all')
        gstr2b_df.columns = ['supplier_gstin', 'supplier_name', 'invoice_no', 'invoice_type', 
                            'invoice_date', 'invoice_value', 'place_of_supply', 'reverse_charge',
                            'rate', 'taxable_value', 'igst', 'cgst', 'sgst', 'cess', 'period',
                            'filing_date', 'itc_availability', 'reason', 'tax_rate_percent', 
                            'source', 'irn_no', 'irn_date']
        
        # Save to databases
        conn = sqlite3.connect('gst_data.db')
        purchase_df.to_sql('purchase', conn, if_exists='replace', index=False)
        gstr2b_df.to_sql('gstr2b', conn, if_exists='replace', index=False)
        conn.close()
        
        self.purchase_df = purchase_df
        self.gstr2b_df = gstr2b_df
    
    def perform_reconciliation(self):
        # Match on GSTIN and Invoice Number
        matched = []
        unmatched_purchase = []
        unmatched_gstr2b = []
        
        for _, purchase_row in self.purchase_df.iterrows():
            match_found = False
            for _, gstr2b_row in self.gstr2b_df.iterrows():
                if (str(purchase_row['gstin']).strip() == str(gstr2b_row['supplier_gstin']).strip() and
                    str(purchase_row['invoice_no']).strip() == str(gstr2b_row['invoice_no']).strip()):
                    
                    matched.append({
                        'gstin': purchase_row['gstin'],
                        'party_name': purchase_row['party_name'],
                        'invoice_no': purchase_row['invoice_no'],
                        'purchase_value': purchase_row['taxable_value'],
                        'gstr2b_value': gstr2b_row['taxable_value'],
                        'difference': float(purchase_row['taxable_value'] or 0) - float(gstr2b_row['taxable_value'] or 0),
                        'status': 'Matched'
                    })
                    match_found = True
                    break
            
            if not match_found:
                unmatched_purchase.append({
                    'gstin': purchase_row['gstin'],
                    'party_name': purchase_row['party_name'],
                    'invoice_no': purchase_row['invoice_no'],
                    'taxable_value': purchase_row['taxable_value'],
                    'status': 'Not in GSTR2B'
                })
        
        # Find GSTR2B entries not in purchase
        for _, gstr2b_row in self.gstr2b_df.iterrows():
            match_found = False
            for _, purchase_row in self.purchase_df.iterrows():
                if (str(purchase_row['gstin']).strip() == str(gstr2b_row['supplier_gstin']).strip() and
                    str(purchase_row['invoice_no']).strip() == str(gstr2b_row['invoice_no']).strip()):
                    match_found = True
                    break
            
            if not match_found:
                unmatched_gstr2b.append({
                    'supplier_gstin': gstr2b_row['supplier_gstin'],
                    'supplier_name': gstr2b_row['supplier_name'],
                    'invoice_no': gstr2b_row['invoice_no'],
                    'taxable_value': gstr2b_row['taxable_value'],
                    'status': 'Not in Books'
                })
        
        return {
            'matched': pd.DataFrame(matched),
            'not_in_gstr2b': pd.DataFrame(unmatched_purchase),
            'not_in_books': pd.DataFrame(unmatched_gstr2b)
        }

def main():
    st.set_page_config(page_title="GST Reconciliation Dashboard", layout="wide")
    st.title("🧾 GST Reconciliation Dashboard")
    
    # Initialize reconciliation
    if 'reco' not in st.session_state:
        with st.spinner("Loading data..."):
            st.session_state.reco = GSTReconciliation()
            st.session_state.results = st.session_state.reco.perform_reconciliation()
    
    results = st.session_state.results
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Purchase Records", len(st.session_state.reco.purchase_df))
    with col2:
        st.metric("📋 Total GSTR2B Records", len(st.session_state.reco.gstr2b_df))
    with col3:
        st.metric("✅ Matched Records", len(results['matched']))
    with col4:
        st.metric("❌ Unmatched Records", len(results['not_in_gstr2b']) + len(results['not_in_books']))
    
    # Reconciliation summary chart
    st.subheader("📈 Reconciliation Summary")
    
    summary_data = {
        'Category': ['Matched', 'Not in GSTR2B', 'Not in Books'],
        'Count': [len(results['matched']), len(results['not_in_gstr2b']), len(results['not_in_books'])]
    }
    
    fig = px.pie(summary_data, values='Count', names='Category', 
                 color_discrete_map={'Matched': '#00ff00', 'Not in GSTR2B': '#ff6b6b', 'Not in Books': '#ffa500'})
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed tables
    tab1, tab2, tab3, tab4 = st.tabs(["✅ Matched", "❌ Not in GSTR2B", "⚠️ Not in Books", "📊 Raw Data"])
    
    with tab1:
        st.subheader("Matched Records")
        if not results['matched'].empty:
            st.dataframe(results['matched'], use_container_width=True)
            
            # Value difference analysis
            if 'difference' in results['matched'].columns:
                fig_diff = px.histogram(results['matched'], x='difference', 
                                       title="Value Differences in Matched Records")
                st.plotly_chart(fig_diff, use_container_width=True)
        else:
            st.info("No matched records found")
    
    with tab2:
        st.subheader("Records in Purchase but Not in GSTR2B")
        if not results['not_in_gstr2b'].empty:
            st.dataframe(results['not_in_gstr2b'], use_container_width=True)
            
            # Download button
            csv = results['not_in_gstr2b'].to_csv(index=False)
            st.download_button("📥 Download CSV", csv, "not_in_gstr2b.csv", "text/csv")
        else:
            st.info("All purchase records found in GSTR2B")
    
    with tab3:
        st.subheader("Records in GSTR2B but Not in Books")
        if not results['not_in_books'].empty:
            st.dataframe(results['not_in_books'], use_container_width=True)
            
            # Download button
            csv = results['not_in_books'].to_csv(index=False)
            st.download_button("📥 Download CSV", csv, "not_in_books.csv", "text/csv")
        else:
            st.info("All GSTR2B records found in books")
    
    with tab4:
        st.subheader("Raw Data")
        data_choice = st.selectbox("Select Data", ["Purchase Data", "GSTR2B Data"])
        
        if data_choice == "Purchase Data":
            st.dataframe(st.session_state.reco.purchase_df, use_container_width=True)
        else:
            st.dataframe(st.session_state.reco.gstr2b_df, use_container_width=True)
    
    # Refresh button
    if st.button("🔄 Refresh Data"):
        del st.session_state.reco
        del st.session_state.results
        st.rerun()

if __name__ == "__main__":
    main()