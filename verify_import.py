import sqlite3

def verify():
    conn = sqlite3.connect('data/expenses.db')
    conn.row_factory = sqlite3.Row
    
    print("--- Muestra de Registros de Enero ---")
    query_sample = "SELECT date, category, amount, description FROM expenses WHERE date LIKE '2026-01-%' LIMIT 10"
    rows = conn.execute(query_sample).fetchall()
    for r in rows:
        print(f"{r['date']} | {r['category']:<20} | ${r['amount']:>8.2f} | {r['description']}")
        
    print("\n--- Resumen por Clasificación (Group Header) ---")
    query_summary = """
        SELECT description, COUNT(*) as count, SUM(amount) as total 
        FROM expenses 
        WHERE date LIKE '2026-01-%' 
        GROUP BY description 
        ORDER BY total DESC
    """
    groups = conn.execute(query_summary).fetchall()
    for g in groups:
        print(f"{g['description']:<25} | {g['count']:>3} registros | Total: ${g['total']:>10.2f}")
        
    conn.close()

if __name__ == '__main__':
    verify()

