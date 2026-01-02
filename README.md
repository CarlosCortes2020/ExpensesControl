# Expenses Control System

A powerful and user-friendly desktop application for personal financial management, built with **Python**, **PyQt6**, **Pandas**, and **SQLite**. This application allows users to track daily expenses, plan monthly budgets for both income and expenses, and visualize financial trends.

## 🚀 Features

### 1. Expense Tracking ("Gastos" Tab)
*   **Ledger View:** View all recorded daily expenses in a detailed list.
*   **CRUD Operations:** Add, Edit, and Delete expense records.
*   **Database Integration:** Data is securely stored in a local SQLite database (`data/expenses.db`).

### 2. Budget Management ("Presupuesto" Tab)
*   **Dual View:** Split view for **Income** (Ingresos) and **Expenses** (Gastos) planning.
*   **Excel-like Grid:** 
    *   **Months (1-12)** as columns.
    *   **Categories** as rows.
    *   **Totals:** Automatic calculation of Monthly Totals (Top Row) and Category Totals (Right Column).
*   **Dynamic Editing:**
    *   **Live Updates:** Totals recalculate instantly upon editing a cell.
    *   **Quick Creation:** Type in the empty bottom row to instantly create a new Category.
    *   **Renaming:** Rename categories directly in the grid.
*   **Clipboard Support:** Full **Copy (Ctrl+C)** and **Paste (Ctrl+V)** functionality compatible with Excel.
*   **Auto-Resize:** Automatically adjusts column widths to fit content.

### 3. Financial Analytics
*   **Interactive Trend Chart:** A visual representation at the bottom of the Budget tab.
*   **Multi-Series Plotting:**
    *   ✅ **Presupuesto (Green):** Planned Expenses from the budget table.
    *   ✅ **Gastos (Red):** Actual Expenses recorded in the ledger.
    *   ✅ **Ingresos (Blue):** Planned Income from the income table.
*   **Filtering:** Toggle specific series on/off using checkboxes.

## 🛠️ Installation & Requirements

### Prerequisites
*   Python 3.8+

### Setup
1.  Clone or download the repository.
2.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    *Key dependencies: `PyQt6`, `pandas`, `matplotlib`, `tabulate`.*

## ▶️ Usage

Run the application using the main entry point:

```bash
python main_gui_qt.py
```

### Navigation
*   **Tab 1: Gastos (Expenses):** Use this to log your daily receipts. 
    *   *Add:* Menu > Edición > Agregar Gasto.
    *   *Delete:* Select rows and press Delete or use the Menu.
*   **Tab 2: Presupuesto (Budget):** Use this to plan your year.
    *   *Edit:* Double-click any cell or type directly.
    *   *New Category:* Go to the last empty row, type a name in the "Categoría" column, and press Enter.
    *   *Analysis:* Watch the chart at the bottom update as you change your budget.

## 📂 Project Structure

```
ExpensesControl/
├── data/                   # Database storage
│   ├── expenses.db         # SQLite Database (Auto-generated)
│   └── expenses.csv        # Legacy data (Auto-imported)
├── src/
│   └── expenses_control/
│       ├── core.py         # Backend logic, DB handling, Analytics
│       ├── cli.py          # Legacy CLI interface
│       └── gui/
│           ├── qt_app.py   # Main GUI Logic (View/Controller)
│           └── models.py   # Qt Models (ExpenseTableModel, BudgetTableModel)
├── main_gui_qt.py          # Entry point for GUI
├── main_cli.py             # Entry point for CLI
├── requirements.txt        # Dependencies
└── README.md               # Documentation
```

## 🧠 Technical Highlights
*   **MVC Pattern:** Separation of data (Pandas/SQLite) from presentation (PyQt6 Tables) using custom `QAbstractTableModel`.
*   **Robust Backend:** Automatic schema migration ensures the database adds necessary columns (`type`, `member`) without breaking existing data.
*   **Matplotlib Integration:** Seamless embedding of Matplotlib figures within the PyQt6 interface using `FigureCanvasQTAgg`.