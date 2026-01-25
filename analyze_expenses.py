import pandas as pd
import sqlite3
import datetime

# Configuration
EXCEL_PATH = 'data/Presupuesto-familiar-2026.xlsx'
DB_PATH = 'data/expenses.db'
YEAR = 2026
MONTHS = {
    'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5, 'Junio': 6,
    'Julio': 7, 'Agosto': 8, 'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12
}

def get_db_categories():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM categories")
    cats = {row[0] for row in cursor.fetchall()}
    conn.close()
    return cats

def is_category_row(row_val):
    if pd.isna(row_val): return False
    if str(row_val).strip() in ['-', 'Gastos', 'Categoría', 'SUMA']: return False
    # Check if it's a group header (uppercase often indicates group in this sheet, but not always reliable)
    # However, rows with actual data are categories. Group headers usually don't have data in day columns.
    return True

def analyze_sheet(sheet_name, month_num, xl, db_cats):
    df = xl.parse(sheet_name)
    
    # Locate "Gastos" start
    gastos_start_idx = -1
    for idx, val in df.iloc[:, 1].items():
        if str(val).strip() == "Gastos":
            gastos_start_idx = idx
            break
    
    if gastos_start_idx == -1:
        print(f"[{sheet_name}] 'Gastos' section not found.")
        return []

    expenses_found = []
    current_group = "Unknown"
    
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
            
        # Heuristic for Group Headers: 
        # In this sheet, group headers like "ALIMENTOS Y BEBIDAS" seem to be in all caps
        # and likely don't have daily data.
        # Let's check if there is data in columns 7-37
        row_data = df.iloc[i, 7:38]
        # Force conversion to numeric, coercing errors (strings) to NaN
        row_data = pd.to_numeric(row_data, errors='coerce')
        has_data = row_data.sum() > 0 if not row_data.isna().all() else False
        
        if not has_data:
            # Assume it's a group header if it has no data and looks like a header (e.g. Uppercase)
            # Or it might be just an unused category.
            # But "ALIMENTOS Y BEBIDAS" is a group.
            if category_name.isupper():
                current_group = category_name
                continue
            # If it's not uppercase but has no data, it might be an unused category. 
            # We can skip it or treat it as category with 0 expenses.
            continue
            
        # If we are here, it's a category with data
        # Iterate days
        for day_idx in range(31):
            col_idx = 7 + day_idx
            if col_idx >= len(df.columns): break
            
            amount = df.iloc[i, col_idx]
            if pd.notna(amount) and isinstance(amount, (int, float)) and amount > 0:
                # Construct date
                try:
                    # day_idx 0 is Day 1
                    day = day_idx + 1
                    # check valid date (e.g., Feb 30)
                    date_obj = datetime.date(YEAR, month_num, day)
                    
                    expenses_found.append({
                        'date': date_obj.strftime('%Y-%m-%d'),
                        'category': category_name,
                        'group': current_group,
                        'amount': amount,
                        'known_in_db': category_name in db_cats
                    })
                except ValueError:
                    continue # Invalid date (e.g., Feb 30)

    return expenses_found

def main():
    print("--- Analyzing Excel and Matching with DB ---")
    db_cats = get_db_categories()
    print(f"Loaded {len(db_cats)} categories from DB.")
    
    xl = pd.ExcelFile(EXCEL_PATH)
    
    total_expenses = 0
    unknown_categories = set()
    
    for sheet in xl.sheet_names:
        if sheet in MONTHS:
            print(f"Processing {sheet}...")
            expenses = analyze_sheet(sheet, MONTHS[sheet], xl, db_cats)
            count = len(expenses)
            total_expenses += count
            if count > 0:
                print(f"  Found {count} expense entries.")
                # Show a few examples
                # print(f"  Example: {expenses[0]}")
                
                for exp in expenses:
                    if not exp['known_in_db']:
                        unknown_categories.add(exp['category'])
    
    print("\n--- Summary ---")
    print(f"Total Expenses Identified: {total_expenses}")
    print(f"Unique Categories NOT in DB ({len(unknown_categories)}):")
    for cat in unknown_categories:
        print(f"  - {cat}")

if __name__ == "__main__":
    main()
