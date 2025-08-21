import sqlite3
import pandas as pd
from flask import Flask, render_template, jsonify

app = Flask(__name__)

def get_reconciliation_data():
    conn = sqlite3.connect('reconciliation_results.db')
    
    try:
        matched_df = pd.read_sql_query("SELECT * FROM matched", conn)
    except:
        matched_df = pd.DataFrame()
    
    try:
        not_in_gstr2b_df = pd.read_sql_query("SELECT * FROM not_in_gstr2b", conn)
    except:
        not_in_gstr2b_df = pd.DataFrame()
    
    try:
        not_in_books_df = pd.read_sql_query("SELECT * FROM not_in_books", conn)
    except:
        not_in_books_df = pd.DataFrame()
    
    conn.close()
    
    return {
        'matched': matched_df,
        'not_in_gstr2b': not_in_gstr2b_df,
        'not_in_books': not_in_books_df
    }

@app.route('/')
def dashboard():
    data = get_reconciliation_data()
    
    summary = {
        'matched_count': len(data['matched']),
        'not_in_gstr2b_count': len(data['not_in_gstr2b']),
        'not_in_books_count': len(data['not_in_books']),
        'total_records': len(data['matched']) + len(data['not_in_gstr2b']) + len(data['not_in_books'])
    }
    
    return render_template('dashboard.html', 
                         summary=summary,
                         matched=data['matched'].to_html(classes='table table-striped', table_id='matched-table'),
                         not_in_gstr2b=data['not_in_gstr2b'].to_html(classes='table table-striped', table_id='not-gstr2b-table'),
                         not_in_books=data['not_in_books'].to_html(classes='table table-striped', table_id='not-books-table'))

@app.route('/api/summary')
def api_summary():
    data = get_reconciliation_data()
    return jsonify({
        'matched': len(data['matched']),
        'not_in_gstr2b': len(data['not_in_gstr2b']),
        'not_in_books': len(data['not_in_books'])
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)