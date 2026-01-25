import pandas as pd

try:
    excel_path = 'data/Presupuesto-familiar-2026.xlsx'
    xl = pd.ExcelFile(excel_path)
    
    sheet = 'Enero'
    print(f"--- Inspection of {sheet} ---")
    df = xl.parse(sheet)
    
    # Print a slice of the dataframe to find the structure
    # Rows 5 to 20, first 15 columns to see the "budget" part
    print("\n--- Rows 5-20, Cols 0-15 (Budget/Categories?) ---")
    print(df.iloc[5:20, 0:15].to_string())

    # Rows 5 to 20, Columns 15 to end to see the "daily expenses" part
    print("\n--- Rows 5-20, Cols 15+ (Daily Expenses?) ---")
    print(df.iloc[5:20, 15:].to_string())

except Exception as e:
    print(f"Error: {e}")
