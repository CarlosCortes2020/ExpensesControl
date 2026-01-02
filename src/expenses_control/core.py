import sqlite3
import datetime
import os
import pandas as pd

# Determine the absolute path to the project root
# file is at src/expenses_control/core.py
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_NAME = os.path.join(BASE_DIR, 'data', 'expenses.db')
CSV_FILE = os.path.join(BASE_DIR, 'data', 'expenses.csv')

DEFAULT_CATEGORIES = [
    "Alimentos", "Transporte", "Hogar", "Servicios", "Entretenimiento",
    "Salud", "Educación", "Ahorro", "Compras", "Otros"
]

DEFAULT_INCOME_CATEGORIES = [
    "Salary", "Bonus", "Food Coupons", "Market coupons"
]

DEFAULT_COLUMNS = ["Fecha", "Categoría", "Descripción", "Miembro", "Monto", "Tipo"]

# --- CSV Persistence (Excel Style) ---

def load_data_csv():
    """Load expenses from CSV, or create an empty DataFrame if it doesn't exist."""
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame(columns=DEFAULT_COLUMNS)
    try:
        df = pd.read_csv(CSV_FILE)
        # Ensure all required columns exist
        for col in DEFAULT_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return pd.DataFrame(columns=DEFAULT_COLUMNS)

def save_data_csv(df):
    """Save the current DataFrame to CSV."""
    try:
        os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
        df.to_csv(CSV_FILE, index=False)
        return True
    except Exception as e:
        print(f"Error saving CSV: {e}")
        return False

# --- Database Logic (Backend - Legacy) ---

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with tables and default categories."""
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_NAME), exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Expenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT
        )
    ''')
    
    # Ensure 'type' and 'member' columns exist in expenses
    cursor.execute("PRAGMA table_info(expenses)")
    exp_cols = [info[1] for info in cursor.fetchall()]
    if 'type' not in exp_cols:
        cursor.execute("ALTER TABLE expenses ADD COLUMN type TEXT DEFAULT 'Gasto'")
    if 'member' not in exp_cols:
        cursor.execute("ALTER TABLE expenses ADD COLUMN member TEXT DEFAULT ''")

    # Budgets table (month is 1-12, year is YYYY, category is text)
    try:
        cursor.execute("SELECT category FROM budgets LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("DROP TABLE IF EXISTS budgets")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            category TEXT NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            amount REAL NOT NULL,
            PRIMARY KEY (category, month, year)
        )
    ''')
    
    # Categories table (for validation/listing)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Add 'type' column to categories if not exists
    cursor.execute("PRAGMA table_info(categories)")
    cat_cols = [info[1] for info in cursor.fetchall()]
    if 'type' not in cat_cols:
        cursor.execute("ALTER TABLE categories ADD COLUMN type TEXT DEFAULT 'Expense'")
    
    # Seed Expense categories if empty
    cursor.execute("SELECT count(*) FROM categories WHERE type='Expense'")
    if cursor.fetchone()[0] == 0:
        for cat in DEFAULT_CATEGORIES:
            cursor.execute('INSERT INTO categories (name, type) VALUES (?, ?)', (cat, 'Expense'))
            
    # Seed Income categories if empty
    cursor.execute("SELECT count(*) FROM categories WHERE type='Income'")
    if cursor.fetchone()[0] == 0:
        for cat in DEFAULT_INCOME_CATEGORIES:
            cursor.execute('INSERT INTO categories (name, type) VALUES (?, ?)', (cat, 'Income'))
    
    conn.commit()
    conn.close()

    # Attempt to import CSV if DB expenses are empty
    import_csv_to_db()

def import_csv_to_db():
    """Import data from legacy CSV if DB is empty."""
    if not os.path.exists(CSV_FILE):
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if we already have expenses
    cursor.execute('SELECT count(*) FROM expenses')
    if cursor.fetchone()[0] > 0:
        conn.close()
        return # DB already populated
    
    print("Migrating CSV data to Database...")
    try:
        df = pd.read_csv(CSV_FILE)
        # Expected CSV columns: "Fecha", "Categoría", "Descripción", "Miembro", "Monto", "Tipo"
        # DB columns: date, category, amount, description
        # We lose "Miembro" and "Tipo" in the current DB schema?
        # Let's check DB schema in init_db. 
        # Schema: date, category, amount, description. 
        # Missing: type, member. 
        # We should update the schema to be lossless before importing.
        
        # Ensure new columns exist
        cursor.execute("PRAGMA table_info(expenses)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'type' not in columns:
            cursor.execute('ALTER TABLE expenses ADD COLUMN type TEXT')
        if 'member' not in columns:
            cursor.execute('ALTER TABLE expenses ADD COLUMN member TEXT')
        
        for _, row in df.iterrows():
            cursor.execute(
                'INSERT INTO expenses (date, category, description, member, amount, type) VALUES (?, ?, ?, ?, ?, ?)',
                (
                    row.get('Fecha', ''), 
                    row.get('Categoría', 'Otros'), 
                    row.get('Descripción', ''), 
                    row.get('Miembro', ''),
                    row.get('Monto', 0.0),
                    row.get('Tipo', 'Gasto')
                )
            )
        conn.commit()
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

def db_rename_category(old_name, new_name):
    """Rename a category and update all related expenses and budgets."""
    conn = get_db_connection()
    try:
        # Check if new name already exists
        cursor = conn.execute('SELECT 1 FROM categories WHERE name = ?', (new_name,))
        if cursor.fetchone():
            return False, "Category name already exists."

        # Begin transaction implicitly
        conn.execute('UPDATE categories SET name = ? WHERE name = ?', (new_name, old_name))
        conn.execute('UPDATE expenses SET category = ? WHERE category = ?', (new_name, old_name))
        conn.execute('UPDATE budgets SET category = ? WHERE category = ?', (new_name, old_name))
        
        conn.commit()
        return True, "Success"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def db_get_categories(ctype=None):
    """Fetch all category names, optionally filtered by type ('Expense' or 'Income')."""
    conn = get_db_connection()
    if ctype:
        query = 'SELECT name FROM categories WHERE type = ?'
        params = (ctype,)
    else:
        query = 'SELECT name FROM categories'
        params = ()
        
    categories = [row['name'] for row in conn.execute(query, params).fetchall()]
    conn.close()
    return categories

def db_add_category(name, ctype='Expense'):
    """Add a new category."""
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO categories (name, type) VALUES (?, ?)', (name, ctype))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def db_add_expense(date, category, amount, description, expense_type="Gasto", member=""):
    """Insert a new expense into the database."""
    conn = get_db_connection()
    try:
        # Check schema
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(expenses)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'type' in columns and 'member' in columns:
             conn.execute(
                'INSERT INTO expenses (date, category, amount, description, type, member) VALUES (?, ?, ?, ?, ?, ?)',
                (date, category, amount, description, expense_type, member)
            )
        else:
            # Fallback for legacy schema (though import_csv_to_db should have fixed it)
            conn.execute(
                'INSERT INTO expenses (date, category, amount, description) VALUES (?, ?, ?, ?)',
                (date, category, amount, description)
            )
        conn.commit()
    finally:
        conn.close()

def db_set_budget(category, month, year, amount):
    """Set or update the budget for a specific category, month and year."""
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO budgets (category, month, year, amount) VALUES (?, ?, ?, ?) '
        'ON CONFLICT(category, month, year) DO UPDATE SET amount=excluded.amount',
        (category, month, year, amount)
    )
    conn.commit()
    conn.close()

def db_get_all_expenses_df():
    """Fetch all expenses as a DataFrame (for GUI)."""
    conn = get_db_connection()
    try:
        # Check for extended schema columns
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(expenses)")
        columns = [info[1] for info in cursor.fetchall()]
        
        has_type = 'type' in columns
        has_member = 'member' in columns
        
        query = "SELECT id, date as 'Fecha', category as 'Categoría', amount as 'Monto', description as 'Descripción'"
        if has_type:
            query += ", type as 'Tipo'"
        else:
            query += ", 'Gasto' as 'Tipo'"
            
        if has_member:
            query += ", member as 'Miembro'"
        else:
            query += ", '' as 'Miembro'"
            
        query += " FROM expenses ORDER BY date DESC"
        
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        print(f"Error fetching expenses DF: {e}")
        return pd.DataFrame(columns=DEFAULT_COLUMNS)
    finally:
        conn.close()

def db_get_budget_matrix(year, ctype='Expense'):
    """
    Return a DataFrame where:
    Index = Categories (filtered by type)
    Columns = Months (1-12)
    Values = Budget Amount
    """
    conn = get_db_connection()
    try:
        # Get categories of specific type
        categories = db_get_categories(ctype)
        
        if not categories:
            return pd.DataFrame(columns=range(1, 13))

        # Get budgets for these categories
        # Ideally we should filter by category type via join, but simple "IN" clause works for small list
        placeholders = ','.join(['?'] * len(categories))
        query = f"SELECT category, month, amount FROM budgets WHERE year = ? AND category IN ({placeholders})"
        
        df_budgets = pd.read_sql_query(query, conn, params=[year] + categories)
        
        if df_budgets.empty:
            df_pivot = pd.DataFrame(0.0, index=categories, columns=range(1, 13))
        else:
            df_pivot = df_budgets.pivot(index='category', columns='month', values='amount').fillna(0.0)
            # Reindex to ensure all categories and months are present
            df_pivot = df_pivot.reindex(index=categories, columns=range(1, 13), fill_value=0.0)
            
        return df_pivot
    finally:
        conn.close()

def db_delete_expense(expense_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
    conn.commit()
    conn.close()

def db_update_expense(expense_id, field, value):
    conn = get_db_connection()
    # Be careful with field injection, but this is local app.
    # Map friendly names to DB columns
    field_map = {
        'Fecha': 'date',
        'Categoría': 'category',
        'Monto': 'amount',
        'Descripción': 'description',
        'Tipo': 'type',
        'Miembro': 'member'
    }
    db_field = field_map.get(field)
    if not db_field:
        return
        
    conn.execute(f'UPDATE expenses SET {db_field} = ? WHERE id = ?', (value, expense_id))
    conn.commit()
    conn.close()

def db_get_recent_expenses(limit=50):
    """Fetch recent expenses."""
    conn = get_db_connection()
    expenses = conn.execute(f'SELECT * FROM expenses ORDER BY date DESC LIMIT {limit}').fetchall()
    conn.close()
    return expenses

def db_get_analytics_data(year):
    """Fetch expenses, income, and budgets for a specific year and return as DataFrames."""
    conn = get_db_connection()
    
    # Load Expenses (Real)
    df_expenses = pd.read_sql_query(
        f"SELECT date, category, amount FROM expenses WHERE strftime('%Y', date) = '{year}' AND type = 'Gasto'",
        conn
    )
    
    # Load Income (Real)
    df_income = pd.read_sql_query(
        f"SELECT date, category, amount FROM expenses WHERE strftime('%Y', date) = '{year}' AND type = 'Ingreso'",
        conn
    )
    
    # Load Budgets (Expense Categories)
    exp_cats = db_get_categories('Expense')
    if exp_cats:
        placeholders = ','.join(['?'] * len(exp_cats))
        df_budget_expenses = pd.read_sql_query(
            f"SELECT category, month, amount as budget_amount FROM budgets WHERE year = ? AND category IN ({placeholders})",
            conn, params=[year] + exp_cats
        )
    else:
        df_budget_expenses = pd.DataFrame(columns=['category', 'month', 'budget_amount'])

    # Load Budgets (Income Categories)
    inc_cats = db_get_categories('Income')
    if inc_cats:
        placeholders = ','.join(['?'] * len(inc_cats))
        df_budget_income = pd.read_sql_query(
            f"SELECT category, month, amount as budget_income_amount FROM budgets WHERE year = ? AND category IN ({placeholders})",
            conn, params=[year] + inc_cats
        )
    else:
        df_budget_income = pd.DataFrame(columns=['category', 'month', 'budget_income_amount'])
        
    conn.close()
    
    return df_expenses, df_income, df_budget_expenses, df_budget_income

def process_monthly_summary(df_expenses, df_income, df_budget_expenses, df_budget_income):
    """Process raw dataframes into a monthly summary dataframe."""
    # Ensure month column exists even if empty
    all_months = pd.DataFrame({'month': range(1, 13)})

    # Expenses Summary
    if not df_expenses.empty:
        df_expenses['date'] = pd.to_datetime(df_expenses['date'])
        df_expenses['month'] = df_expenses['date'].dt.month
        monthly_expenses = df_expenses.groupby('month')['amount'].sum().reset_index().rename(columns={'amount': 'expense_amount'})
        analysis = pd.merge(all_months, monthly_expenses, on='month', how='left').fillna(0)
    else:
        analysis = all_months.copy()
        analysis['expense_amount'] = 0.0

    # Income Summary (Real)
    if not df_income.empty:
        df_income['date'] = pd.to_datetime(df_income['date'])
        df_income['month'] = df_income['date'].dt.month
        monthly_income = df_income.groupby('month')['amount'].sum().reset_index().rename(columns={'amount': 'income_amount'})
        analysis = pd.merge(analysis, monthly_income, on='month', how='left').fillna(0)
    else:
        analysis['income_amount'] = 0.0

    # Budget Summary (Expenses)
    if not df_budget_expenses.empty:
        monthly_budgets = df_budget_expenses.groupby('month')['budget_amount'].sum().reset_index()
        analysis = pd.merge(analysis, monthly_budgets, on='month', how='left').fillna(0)
    else:
        analysis['budget_amount'] = 0.0

    # Budget Summary (Income)
    if not df_budget_income.empty:
        monthly_budget_income = df_budget_income.groupby('month')['budget_income_amount'].sum().reset_index()
        analysis = pd.merge(analysis, monthly_budget_income, on='month', how='left').fillna(0)
    else:
        analysis['budget_income_amount'] = 0.0
    
    return analysis