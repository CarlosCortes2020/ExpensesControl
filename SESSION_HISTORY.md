# Development Session History

**Date:** January 2, 2026
**Topic:** System Audit & Documentation Overhaul

Performed a comprehensive audit of the entire codebase to assess project health, feature completeness, and architectural consistency.

---

## 1. System Audit Findings
*   **Architecture:** Confirmed a clean separation of concerns. `core.py` effectively serves as a shared Data Access Layer (DAL) for all three interfaces (CLI, Qt, Tk), using SQLite as the single source of truth.
*   **Interface Status:**
    *   **Qt (PyQt6):** valid, feature-rich, "Pro" interface with Excel-like grid editing and complex charting.
    *   **Tk (CustomTkinter):** valid, "Modern" interface. Surprisingly complete with dashboarding and budget planning, offering a simpler user experience than Qt.
    *   **CLI:** Functional legacy interface.
*   **Critical Gap:** The `tests/` directory is empty. The project currently relies entirely on manual testing.

## 2. Documentation Updates
*   **Goal:** Reflect the multi-interface nature of the application in the public documentation.
*   **Action:** 
    *   Updated `README.md` to showcase both Qt and Tk interfaces as first-class citizens.
    *   Clarified the distinct use cases for each interface (Power User vs. Modern/Simple).
    *   Added a "Project Status" section to transparently report the lack of automated tests.

---

**Date:** January 2, 2026 (Session 2)
**Topic:** Documentation Refinement & Schema Verification

*   **Verified Codebase:** Checked `src/expenses_control/core.py`, `qt_app.py`, and `tk_app.py` to ensure feature lists in `README.md` are accurate.
*   **Schema Documentation:** Added a detailed "Database Schema" section to `README.md` outlining the `expenses`, `budgets`, and `categories` tables, including recent migrations like `type` and `member`.
*   **Comparison Table:** Added a "Choose Your Interface" comparison table to `README.md` to help users decide between Qt, Tk, and CLI.

---

**Date:** January 2, 2026 (Session 3)
**Topic:** Web Interface Integration & Documentation

*   **Web Interface (Streamlit):**
    *   Recognized `main_streamlit.py` as a fully functional 4th interface.
    *   Features include: Interactive Dashboard (Plotly), Editable Dataframes for Transactions and Budgets, and Matrix views for Income/Expenses.
*   **Documentation:**
    *   Updated `README.md` to include **Streamlit** in the interface comparison table.
    *   Added run instructions (`streamlit run main_streamlit.py`).
    *   Updated project structure to include the web entry point.

---

**Date:** December 31, 2025  
**Topic:** Expenses Control Application - GUI & Feature Enhancement

This document summarizes the chronological development steps taken during the session to transform the application from a basic prototype into a fully featured financial tool.

---

## 1. Initial GUI Setup & Grid View
*   **Goal:** Create a "Set Budget" section with a Month x Category grid.
*   **Action:** 
    *   Refactored `core.py` to use SQLite as the primary source of truth.
    *   Created `qt_app.py` with a Tabbed interface.
    *   Implemented `BudgetTableModel` to pivot database data into a 12-month matrix.

## 2. Stability Fixes
*   **Goal:** Fix `AttributeError` regarding status bar updates.
*   **Action:** Adjusted the initialization order in `qt_app.py` to ensure UI elements exist before data loading triggers.

## 3. Financial Trend Analysis
*   **Goal:** Add a chart showing Budget vs Expenses.
*   **Action:** 
    *   Integrated `Matplotlib` into the PyQt window.
    *   Created logic to fetch annual data and plot comparison lines.
    *   Improved table navigation (Enter key editing).

## 4. Excel-Like Interaction (Copy/Paste)
*   **Goal:** Enable copying and pasting data to/from external spreadsheets.
*   **Action:** 
    *   Implemented `copy_selection` and `paste_selection` in `qt_app.py`.
    *   Added parsing logic to handle tab-separated clipboard data and clean currency formatting.
    *   Bound actions to `Ctrl+C` and `Ctrl+V`.

## 5. Income Management & Split View
*   **Goal:** Add an "Income" table separate from expenses and enable column resizing.
*   **Action:** 
    *   Updated Database Schema to support Category Types ('Income', 'Expense').
    *   Updated GUI to use `QSplitter`, displaying "Ingresos" (top) and "Gastos" (bottom).
    *   Added "Ajustar Tamaño" functionality.

## 6. Dynamic Category Creation
*   **Goal:** Create categories by typing in an empty bottom row (like Excel/Notion).
*   **Action:** 
    *   Modified `BudgetTableModel` to render a "phantom row" at `rowCount + 1`.
    *   Implemented logic in `setData` to detect edits in this row and trigger `db_add_category` instantly.

## 7. Interactive Chart Filtering
*   **Goal:** Allow users to choose which trends to view.
*   **Action:** 
    *   Added `QCheckBox` widgets for "Gastos", "Presupuesto", and "Ingresos".
    *   Updated the plotting logic to conditionally render lines based on checkbox state.

## 8. Database Schema Migration
*   **Goal:** Fix `sqlite3.OperationalError: no such column: type`.
*   **Action:** 
    *   Enhanced `init_db` in `core.py`.
    *   Added automatic `ALTER TABLE` commands to inject missing columns (`type`, `member`) into existing databases, ensuring backward compatibility.

## 9. Data Accuracy (Budgeted Income)
*   **Goal:** Ensure the "Income" line in the chart reflects the *table* values (Plan), not just empty real records.
*   **Action:** 
    *   Updated `db_get_analytics_data` to fetch **Budgeted Income** specifically.
    *   Rewired the chart to plot the Budgeted Income stream when the "Ingresos" checkbox is checked.

## 10. Totals Calculation
*   **Goal:** Display Monthly Totals (Top) and Category Totals (Right).
*   **Action:** 
    *   Refactored `BudgetTableModel` indices.
    *   Row 0 is now reserved for **Monthly Totals**.
    *   Column 13 is now reserved for **Category Totals**.
    *   Implemented read-only flags and background styling (Gray) for these summary cells.
    *   Added real-time recalculation logic in the model.