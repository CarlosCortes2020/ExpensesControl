import pandas as pd
import sqlite3
import datetime
import difflib

# Configuration
EXCEL_PATH = 'data/Presupuesto-familiar-2026.xlsx'
DB_PATH = 'data/expenses.db'
YEAR = 2026
MONTH_NAME = 'Enero'
MONTH_NUM = 1

def get_db_categories():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM categories")
    cats = {row[0] for row in cursor.fetchall()}
    conn.close()
    return cats

def analyze_sheet(sheet_name, month_num, xl):
    df = xl.parse(sheet_name)
    
    # Locate "Gastos" start
    gastos_start_idx = -1
    for idx, val in df.iloc[:, 1].items():
        if str(val).strip() == "Gastos":
            gastos_start_idx = idx
            break
    
    if gastos_start_idx == -1:
        return set()

    found_categories = set()
    
    # Iterate rows from Gastos start
    for i in range(gastos_start_idx + 1, len(df)):
        category_name = df.iloc[i, 1]
        
        # Skip empty rows
        if pd.isna(category_name):
            continue
            
        category_name = str(category_name).strip()
        
        # Skip structural rows
        if category_name in ['Categoría', 'SUMA', '-', 'Gastos']:
            continue
            
        # Check if row has data
        row_data = df.iloc[i, 7:38]
        row_data = pd.to_numeric(row_data, errors='coerce')
        has_data = row_data.sum() > 0 if not row_data.isna().all() else False
        
        if has_data:
            found_categories.add(category_name)

    return found_categories

def main():
    print(f"--- Analyzing Categories for {MONTH_NAME} ---")
    db_cats = get_db_categories()
    db_cats_list = list(db_cats)
    
    xl = pd.ExcelFile(EXCEL_PATH)
    enero_cats = analyze_sheet(MONTH_NAME, MONTH_NUM, xl)
    
    print(f"Categories found in {MONTH_NAME} with data: {len(enero_cats)}")
    
    exact_matches = []
    new_cats = []
    similar_cats = []

    for cat in enero_cats:
        if cat in db_cats:
            exact_matches.append(cat)
        else:
            # Check for similarity
            matches = difflib.get_close_matches(cat, db_cats_list, n=1, cutoff=0.6)
            if matches:
                similar_cats.append((cat, matches[0]))
            else:
                new_cats.append(cat)
    
    print("\n--- Report ---")
    
    if similar_cats:
        print(f"\n[POTENTIAL DUPLICATES/SIMILAR] ({len(similar_cats)}):")
        print("Excel Category  ->  Existing DB Category")
        for excel_cat, db_cat in similar_cats:
            print(f"  '{excel_cat}'  ->  '{db_cat}'")

    if new_cats:
        print(f"\n[NEW CATEGORIES] ({len(new_cats)}):")
        for cat in new_cats:
            print(f"  - {cat}")

    print(f"\n[EXACT MATCHES] ({len(exact_matches)}):")
    # Uncomment to see exact matches if needed
    # for cat in exact_matches:
    #    print(f"  - {cat}")

if __name__ == "__main__":
    main()
