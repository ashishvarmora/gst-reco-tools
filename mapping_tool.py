import pandas as pd
import sqlite3
import json
import os

class ExcelMappingTool:
    def __init__(self):
        self.purchase_standard_columns = [
            'gstin', 'party_name', 'state', 'invoice_no', 'invoice_date', 
            'rate', 'taxable_value', 'igst', 'cgst', 'sgst', 'cess'
        ]
        self.gstr2b_standard_columns = [
            'supplier_gstin', 'supplier_name', 'invoice_no', 'invoice_type', 
            'invoice_date', 'invoice_value', 'place_of_supply', 'rate', 
            'taxable_value', 'igst', 'cgst', 'sgst', 'cess', 'itc_availability'
        ]
        
    def find_main_table(self, file_path):
        """Find main table by checking rows with min 5 columns"""
        df = pd.read_excel(file_path)
        for i in range(len(df)):
            test_df = pd.read_excel(file_path, skiprows=i)
            if len(test_df.columns) >= 5 and not test_df.empty:
                non_null_count = test_df.iloc[0].count()
                if non_null_count >= 5:
                    return i
        return 0
    
    def create_mapping(self, file_path, db_type):
        """Create column mapping for Excel to database"""
        skip_rows = self.find_main_table(file_path)
        df = pd.read_excel(file_path, skiprows=skip_rows)
        
        print(f"\nFound columns in {db_type} Excel:")
        for i, col in enumerate(df.columns):
            print(f"{i+1}. {col}")
        
        standard_cols = self.purchase_standard_columns if db_type == 'purchase' else self.gstr2b_standard_columns
        mapping = {}
        
        print(f"\nMap to standard {db_type} columns:")
        for std_col in standard_cols:
            print(f"\nStandard column: {std_col}")
            choice = input(f"Enter column number (1-{len(df.columns)}) or 0 to skip: ")
            if choice != '0' and choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(df.columns):
                    mapping[std_col] = df.columns[idx]
        
        return mapping, skip_rows
    
    def save_mapping(self, mapping, skip_rows, db_type):
        """Save mapping to JSON file"""
        config = {'mapping': mapping, 'skip_rows': skip_rows}
        with open(f'{db_type}_mapping.json', 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Mapping saved to {db_type}_mapping.json")
    
    def load_mapping(self, db_type):
        """Load mapping from JSON file"""
        try:
            with open(f'{db_type}_mapping.json', 'r') as f:
                config = json.load(f)
            return config['mapping'], config['skip_rows']
        except FileNotFoundError:
            return None, None
    
    def apply_mapping(self, file_path, mapping, skip_rows, standard_columns):
        """Apply mapping and return standardized DataFrame"""
        df = pd.read_excel(file_path, skiprows=skip_rows)
        df = df.dropna(how='all')
        
        mapped_df = pd.DataFrame()
        for std_col in standard_columns:
            if std_col in mapping and mapping[std_col] in df.columns:
                mapped_df[std_col] = df[mapping[std_col]]
            else:
                mapped_df[std_col] = None
        
        return mapped_df
    
    def create_database(self, df, db_name, table_name):
        """Create database with standardized data"""
        conn = sqlite3.connect(f'{db_name}.db')
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        conn.close()
        print(f"Database {db_name}.db created with {len(df)} records")

def main():
    tool = ExcelMappingTool()
    
    # Process Purchase Excel
    print("=== PURCHASE EXCEL PROCESSING ===")
    purchase_mapping, purchase_skip = tool.load_mapping('purchase')
    
    if purchase_mapping is None:
        print("No existing mapping found. Creating new mapping...")
        purchase_mapping, purchase_skip = tool.create_mapping('purchase.xlsx', 'purchase')
        tool.save_mapping(purchase_mapping, purchase_skip, 'purchase')
    else:
        print("Loaded existing purchase mapping")
    
    purchase_df = tool.apply_mapping('purchase.xlsx', purchase_mapping, purchase_skip, tool.purchase_standard_columns)
    tool.create_database(purchase_df, 'purchase_standard', 'purchase_data')
    
    # Process GSTR2B Excel
    print("\n=== GSTR2B EXCEL PROCESSING ===")
    gstr2b_mapping, gstr2b_skip = tool.load_mapping('gstr2b')
    
    if gstr2b_mapping is None:
        print("No existing mapping found. Creating new mapping...")
        gstr2b_mapping, gstr2b_skip = tool.create_mapping('gstr2b.xlsx', 'gstr2b')
        tool.save_mapping(gstr2b_mapping, gstr2b_skip, 'gstr2b')
    else:
        print("Loaded existing gstr2b mapping")
    
    gstr2b_df = tool.apply_mapping('gstr2b.xlsx', gstr2b_mapping, gstr2b_skip, tool.gstr2b_standard_columns)
    tool.create_database(gstr2b_df, 'gstr2b_standard', 'gstr2b_data')
    
    print("\n=== PROCESSING COMPLETE ===")

if __name__ == "__main__":
    main()