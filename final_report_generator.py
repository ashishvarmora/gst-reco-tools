import pandas as pd
import sqlite3
from datetime import datetime
import os

def generate_comprehensive_report():
    # Read data from existing files
    purchase_df = pd.read_excel('purchase.xlsx', skiprows=6).dropna(how='all')
    gstr2b_df = pd.read_excel('gstr2b.xlsx', skiprows=6).dropna(how='all')
    
    # Standardize columns
    purchase_df.columns = ['gstin', 'party_name', 'state', 'invoice_no', 'invoice_date', 
                          'rate', 'taxable_value', 'igst', 'cgst', 'sgst', 'cess', 'total_value']
    
    gstr2b_df.columns = ['supplier_gstin', 'supplier_name', 'invoice_no', 'invoice_type', 
                        'invoice_date', 'invoice_value', 'place_of_supply', 'reverse_charge',
                        'rate', 'taxable_value', 'igst', 'cgst', 'sgst', 'cess', 'period',
                        'filing_date', 'itc_availability', 'reason', 'tax_rate_percent', 
                        'source', 'irn_no', 'irn_date']
    
    # Perform detailed reconciliation
    matched = []
    mismatched = []
    not_in_gstr2b = []
    not_in_books = []
    
    # Process matches and mismatches
    for _, p_row in purchase_df.iterrows():
        match_found = False
        for _, g_row in gstr2b_df.iterrows():
            if (str(p_row['gstin']).strip() == str(g_row['supplier_gstin']).strip() and
                str(p_row['invoice_no']).strip() == str(g_row['invoice_no']).strip()):
                
                # Calculate differences
                value_diff = float(p_row['taxable_value'] or 0) - float(g_row['taxable_value'] or 0)
                igst_diff = float(p_row['igst'] or 0) - float(g_row['igst'] or 0)
                cgst_diff = float(p_row['cgst'] or 0) - float(g_row['cgst'] or 0)
                sgst_diff = float(p_row['sgst'] or 0) - float(g_row['sgst'] or 0)
                cess_diff = float(p_row['cess'] or 0) - float(g_row['cess'] or 0)
                
                # Determine if matched or mismatched
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
                'Differnce Record Value': '',
                'Differnce Record IGST': '',
                'Differnce Record CGST': '',
                'Differnce Record SGST': '',
                'Differnce Record CESS': '',
                'Status': 'Not in GSTR2B',
                'Reason': 'Missing in GSTR2B',
                'Accept / Reject': 'Reject',
                'Remark 1': 'Invoice not found in GSTR2B',
                'ITC Claim Status': 'Not Available',
                'ITC Claim Month': '',
                'A/C Month': '',
                'GSTR 2B Month': '',
                'GSTR1 Filing Month': '',
                'GSTR1 Filing Date': '',
                'Remark 2': '',
                'Remark 3': '',
                'Eligibility For ITC Books': 'No',
                'Eligibility For ITC 2B': 'No',
                'Section Name': '',
                'A/C Reverse Charge': 'No',
                'GSTR 2B Reverse Charge': ''
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
                'Differnce Record Value': '',
                'Differnce Record IGST': '',
                'Differnce Record CGST': '',
                'Differnce Record SGST': '',
                'Differnce Record CESS': '',
                'Status': 'Not in Books',
                'Reason': 'Missing in Purchase Books',
                'Accept / Reject': 'Review Required',
                'Remark 1': 'Invoice not found in books',
                'ITC Claim Status': g_row.get('itc_availability', ''),
                'ITC Claim Month': '',
                'A/C Month': '',
                'GSTR 2B Month': '',
                'GSTR1 Filing Month': '',
                'GSTR1 Filing Date': g_row.get('filing_date', ''),
                'Remark 2': '',
                'Remark 3': '',
                'Eligibility For ITC Books': 'No',
                'Eligibility For ITC 2B': g_row.get('itc_availability', ''),
                'Section Name': '',
                'A/C Reverse Charge': '',
                'GSTR 2B Reverse Charge': g_row.get('reverse_charge', '')
            })
    
    # Create summary report
    summary = {
        'Category': ['Matched', 'Mismatched', 'Not in GSTR2B', 'Not in Books', 'Total'],
        'Count': [len(matched), len(mismatched), len(not_in_gstr2b), len(not_in_books), 
                 len(matched) + len(mismatched) + len(not_in_gstr2b) + len(not_in_books)],
        'Percentage': [
            f"{len(matched)/(len(matched) + len(mismatched) + len(not_in_gstr2b) + len(not_in_books))*100:.1f}%" if (len(matched) + len(mismatched) + len(not_in_gstr2b) + len(not_in_books)) > 0 else "0%",
            f"{len(mismatched)/(len(matched) + len(mismatched) + len(not_in_gstr2b) + len(not_in_books))*100:.1f}%" if (len(matched) + len(mismatched) + len(not_in_gstr2b) + len(not_in_books)) > 0 else "0%",
            f"{len(not_in_gstr2b)/(len(matched) + len(mismatched) + len(not_in_gstr2b) + len(not_in_books))*100:.1f}%" if (len(matched) + len(mismatched) + len(not_in_gstr2b) + len(not_in_books)) > 0 else "0%",
            f"{len(not_in_books)/(len(matched) + len(mismatched) + len(not_in_gstr2b) + len(not_in_books))*100:.1f}%" if (len(matched) + len(mismatched) + len(not_in_gstr2b) + len(not_in_books)) > 0 else "0%",
            "100%"
        ]
    }
    
    # Generate Excel report with 5 sheets
    filename = f"GST_Reconciliation_Final_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        # Summary sheet
        pd.DataFrame(summary).to_excel(writer, sheet_name='Summary', index=False)
        
        # Matched records
        if matched:
            pd.DataFrame(matched).to_excel(writer, sheet_name='Matched', index=False)
        
        # Mismatched records
        if mismatched:
            pd.DataFrame(mismatched).to_excel(writer, sheet_name='Mismatched', index=False)
        
        # Not in GSTR2B
        if not_in_gstr2b:
            pd.DataFrame(not_in_gstr2b).to_excel(writer, sheet_name='Not_in_GSTR2B', index=False)
        
        # Not in Books
        if not_in_books:
            pd.DataFrame(not_in_books).to_excel(writer, sheet_name='Not_in_Books', index=False)
    
    print(f"✅ Final report generated: {filename}")
    print(f"📊 Summary:")
    print(f"   Matched: {len(matched)}")
    print(f"   Mismatched: {len(mismatched)}")
    print(f"   Not in GSTR2B: {len(not_in_gstr2b)}")
    print(f"   Not in Books: {len(not_in_books)}")
    
    return filename

if __name__ == "__main__":
    generate_comprehensive_report()