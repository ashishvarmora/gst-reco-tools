import pandas as pd
import sqlite3
import json
from difflib import SequenceMatcher

class AutoMappingTool:
    def __init__(self):
        self.purchase_keywords = {
            'gstin': ['gstin', 'gst', 'tin'],
            'party_name': ['party', 'name', 'supplier', 'vendor'],
            'state': ['state', 'location'],
            'invoice_no': ['invoice', 'bill', 'no', 'number'],
            'invoice_date': ['date', 'invoice date'],
            'rate': ['rate', 'tax rate', '%'],
            'taxable_value': ['taxable', 'value', 'amount'],
            'igst': ['igst', 'integrated'],
            'cgst': ['cgst', 'central'],
            'sgst': ['sgst', 'state'],
            'cess': ['cess']
        }
        
        self.gstr2b_keywords = {
            'supplier_gstin': ['gstin', 'supplier gstin'],
            'supplier_name': ['name', 'supplier', 'trade'],
            'invoice_no': ['invoice', 'number'],
            'invoice_type': ['type', 'invoice type'],
            'invoice_date': ['date', 'invoice date'],
            'invoice_value': ['value', 'invoice value'],
            'place_of_supply': ['place', 'supply'],
            'rate': ['rate', '%'],
            'taxable_value': ['taxable', 'value'],
            'igst': ['integrated', 'igst'],
            'cgst': ['central', 'cgst'],
            'sgst': ['state', 'sgst'],
            'cess': ['cess'],
            'itc_availability': ['itc', 'availability']
        }
    
    def find_main_table(self, file_path):
        df = pd.read_excel(file_path)
        for i in range(len(df)):
            test_df = pd.read_excel(file_path, skiprows=i)
            if len(test_df.columns) >= 5:
                non_null_count = test_df.iloc[0].count() if not test_df.empty else 0
                if non_null_count >= 5:
                    return i
        return 0
    
    def similarity(self, a, b):
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def auto_map_columns(self, excel_columns, keywords):
        mapping = {}
        for std_col, keyword_list in keywords.items():
            best_match = None
            best_score = 0
            
            for excel_col in excel_columns:
                for keyword in keyword_list:
                    score = self.similarity(excel_col, keyword)
                    if score > best_score and score > 0.4:
                        best_score = score
                        best_match = excel_col
            
            if best_match:
                mapping[std_col] = best_match
        
        return mapping
    
    def process_excel(self, file_path, db_type):
        skip_rows = self.find_main_table(file_path)
        df = pd.read_excel(file_path, skiprows=skip_rows)
        df = df.dropna(how='all')
        
        keywords = self.purchase_keywords if db_type == 'purchase' else self.gstr2b_keywords
        mapping = self.auto_map_columns(df.columns, keywords)
        
        # Create standardized DataFrame
        mapped_df = pd.DataFrame()
        for std_col in keywords.keys():
            if std_col in mapping:
                mapped_df[std_col] = df[mapping[std_col]]
            else:
                mapped_df[std_col] = None
        
        # Save to database
        conn = sqlite3.connect(f'{db_type}_standard.db')
        mapped_df.to_sql(f'{db_type}_data', conn, if_exists='replace', index=False)
        conn.close()
        
        # Save mapping
        config = {'mapping': mapping, 'skip_rows': skip_rows}
        with open(f'{db_type}_mapping.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"{db_type.upper()} processed: {len(mapped_df)} records")
        print(f"Mapped columns: {list(mapping.values())}")
        
        return mapped_df

# Process both files
tool = AutoMappingTool()
purchase_df = tool.process_excel('purchase.xlsx', 'purchase')
gstr2b_df = tool.process_excel('gstr2b.xlsx', 'gstr2b')

print("\nStandardized databases created successfully!")