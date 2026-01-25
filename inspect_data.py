import sqlite3
import pandas as pd
import sys

# 1. Inspect Database Schema
print("--- Database Schema ---")
try:
    conn = sqlite3.connect('data/expenses.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for table_name in tables:
        table = table_name[0]
        print(f"\nTable: {table}")
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
            
    conn.close()
except Exception as e:
    print(f"Error reading DB: {e}")

# 2. Inspect Excel File
print("\n--- Excel Structure ---")
try:
    excel_path = 'data/Presupuesto-familiar-2026.xlsx'
    xl = pd.ExcelFile(excel_path)
    print(f"Sheets: {xl.sheet_names}")
    
    for sheet in xl.sheet_names:
        print(f"\nSheet: {sheet}")
        df = xl.parse(sheet)
        print(df.head().to_string())
        print("\nColumns:", df.columns.tolist())
except Exception as e:
    print(f"Error reading Excel: {e}")
