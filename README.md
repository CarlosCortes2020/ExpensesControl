# Expenses Control System

A versatile personal finance management system offering multiple interfaces to suit your workflow. Whether you prefer a power-user spreadsheet experience (Qt), a modern dashboard (Tk), or a quick command line (CLI), Expenses Control has you covered.

Built with **Python 3**, featuring **SQLite** persistence and **Matplotlib** analytics.

## 🌟 Choose Your Interface

This project provides three distinct ways to manage your money. All interfaces share the same database, so you can switch between them seamlessly.

| Feature | PyQt6 (Power User) | CustomTkinter (Modern) | CLI (Terminal) |
| :--- | :--- | :--- | :--- |
| **Best For** | Heavy data entry, Planning | Dashboarding, Quick Entry | Minimalists, Scripts |
| **Visual Style** | Spreadsheet / Excel-like | Modern / Dark Mode | Text / ASCII Tables |
| **Data Entry** | In-cell editing, Copy/Paste | Form-based | Interactive Prompts |
| **Analytics** | Interactive Charts, Split View | Dashboard w/ Pie & Bar | ASCII Tables |
| **Budgeting** | Matrix (Month x Category) | Matrix (Scrollable) | Basic Set/Get |

### 1. The Power User Suite (PyQt6)
**Run:** `python main_gui_qt.py`
*   **Excel-like Grid:** Copy/Paste support (Ctrl+C/V), dynamic cell editing, and auto-sum rows/columns.
*   **Dual View:** Split screen for Income vs. Expense planning.
*   **Advanced Analytics:** Interactive chart with toggleable series for Budget vs. Actual vs. Income.

### 2. The Modern Dashboard (CustomTkinter)
**Run:** `python main_gui_tk.py`
*   **Sleek UI:** Built with `customtkinter` for a native dark/light mode experience.
*   **Dashboard:** Instant visual summary of the year's performance (Pie & Bar charts).
*   **Simplified Budgeting:** Clean form-based inputs for setting monthly limits.

### 3. The Command Line (CLI)
**Run:** `python main_cli.py`
*   **Fast startup.**
*   **Text-based tables** (via `tabulate`).
*   **Basic plotting** (pop-up window).

---

## 🚀 Common Features
All interfaces support the core functionality:
*   **Expense Tracking:** Log daily expenses with categories and descriptions.
*   **Budgeting:** Set monthly limits per category.
*   **Data Persistence:** Automatic storage in `data/expenses.db` (SQLite).
*   **Legacy Support:** Automatically imports data from `data/expenses.csv` if the database is empty.

## 🛠️ Installation

### Prerequisites
*   Python 3.8+

### Setup
1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    *Dependencies include: `PyQt6`, `customtkinter`, `pandas`, `matplotlib`, `tabulate`.*

## 💾 Database Schema

The application uses SQLite (`data/expenses.db`) with the following structure:

*   **`expenses`**: Stores individual transactions.
    *   `id`: Auto-incrementing primary key.
    *   `date`: YYYY-MM-DD string.
    *   `category`: String (linked to `categories.name`).
    *   `amount`: Real/Float.
    *   `description`: String.
    *   `type`: 'Gasto' (Expense) or 'Ingreso' (Income).
    *   `member`: Optional string for family member name.
*   **`budgets`**: Stores monthly targets.
    *   Composite Key: (`category`, `month`, `year`).
    *   `amount`: Real/Float.
*   **`categories`**: Valid categories to ensure consistency.
    *   `name`: Unique string.
    *   `type`: 'Expense' or 'Income'.

## 📂 Project Structure

```
ExpensesControl/
├── data/                   # Data storage
│   ├── expenses.db         # Primary SQLite Database
│   └── expenses.csv        # Legacy import source
├── src/
│   └── expenses_control/
│       ├── core.py         # Shared Business Logic & DAL
│       ├── cli.py          # CLI Implementation
│       └── gui/
│           ├── qt_app.py   # PyQt6 Implementation (Power User)
│           ├── tk_app.py   # CustomTkinter Implementation (Modern)
│           └── models.py   # Qt Data Models
├── main_gui_qt.py          # Entry point for Qt App
├── main_gui_tk.py          # Entry point for Tk App
├── main_cli.py             # Entry point for CLI
└── requirements.txt        # Dependencies
```

## ⚠️ Project Status

*   **Audit Date:** January 2, 2026
*   **Status:** Active Development.
*   **Known Issues:** 
    *   **Testing:** The project currently lacks automated unit tests (`tests/` is empty). All testing is manual.
    *   **Tk Interface:** While functional, the Tk interface uses a different budgeting paradigm (Entry widgets vs Table) compared to Qt.
