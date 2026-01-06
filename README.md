# Expenses Control System

A versatile personal finance management system offering multiple interfaces to suit your workflow. Whether you prefer a power-user spreadsheet experience (Qt) or a modern web dashboard (Streamlit), Expenses Control has you covered.

Built with **Python 3**, featuring **SQLite** persistence and **Matplotlib/Plotly** analytics.

## 🌟 Choose Your Interface

This project provides two distinct ways to manage your money. Both interfaces share the same database, so you can switch between them seamlessly.

| Feature | PyQt6 (Power User) | Streamlit (Web) |
| :--- | :--- | :--- |
| **Best For** | Heavy data entry, Planning | Browser access, Visualizations |
| **Visual Style** | Spreadsheet / Excel-like | Modern Web / Interactive |
| **Data Entry** | In-cell editing, Copy/Paste | Editable Dataframes |
| **Analytics** | Interactive Charts, Split View | Plotly Interactive Charts |
| **Budgeting** | Matrix (Month x Category) | Matrix (Edit & Save) |

### 1. The Power User Suite (PyQt6)
**Run:** `python main_gui_qt.py`
*   **Excel-like Grid:** Copy/Paste support (Ctrl+C/V), dynamic cell editing, and auto-sum rows/columns.
*   **Dual View:** Split screen for Income vs. Expense planning.
*   **Advanced Analytics:** Interactive chart with toggleable series for Budget vs. Actual vs. Income.

### 2. The Web Application (Streamlit)
**Run:** `streamlit run main_streamlit.py`
*   **Web Accessibility:** Run directly in your browser.
*   **Interactive Analytics:** Powered by `Plotly` for rich, interactive visualizations (Trend lines, Donut charts).
*   **Editable Dataframes:** Bulk edit transactions and budgets directly in the browser.

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
    *Dependencies include: `PyQt6`, `streamlit`, `pandas`, `matplotlib`, `plotly`.*

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
│       └── gui/
│           ├── qt_app.py   # PyQt6 Implementation (Power User)
│           └── models.py   # Qt Data Models
├── main_gui_qt.py          # Entry point for Qt App
├── main_streamlit.py       # Entry point for Web App
└── requirements.txt        # Dependencies
```

## ⚠️ Project Status

*   **Audit Date:** January 5, 2026
*   **Status:** Active Development.
*   **Known Issues:** 
    *   **Testing:** The project currently lacks automated unit tests (`tests/` is empty). All testing is manual.
    *   **Interfaces:** The Qt and Streamlit interfaces are functional and share the same data.