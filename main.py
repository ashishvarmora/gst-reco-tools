import pandas as pd
import sqlite3
import os

def main_menu():
    print("\n" + "="*50)
    print("🧾 GST RECONCILIATION SYSTEM")
    print("="*50)
    print("1. Process Excel Files & Create Databases")
    print("2. Run GST Reconciliation")
    print("3. View Reconciliation Results")
    print("4. Export Results to Excel")
    print("5. Start Web Dashboard")
    print("6. Exit")
    print("="*50)
    
    choice = input("Enter your choice (1-6): ")
    return choice

def process_excel_files():
    print("\n📊 Processing Excel Files...")
    
    # Read and clean purchase data
    purchase_df = pd.read_excel('purchase.xlsx', skiprows=6)
    purchase_df = purchase_df.dropna(how='all')
    purchase_df.columns = ['gstin', 'party_name', 'state', 'invoice_no', 'invoice_date', 
                          'rate', 'taxable_value', 'igst', 'cgst', 'sgst', 'cess', 'total_value']
    
    # Read and clean gstr2b data
    gstr2b_df = pd.read_excel('gstr2b.xlsx', skiprows=6)
    gstr2b_df = gstr2b_df.dropna(how='all')
    gstr2b_df.columns = ['supplier_gstin', 'supplier_name', 'invoice_no', 'invoice_type', 
                        'invoice_date', 'invoice_value', 'place_of_supply', 'reverse_charge',
                        'rate', 'taxable_value', 'igst', 'cgst', 'sgst', 'cess', 'period',
                        'filing_date', 'itc_availability', 'reason', 'tax_rate_percent', 
                        'source', 'irn_no', 'irn_date']
    
    # Save to databases
    conn = sqlite3.connect('gst_master.db')
    purchase_df.to_sql('purchase_data', conn, if_exists='replace', index=False)
    gstr2b_df.to_sql('gstr2b_data', conn, if_exists='replace', index=False)
    conn.close()
    
    print(f"✅ Purchase records processed: {len(purchase_df)}")
    print(f"✅ GSTR2B records processed: {len(gstr2b_df)}")
    print("✅ Databases created successfully!")

def run_reconciliation():
    print("\n🔄 Running GST Reconciliation...")
    
    conn = sqlite3.connect('gst_master.db')
    purchase_df = pd.read_sql_query("SELECT * FROM purchase_data", conn)
    gstr2b_df = pd.read_sql_query("SELECT * FROM gstr2b_data", conn)
    conn.close()
    
    matched = []
    not_in_gstr2b = []
    not_in_books = []
    
    # Find matches
    for _, p_row in purchase_df.iterrows():
        match_found = False
        for _, g_row in gstr2b_df.iterrows():
            if (str(p_row['gstin']).strip() == str(g_row['supplier_gstin']).strip() and
                str(p_row['invoice_no']).strip() == str(g_row['invoice_no']).strip()):
                matched.append({
                    'gstin': p_row['gstin'],
                    'party_name': p_row['party_name'],
                    'invoice_no': p_row['invoice_no'],
                    'purchase_value': p_row['taxable_value'],
                    'gstr2b_value': g_row['taxable_value'],
                    'difference': float(p_row['taxable_value'] or 0) - float(g_row['taxable_value'] or 0)
                })
                match_found = True
                break
        
        if not match_found:
            not_in_gstr2b.append({
                'gstin': p_row['gstin'],
                'party_name': p_row['party_name'],
                'invoice_no': p_row['invoice_no'],
                'taxable_value': p_row['taxable_value']
            })
    
    # Find GSTR2B records not in purchase
    for _, g_row in gstr2b_df.iterrows():
        match_found = False
        for _, p_row in purchase_df.iterrows():
            if (str(p_row['gstin']).strip() == str(g_row['supplier_gstin']).strip() and
                str(p_row['invoice_no']).strip() == str(g_row['invoice_no']).strip()):
                match_found = True
                break
        
        if not match_found:
            not_in_books.append({
                'supplier_gstin': g_row['supplier_gstin'],
                'supplier_name': g_row['supplier_name'],
                'invoice_no': g_row['invoice_no'],
                'taxable_value': g_row['taxable_value']
            })
    
    # Save results
    conn = sqlite3.connect('reconciliation_results.db')
    if matched:
        pd.DataFrame(matched).to_sql('matched', conn, if_exists='replace', index=False)
    if not_in_gstr2b:
        pd.DataFrame(not_in_gstr2b).to_sql('not_in_gstr2b', conn, if_exists='replace', index=False)
    if not_in_books:
        pd.DataFrame(not_in_books).to_sql('not_in_books', conn, if_exists='replace', index=False)
    conn.close()
    
    print(f"✅ Matched Records: {len(matched)}")
    print(f"❌ Not in GSTR2B: {len(not_in_gstr2b)}")
    print(f"⚠️ Not in Books: {len(not_in_books)}")
    print("✅ Reconciliation completed!")

def view_results():
    print("\n📋 Reconciliation Results:")
    
    try:
        conn = sqlite3.connect('reconciliation_results.db')
        
        print("\n✅ MATCHED RECORDS:")
        matched_df = pd.read_sql_query("SELECT * FROM matched LIMIT 5", conn)
        print(matched_df.to_string(index=False))
        
        print("\n❌ NOT IN GSTR2B:")
        not_gstr2b_df = pd.read_sql_query("SELECT * FROM not_in_gstr2b LIMIT 5", conn)
        print(not_gstr2b_df.to_string(index=False))
        
        print("\n⚠️ NOT IN BOOKS:")
        not_books_df = pd.read_sql_query("SELECT * FROM not_in_books LIMIT 5", conn)
        print(not_books_df.to_string(index=False))
        
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Please run reconciliation first!")

def export_results():
    print("\n📤 Exporting Results to Excel...")
    
    try:
        conn = sqlite3.connect('reconciliation_results.db')
        
        with pd.ExcelWriter('GST_Reconciliation_Report.xlsx') as writer:
            matched_df = pd.read_sql_query("SELECT * FROM matched", conn)
            not_gstr2b_df = pd.read_sql_query("SELECT * FROM not_in_gstr2b", conn)
            not_books_df = pd.read_sql_query("SELECT * FROM not_in_books", conn)
            
            matched_df.to_excel(writer, sheet_name='Matched', index=False)
            not_gstr2b_df.to_excel(writer, sheet_name='Not_in_GSTR2B', index=False)
            not_books_df.to_excel(writer, sheet_name='Not_in_Books', index=False)
        
        conn.close()
        print("✅ Excel report saved as 'GST_Reconciliation_Report.xlsx'")
    except Exception as e:
        print(f"❌ Error: {e}")

def start_dashboard():
    print("\n🌐 Starting Web Dashboard...")
    print("Dashboard will be available at: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    
    try:
        os.system("python dashboard.py")
    except KeyboardInterrupt:
        print("\n✅ Dashboard stopped")

def main():
    while True:
        choice = main_menu()
        
        if choice == '1':
            process_excel_files()
        elif choice == '2':
            run_reconciliation()
        elif choice == '3':
            view_results()
        elif choice == '4':
            export_results()
        elif choice == '5':
            start_dashboard()
        elif choice == '6':
            print("\n👋 Thank you for using GST Reconciliation System!")
            break
        else:
            print("\n❌ Invalid choice! Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()