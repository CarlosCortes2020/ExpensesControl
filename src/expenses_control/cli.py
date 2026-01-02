import datetime
import matplotlib.pyplot as plt
from tabulate import tabulate
from . import core as em

# --- CLI Interface (Frontend) ---

def get_date_input(prompt="Enter date (YYYY-MM-DD) [default: today]: "):
    date_str = input(prompt).strip()
    if not date_str:
        return datetime.date.today().strftime("%Y-%m-%d")
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        print("Invalid format. Using today's date.")
        return datetime.date.today().strftime("%Y-%m-%d")

def get_category_input():
    categories = em.db_get_categories()
    
    print("\nSelect a Category:")
    for i, cat in enumerate(categories, 1):
        print(f"{i}. {cat}")
    
    while True:
        try:
            choice = int(input("Enter choice number: "))
            if 1 <= choice <= len(categories):
                return categories[choice - 1]
        except ValueError:
            pass
        print("Invalid choice. Please try again.")

def add_expense():
    print("\n--- Register New Expense ---")
    date = get_date_input()
    amount_str = input("Enter amount: ")
    try:
        amount = float(amount_str)
    except ValueError:
        print("Invalid amount. Operation cancelled.")
        return

    category = get_category_input()
    description = input("Enter description (optional): ").strip()

    em.db_add_expense(date, category, amount, description)
    print("Expense registered successfully!")

def set_budget():
    print("\n--- Set Monthly Budget ---")
    try:
        year = int(input(f"Enter Year [default: {datetime.date.today().year}]: ") or datetime.date.today().year)
        month = int(input(f"Enter Month (1-12) [default: {datetime.date.today().month}]: ") or datetime.date.today().month)
        amount = float(input("Enter Budget Amount: "))
    except ValueError:
        print("Invalid input. Cancelled.")
        return

    em.db_set_budget(month, year, amount)
    print(f"Budget for {year}-{month:02d} set to {amount}")

def list_expenses():
    expenses = em.db_get_recent_expenses()
    
    if not expenses:
        print("No expenses found.")
        return

    data = [[e['id'], e['date'], e['category'], e['amount'], e['description']] for e in expenses]
    print("\n--- Recent Expenses ---")
    print(tabulate(data, headers=["ID", "Date", "Category", "Amount", "Description"], tablefmt="simple"))

def show_analytics():
    print("\n--- Annual Graphics & Analytics ---")
    try:
        year = int(input(f"Enter Year to analyze [default: {datetime.date.today().year}]: ") or datetime.date.today().year)
    except ValueError:
        year = datetime.date.today().year

    df_expenses, df_income, df_budget_expenses, df_budget_income = em.db_get_analytics_data(year)

    if df_expenses.empty and df_income.empty:
        print(f"No data found for {year}.")
        return

    analysis = em.process_monthly_summary(df_expenses, df_income, df_budget_expenses, df_budget_income)
    
    print(f"\nSummary for {year}:")
    print(tabulate(analysis, headers=["Month", "Total Expense", "Total Income", "Budget (Exp)", "Budget (Inc)"], tablefmt="grid", showindex=False))

    total_expense_year = analysis['expense_amount'].sum()
    total_budget_year = analysis['budget_amount'].sum()
    total_income_year = analysis['income_amount'].sum()
    
    print(f"\nTotal Annual Expense: {total_expense_year}")
    print(f"Total Annual Income: {total_income_year}")
    print(f"Total Annual Budget defined (Expenses): {total_budget_year}")

    # Visualization
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
    fig.suptitle(f'Financial Overview - {year}')

    # Plot 1: Monthly Trends
    months_labels = [datetime.date(year, m, 1).strftime('%b') for m in range(1, 13)]
    x = range(len(months_labels))
    width = 0.2

    ax1.bar([i - width*1.5 for i in x], analysis['budget_amount'], width, label='Budget (Exp)', color='green', alpha=0.6)
    ax1.bar([i - width*0.5 for i in x], analysis['expense_amount'], width, label='Expenses', color='red', alpha=0.6)
    ax1.bar([i + width*0.5 for i in x], analysis['income_amount'], width, label='Income (Real)', color='blue', alpha=0.6)
    ax1.bar([i + width*1.5 for i in x], analysis['budget_income_amount'], width, label='Income (Plan)', color='cyan', alpha=0.6)
    
    ax1.set_ylabel('Amount')
    ax1.set_title('Monthly Financial Overview')
    ax1.set_xticks(x)
    ax1.set_xticklabels(months_labels)
    ax1.legend()

    # Plot 2: Expense Distribution by Category (Pie Chart)
    if not df_expenses.empty:
        cat_expenses = df_expenses.groupby('category')['amount'].sum()
        ax2.pie(cat_expenses, labels=cat_expenses.index, autopct='%1.1f%%', startangle=90)
        ax2.set_title('Annual Expenses by Category')
    else:
        ax2.text(0.5, 0.5, 'No Expenses Data', ha='center')

    plt.tight_layout()
    plt.show()

def main_menu():
    em.init_db()
    while True:
        print("=== Expenses Control System ===")
        print("1. Register Expense")
        print("2. Set Monthly Budget")
        print("3. List Recent Expenses")
        print("4. Show Annual Analytics (Graphs)")
        print("5. Exit")
        
        choice = input("Select an option: ")
        
        if choice == '1':
            add_expense()
        elif choice == '2':
            set_budget()
        elif choice == '3':
            list_expenses()
        elif choice == '4':
            show_analytics()
        elif choice == '5':
            print("Goodbye!")
            break
        else:
            print("Invalid option.")
