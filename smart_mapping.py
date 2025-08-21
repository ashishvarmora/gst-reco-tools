import pandas as pd
import sqlite3
import json

class SmartMappingTool:
    def __init__(self):
        self.purchase_standard = {
            'gstin': 'TEXT',
            'party_name': 'TEXT', 
            'state': 'TEXT',
            'invoice_no': 'TEXT',
            'invoice_date': 'DATE',
            'rate': 'REAL',
            'taxable_value': 'REAL',
            'igst': 'REAL',
            'cgst': 'REAL', 
            'sgst': 'REAL',
            'cess': 'REAL'
        }
        
        self.gstr2b_standard = {
            'supplier_gstin': 'TEXT',
            'supplier_name': 'TEXT',
            'invoice_no': 'TEXT',
            'invoice_type': 'TEXT',
            'invoice_date': 'DATE',
            'invoice_value': 'REAL',
            'place_of_supply': 'TEXT',
            'rate': 'REAL',
            'taxable_value': 'REAL',
            'igst': 'REAL',
            'cgst': 'REAL',
            'sgst': 'REAL',
            'cess': 'REAL',
            'itc_availability': 'TEXT'
        }
    
    def find_data_start(self, file_path):
        df = pd.read_excel(file_path)
        for i in range(len(df)):
            test_df = pd.read_excel(file_path, skiprows=i)
            if len(test_df.columns) >= 5 and not test_df.empty:
                if test_df.iloc[0].count() >= 5:
                    return i, test_df.columns.tolist()
        return 0, []
    
    def create_mapping_file(self, file_path, db_type):
        skip_rows, columns = self.find_data_start(file_path)
        standard_cols = list(self.purchase_standard.keys()) if db_type == 'purchase' else list(self.gstr2b_standard.keys())
        
        # Auto-create basic mapping based on position for current files
        if db_type == 'purchase':
            mapping = {
                'gstin': columns[0] if len(columns) > 0 else None,
                'party_name': columns[1] if len(columns) > 1 else None,
                'state': columns[2] if len(columns) > 2 else None,
                'invoice_no': columns[3] if len(columns) > 3 else None,
                'invoice_date': columns[4] if len(columns) > 4 else None,
                'rate': columns[5] if len(columns) > 5 else None,
                'taxable_value': columns[6] if len(columns) > 6 else None,
                'igst': columns[7] if len(columns) > 7 else None,
                'cgst': columns[8] if len(columns) > 8 else None,
                'sgst': columns[9] if len(columns) > 9 else None,
                'cess': columns[10] if len(columns) > 10 else None
            }
        else:
            mapping = {
                'supplier_gstin': columns[0] if len(columns) > 0 else None,
                'supplier_name': columns[1] if len(columns) > 1 else None,
                'invoice_no': columns[2] if len(columns) > 2 else None,
                'invoice_type': columns[3] if len(columns) > 3 else None,
                'invoice_date': columns[4] if len(columns) > 4 else None,
                'invoice_value': columns[5] if len(columns) > 5 else None,
                'place_of_supply': columns[6] if len(columns) > 6 else None,
                'rate': columns[8] if len(columns) > 8 else None,
                'taxable_value': columns[9] if len(columns) > 9 else None,
                'igst': columns[10] if len(columns) > 10 else None,
                'cgst': columns[11] if len(columns) > 11 else None,
                'sgst': columns[12] if len(columns) > 12 else None,
                'cess': columns[13] if len(columns) > 13 else None,
                'itc_availability': columns[16] if len(columns) > 16 else None
            }
        
        config = {'mapping': mapping, 'skip_rows': skip_rows, 'columns': columns}
        with open(f'{db_type}_mapping.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        return mapping, skip_rows
    
    def load_or_create_mapping(self, file_path, db_type):
        try:
            with open(f'{db_type}_mapping.json', 'r') as f:
                config = json.load(f)
            return config['mapping'], config['skip_rows']
        except FileNotFoundError:
            return self.create_mapping_file(file_path, db_type)
    
    def process_to_database(self, file_path, db_type):
        mapping, skip_rows = self.load_or_create_mapping(file_path, db_type)
        
        df = pd.read_excel(file_path, skiprows=skip_rows)
        df = df.dropna(how='all')
        
        standard_schema = self.purchase_standard if db_type == 'purchase' else self.gstr2b_standard
        
        # Create standardized DataFrame
        result_df = pd.DataFrame()
        for std_col in standard_schema.keys():
            if mapping.get(std_col) and mapping[std_col] in df.columns:
                result_df[std_col] = df[mapping[std_col]]
            else:
                result_df[std_col] = None
        
        # Save to database
        conn = sqlite3.connect(f'{db_type}_standard.db')
        result_df.to_sql(f'{db_type}_data', conn, if_exists='replace', index=False)
        conn.close()
        
        print(f"{db_type.upper()}: {len(result_df)} records processed")
        return result_df

# Process files
tool = SmartMappingTool()
purchase_df = tool.process_to_database('purchase.xlsx', 'purchase')
gstr2b_df = tool.process_to_database('gstr2b.xlsx', 'gstr2b')

# Show sample data
print("\nPurchase Sample:")
print(purchase_df[['gstin', 'party_name', 'taxable_value']].head(3))

print("\nGSTR2B Sample:")
print(gstr2b_df[['supplier_gstin', 'supplier_name', 'taxable_value']].head(3))