import pandas as pd

try:
    excel_path = 'data/Presupuesto-familiar-2026.xlsx'
    xl = pd.ExcelFile(excel_path)
    sheet = 'Enero'
    df = xl.parse(sheet)
    
    # Check rows 20-100 to find "Gastos"
    print("\n--- Rows 20-100, Col 1 (Category Names) ---")
    print(df.iloc[20:100, 1].to_string())

    # Also check if there are columns way to the right (beyond day 31)
    print("\n--- Columns beyond 37? ---")
    if len(df.columns) > 38:
        print(df.iloc[0:10, 38:].to_string())
    else:
        print("No columns beyond Unnamed: 37")

except Exception as e:
    print(f"Error: {e}")
