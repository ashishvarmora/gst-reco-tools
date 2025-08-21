import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import sqlite3
from datetime import datetime

class GSTReconciliationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GST Reconciliation System")
        self.root.geometry("1200x800")
        
        self.purchase_file = None
        self.gstr2b_file = None
        self.results = None
        
        self.setup_gui()
    
    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="🧾 GST Reconciliation System", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Purchase file selection
        ttk.Label(file_frame, text="Purchase Excel:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.purchase_label = ttk.Label(file_frame, text="No file selected", foreground="red")
        self.purchase_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Button(file_frame, text="Browse", command=self.select_purchase_file).grid(row=0, column=2, padx=5)
        
        # GSTR2B file selection
        ttk.Label(file_frame, text="GSTR2B Excel:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.gstr2b_label = ttk.Label(file_frame, text="No file selected", foreground="red")
        self.gstr2b_label.grid(row=1, column=1, sticky=tk.W, padx=5)
        ttk.Button(file_frame, text="Browse", command=self.select_gstr2b_file).grid(row=1, column=2, padx=5)
        
        # Process button
        self.process_btn = ttk.Button(file_frame, text="🔄 Process & Reconcile", command=self.process_files, state="disabled")
        self.process_btn.grid(row=2, column=0, columnspan=3, pady=10)
        
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Reconciliation Results", padding="10")
        results_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Summary labels
        self.summary_frame = ttk.Frame(results_frame)
        self.summary_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(results_frame)
        self.notebook.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(1, weight=1)
    
    def select_purchase_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Purchase Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if file_path:
            self.purchase_file = file_path
            self.purchase_label.config(text=file_path.split('/')[-1], foreground="green")
            self.check_files_selected()
    
    def select_gstr2b_file(self):
        file_path = filedialog.askopenfilename(
            title="Select GSTR2B Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if file_path:
            self.gstr2b_file = file_path
            self.gstr2b_label.config(text=file_path.split('/')[-1], foreground="green")
            self.check_files_selected()
    
    def check_files_selected(self):
        if self.purchase_file and self.gstr2b_file:
            self.process_btn.config(state="normal")
    
    def find_data_start(self, file_path):
        df = pd.read_excel(file_path)
        for i in range(len(df)):
            test_df = pd.read_excel(file_path, skiprows=i)
            if len(test_df.columns) >= 5 and not test_df.empty:
                if test_df.iloc[0].count() >= 5:
                    return i
        return 0
    
    def process_files(self):
        try:
            # Show progress
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Processing...")
            progress_window.geometry("300x100")
            ttk.Label(progress_window, text="Processing files...").pack(pady=20)
            progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
            progress_bar.pack(pady=10)
            progress_bar.start()
            self.root.update()
            
            # Read files
            purchase_skip = self.find_data_start(self.purchase_file)
            gstr2b_skip = self.find_data_start(self.gstr2b_file)
            
            purchase_df = pd.read_excel(self.purchase_file, skiprows=purchase_skip).dropna(how='all')
            gstr2b_df = pd.read_excel(self.gstr2b_file, skiprows=gstr2b_skip).dropna(how='all')
            
            # Standardize column names
            purchase_df.columns = ['gstin', 'party_name', 'state', 'invoice_no', 'invoice_date', 
                                  'rate', 'taxable_value', 'igst', 'cgst', 'sgst', 'cess', 'total_value']
            
            gstr2b_df.columns = ['supplier_gstin', 'supplier_name', 'invoice_no', 'invoice_type', 
                                'invoice_date', 'invoice_value', 'place_of_supply', 'reverse_charge',
                                'rate', 'taxable_value', 'igst', 'cgst', 'sgst', 'cess', 'period',
                                'filing_date', 'itc_availability', 'reason', 'tax_rate_percent', 
                                'source', 'irn_no', 'irn_date']
            
            # Perform reconciliation with detailed columns
            self.results = self.detailed_reconciliation(purchase_df, gstr2b_df)
            
            progress_window.destroy()
            self.display_results()
            
        except Exception as e:
            if 'progress_window' in locals():
                progress_window.destroy()
            messagebox.showerror("Error", f"Error processing files: {str(e)}")
    
    def detailed_reconciliation(self, purchase_df, gstr2b_df):
        matched = []
        not_in_gstr2b = []
        not_in_books = []
        
        # Create detailed matched records
        for _, p_row in purchase_df.iterrows():
            match_found = False
            for _, g_row in gstr2b_df.iterrows():
                if (str(p_row['gstin']).strip() == str(g_row['supplier_gstin']).strip() and
                    str(p_row['invoice_no']).strip() == str(g_row['invoice_no']).strip()):
                    
                    matched.append({
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
                        'Difference Record Value': float(p_row['taxable_value'] or 0) - float(g_row['taxable_value'] or 0),
                        'Difference Record IGST': float(p_row['igst'] or 0) - float(g_row['igst'] or 0),
                        'Difference Record CGST': float(p_row['cgst'] or 0) - float(g_row['cgst'] or 0),
                        'Difference Record SGST': float(p_row['sgst'] or 0) - float(g_row['sgst'] or 0),
                        'Difference Record CESS': float(p_row['cess'] or 0) - float(g_row['cess'] or 0),
                        'Status': 'Matched',
                        'Reason': 'Perfect Match',
                        'Accept / Reject': 'Accept',
                        'Remark 1': '',
                        'ITC Claim Status': g_row['itc_availability'],
                        'ITC Claim Month': '',
                        'A/C Month': '',
                        'GSTR 2B Month': '',
                        'GSTR1 Filing Month': '',
                        'GSTR1 Filing Date': '',
                        'Remark 2': '',
                        'Remark 3': '',
                        'Eligibility For ITC Books': 'Yes',
                        'Eligibility For ITC 2B': g_row['itc_availability'],
                        'Section Name': '',
                        'A/C Reverse Charge': 'No',
                        'GSTR 2B Reverse Charge': g_row['reverse_charge']
                    })
                    match_found = True
                    break
            
            if not match_found:
                not_in_gstr2b.append({
                    'GSTIN': p_row['gstin'],
                    'Name of Party': p_row['party_name'],
                    'State Name': p_row['state'],
                    'A/C Invoice No': p_row['invoice_no'],
                    'A/C Date': p_row['invoice_date'],
                    'A/C Taxable Value': p_row['taxable_value'],
                    'Status': 'Not in GSTR2B',
                    'Reason': 'Missing in GSTR2B'
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
                    'GSTR 2B Invoice No': g_row['invoice_no'],
                    'GSTR 2B Date': g_row['invoice_date'],
                    'GSTR 2B Taxable Value': g_row['taxable_value'],
                    'Status': 'Not in Books',
                    'Reason': 'Missing in Purchase Books'
                })
        
        return {
            'matched': pd.DataFrame(matched),
            'not_in_gstr2b': pd.DataFrame(not_in_gstr2b),
            'not_in_books': pd.DataFrame(not_in_books)
        }
    
    def display_results(self):
        # Clear existing tabs
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)
        
        # Update summary
        for widget in self.summary_frame.winfo_children():
            widget.destroy()
        
        matched_count = len(self.results['matched'])
        not_gstr2b_count = len(self.results['not_in_gstr2b'])
        not_books_count = len(self.results['not_in_books'])
        
        ttk.Label(self.summary_frame, text=f"✅ Matched: {matched_count}", foreground="green").grid(row=0, column=0, padx=10)
        ttk.Label(self.summary_frame, text=f"❌ Not in GSTR2B: {not_gstr2b_count}", foreground="red").grid(row=0, column=1, padx=10)
        ttk.Label(self.summary_frame, text=f"⚠️ Not in Books: {not_books_count}", foreground="orange").grid(row=0, column=2, padx=10)
        
        # Create tabs with data
        self.create_data_tab("✅ Matched", self.results['matched'])
        self.create_data_tab("❌ Not in GSTR2B", self.results['not_in_gstr2b'])
        self.create_data_tab("⚠️ Not in Books", self.results['not_in_books'])
        
        # Export button
        export_btn = ttk.Button(self.summary_frame, text="📤 Export to Excel", command=self.export_results)
        export_btn.grid(row=0, column=3, padx=10)
    
    def create_data_tab(self, title, df):
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text=title)
        
        # Create treeview
        tree = ttk.Treeview(tab_frame)
        tree.pack(fill=tk.BOTH, expand=True)
        
        if not df.empty:
            # Configure columns
            tree["columns"] = list(df.columns)
            tree["show"] = "headings"
            
            for col in df.columns:
                tree.heading(col, text=col)
                tree.column(col, width=100)
            
            # Insert data
            for _, row in df.iterrows():
                tree.insert("", tk.END, values=list(row))
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(tab_frame, orient=tk.VERTICAL, command=tree.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=v_scrollbar.set)
        
        h_scrollbar = ttk.Scrollbar(tab_frame, orient=tk.HORIZONTAL, command=tree.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        tree.configure(xscrollcommand=h_scrollbar.set)
    
    def export_results(self):
        if self.results:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")]
            )
            if file_path:
                with pd.ExcelWriter(file_path) as writer:
                    self.results['matched'].to_excel(writer, sheet_name='Matched', index=False)
                    self.results['not_in_gstr2b'].to_excel(writer, sheet_name='Not_in_GSTR2B', index=False)
                    self.results['not_in_books'].to_excel(writer, sheet_name='Not_in_Books', index=False)
                messagebox.showinfo("Success", f"Results exported to {file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GSTReconciliationGUI(root)
    root.mainloop()