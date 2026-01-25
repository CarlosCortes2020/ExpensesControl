import pandas as pd
import sqlite3
import datetime
import os

# Configuration
EXCEL_PATH = 'data/Presupuesto-familiar-2026.xlsx'
DB_PATH = 'data/expenses.db'
YEAR = 2026
MONTH_NAME = 'Enero'
MONTH_NUM = 1

# User specified mappings
CATEGORY_MAPPING = {
    'Restaurantes': 'Restaurante',
    # 'Medicamentos': 'Medicamentos', # Implicitly kept same
    # 'Renta Cuarto': 'Renta Cuarto', # Implicitly kept same
    # 'Comida Carlos': 'Comida Carlos' # Implicitly kept same
}

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def ensure_category_exists(conn, category_name):
    """Ensures category exists in DB. Adds it if not."""
    try:
        # Check if exists
        cur = conn.execute('SELECT 1 FROM categories WHERE name = ?', (category_name,))
        if cur.fetchone():
            return
        
        # Add new
        print(f"  [+] Creating new category: {category_name}")
        conn.execute('INSERT INTO categories (name, type) VALUES (?, ?)', (category_name, 'Expense'))
        conn.commit()
    except Exception as e:
        print(f"Error ensuring category {category_name}: {e}")

def import_enero():
    print(f"--- Importing {MONTH_NAME} Expenses ---")
    
    xl = pd.ExcelFile(EXCEL_PATH)
    df = xl.parse(MONTH_NAME)
    
    # Locate "Gastos" start
    gastos_start_idx = -1
    for idx, val in df.iloc[:, 1].items():
        if str(val).strip() == "Gastos":
            gastos_start_idx = idx
            break
            
    if gastos_start_idx == -1:
        print("Could not find 'Gastos' section.")
        return

    conn = get_db_connection()
    expenses_to_add = []
    current_group = "General" # Default group
    
    # Iterate rows from Gastos start
    for i in range(gastos_start_idx + 1, len(df)):
        raw_category_name = df.iloc[i, 1]
        
        # Skip empty rows
        if pd.isna(raw_category_name):
            continue
            
        raw_category_name = str(raw_category_name).strip()
        
        # Skip structural rows
        if raw_category_name in ['Categoría', 'SUMA', '-', 'Gastos']:
            continue
            
        # Check for data in day columns (7-37)
        row_data = df.iloc[i, 7:38]
        # Force numeric
        row_data = pd.to_numeric(row_data, errors='coerce')
        has_data = row_data.sum() > 0 if not row_data.isna().all() else False
        
        # Determine if this row is acting as a Group Header
        # Logic: If it looks like a group (e.g. UPPERCASE) AND implies classification
        # But wait, earlier analysis showed "ALIMENTOS Y BEBIDAS" (Group) had data? 
        # Actually, let's look closely at the data structure again. 
        # Usually Group Headers are just headers.
        # If I treat it as a group header, I update 'current_group'.
        # If it ALSO has data, I must also treat it as a category.
        
        is_group_header = raw_category_name.isupper() 
        # Note: "Medicamentos" is not upper. "ALIMENTOS Y BEBIDAS" is.
        
        if is_group_header:
            current_group = raw_category_name
        
        if not has_data:
            continue
            
        # If it has data, it's an expense entry.
        # Determine Final Category Name
        final_category = CATEGORY_MAPPING.get(raw_category_name, raw_category_name)
        
        # Iterate days to find expenses
        for day_idx in range(31):
            col_idx = 7 + day_idx
            if col_idx >= len(df.columns): break
            
            amount = df.iloc[i, col_idx]
            
            # Check if amount is valid number > 0
            try:
                amount = float(amount)
                if pd.isna(amount) or amount <= 0:
                    continue
            except (ValueError, TypeError):
                continue
                
            # Construct date
            try:
                day = day_idx + 1
                date_str = datetime.date(YEAR, MONTH_NUM, day).strftime('%Y-%m-%d')
                
                expenses_to_add.append({
                    'date': date_str,
                    'category': final_category,
                    'amount': amount,
                    'description': current_group, # Use Group as description
                    'type': 'Gasto'
                })
            except ValueError:
                continue # Invalid date

    print(f"Found {len(expenses_to_add)} expenses to import.")
    
    # Process Import
    count = 0
    for exp in expenses_to_add:
        ensure_category_exists(conn, exp['category'])
        
        conn.execute(
            'INSERT INTO expenses (date, category, amount, description, type, member, payment_method) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (
                exp['date'], 
                exp['category'], 
                exp['amount'], 
                exp['description'], 
                exp['type'],
                '', # member
                'Efectivo' # default payment method
            )
        )
        count += 1
        
    conn.commit()
    conn.close()
    print(f"Successfully imported {count} expenses into DB.")

if __name__ == "__main__":
    import_enero()
