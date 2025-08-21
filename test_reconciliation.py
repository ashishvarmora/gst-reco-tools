import pandas as pd
import sqlite3

# Read and clean data
purchase_df = pd.read_excel('purchase.xlsx', skiprows=6)
purchase_df = purchase_df.dropna(how='all')
purchase_df.columns = ['gstin', 'party_name', 'state', 'invoice_no', 'invoice_date', 
                      'rate', 'taxable_value', 'igst', 'cgst', 'sgst', 'cess', 'total_value']

gstr2b_df = pd.read_excel('gstr2b.xlsx', skiprows=6)
gstr2b_df = gstr2b_df.dropna(how='all')
gstr2b_df.columns = ['supplier_gstin', 'supplier_name', 'invoice_no', 'invoice_type', 
                    'invoice_date', 'invoice_value', 'place_of_supply', 'reverse_charge',
                    'rate', 'taxable_value', 'igst', 'cgst', 'sgst', 'cess', 'period',
                    'filing_date', 'itc_availability', 'reason', 'tax_rate_percent', 
                    'source', 'irn_no', 'irn_date']

print(f"Purchase records: {len(purchase_df)}")
print(f"GSTR2B records: {len(gstr2b_df)}")

# Perform reconciliation
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
                'gstr2b_value': g_row['taxable_value']
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

# Results
print(f"\n=== RECONCILIATION RESULTS ===")
print(f"Matched: {len(matched)}")
print(f"Not in GSTR2B: {len(not_in_gstr2b)}")
print(f"Not in Books: {len(not_in_books)}")

# Save results to database
conn = sqlite3.connect('reconciliation_results.db')

pd.DataFrame(matched).to_sql('matched', conn, if_exists='replace', index=False)
pd.DataFrame(not_in_gstr2b).to_sql('not_in_gstr2b', conn, if_exists='replace', index=False)
pd.DataFrame(not_in_books).to_sql('not_in_books', conn, if_exists='replace', index=False)

conn.close()

print("\nResults saved to reconciliation_results.db")

# Show samples
if matched:
    print("\nMatched Sample:")
    print(pd.DataFrame(matched).head(3))

if not_in_gstr2b:
    print("\nNot in GSTR2B Sample:")
    print(pd.DataFrame(not_in_gstr2b).head(3))

if not_in_books:
    print("\nNot in Books Sample:")
    print(pd.DataFrame(not_in_books).head(3))