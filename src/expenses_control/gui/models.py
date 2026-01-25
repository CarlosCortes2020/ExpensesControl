import pandas as pd
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QDate
from PyQt6.QtGui import QColor

from .. import core as em

class ExpenseTableModel(QAbstractTableModel):
    def __init__(self, data=None):
        super().__init__()
        # Expected columns from DB: id, Fecha, Categoría, Monto, Descripción, Tipo, Miembro
        self._df = data if data is not None else pd.DataFrame()
        
        # Ensure we have a DF, even if empty
        if self._df.empty:
            self._headers = ["id", "Fecha", "Categoría", "Descripción", "Miembro", "Monto", "Tipo"]
            self._df = pd.DataFrame(columns=self._headers)
        else:
            self._headers = list(self._df.columns)

        # Enforce types where possible
        if 'Monto' in self._df.columns:
            self._df['Monto'] = pd.to_numeric(self._df['Monto'], errors='coerce').fillna(0.0)

    def rowCount(self, parent=QModelIndex()):
        return self._df.shape[0]

    def columnCount(self, parent=QModelIndex()):
        return self._df.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()
        column_name = self._df.columns[col]
        value = self._df.iloc[row, col]

        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            if column_name == "Monto":
                if role == Qt.ItemDataRole.DisplayRole:
                    try:
                        return f"{float(value):,.2f}"
                    except (ValueError, TypeError):
                        return "0.00"
                return str(value)
            return str(value)

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if column_name == "Monto":
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            row = index.row()
            col = index.column()
            column_name = self._df.columns[col]

            # Validation / Type conversion
            if column_name == "Monto":
                try:
                    value = float(value)
                except ValueError:
                    return False
            
            # Update local DF
            self._df.iloc[row, col] = value
            
            # Update DB
            # We need the ID of the row. Assuming 'id' column exists.
            try:
                # Find ID column index or name
                expense_id = self._df.iloc[row]['id']
                em.db_update_expense(expense_id, column_name, value)
            except KeyError:
                print("Error: 'id' column not found, cannot update DB.")

            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])
            return True
        return False

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._df.columns[section]
            if orientation == Qt.Orientation.Vertical:
                return str(section + 1)
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        
        # ID column is not editable
        col_name = self._df.columns[index.column()]
        if col_name == 'id':
            return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
            
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable

    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()
        col_name = self._df.columns[column]
        ascending = (order == Qt.SortOrder.AscendingOrder)
        self._df.sort_values(by=col_name, ascending=ascending, inplace=True)
        self._df.reset_index(drop=True, inplace=True)
        self.layoutChanged.emit()

    # --- Custom Methods ---

    def add_row(self):
        # Insert into DB first to get ID
        date = QDate.currentDate().toString("yyyy-MM-dd")
        cat = "Otros"
        amount = 0.0
        desc = ""
        em.db_add_expense(date, cat, amount, desc)
        
        # Refresh Data
        # For efficiency, we could just fetch the last one, but reloading is safer for sync
        self.refresh_data()

    def remove_rows(self, rows):
        # Rows is a list of row indices
        ids_to_delete = []
        for row_idx in rows:
            try:
                # Use item() to convert numpy types to native Python types
                val = self._df.iloc[row_idx]['id']
                # If val is numpy int, int(val) works.
                ids_to_delete.append(int(val))
            except (KeyError, ValueError, TypeError) as e:
                print(f"Error getting ID for row {row_idx}: {e}")
                pass
        
        for eid in ids_to_delete:
            em.db_delete_expense(eid)
            
        self.refresh_data()

    def refresh_data(self):
        self.beginResetModel()
        self._df = em.db_get_all_expenses_df()
        if 'Monto' in self._df.columns:
            self._df['Monto'] = pd.to_numeric(self._df['Monto'], errors='coerce').fillna(0.0)
        self.endResetModel()

    def get_dataframe(self):
        return self._df

    def get_total_amount(self):
        try:
            return self._df['Monto'].sum()
        except:
            return 0.0

class BudgetTableModel(QAbstractTableModel):
    def __init__(self, year, data_df, category_type="Expense"):
        super().__init__()
        self.year = year
        self.category_type = category_type
        
        self.month_names = em.MONTH_MAP
        
        self.refresh_data_internal(data_df)

    def refresh_data_internal(self, data_df):
        self._df = data_df # Index: Categories, Columns: 1..12 (Integers)
        # Transform for View: Reset index so Category is a column
        self._view_df = self._df.reset_index() 
        # _view_df columns: 'category', 1, 2, ... 12
        
        # Pre-calculate totals for display
        # Columns 1 to 12 are months
        numeric_cols = list(range(1, 13))
        # Ensure numeric columns exist and handle empty DF case
        for col in numeric_cols:
            if col not in self._view_df.columns:
                self._view_df[col] = 0.0
                
        self._monthly_totals = self._view_df[numeric_cols].sum(axis=0)
        self._category_totals = self._view_df[numeric_cols].sum(axis=1)
        self._grand_total = self._monthly_totals.sum()

    def rowCount(self, parent=QModelIndex()):
        # 1 (Totals) + Data Rows + 1 (Phantom)
        return self._view_df.shape[0] + 2

    def columnCount(self, parent=QModelIndex()):
        # Category + 12 Months + 1 Total = 14
        return 14

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()
        
        # --- BACKGROUND COLOR FOR TOTALS ---
        if role == Qt.ItemDataRole.BackgroundRole:
            # Totals Row (0) or Total Column (13)
            if row == 0 or col == 13:
                # Use a semi-transparent gray that works in light and dark
                return QColor(128, 128, 128, 40) 
            return None
        
        # --- TEXT COLOR AND FONT FOR TOTALS ---
        if role == Qt.ItemDataRole.ForegroundRole:
            if row == 0 or col == 13:
                # Keep it neutral but ensure it's not too light/dark
                return None # Let the system decide based on background
            return None

        # --- ROW 0: MONTHLY TOTALS ---
        if row == 0:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                if col == 0:
                    return "TOTALES"
                elif 1 <= col <= 12:
                    val = self._monthly_totals.get(col, 0.0)
                    return f"{float(val):,.2f}"
                elif col == 13:
                    return f"{float(self._grand_total):,.2f}"
            return None

        # --- ROW N+1: PHANTOM ROW ---
        phantom_row_idx = self._view_df.shape[0] + 1
        if row == phantom_row_idx:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return ""
            return None

        # --- DATA ROWS (Shifted by 1) ---
        df_row = row - 1
        
        # Check bounds just in case
        if df_row >= self._view_df.shape[0]:
             return None 

        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            if col == 0:
                return str(self._view_df.iloc[df_row, 0]) # Category Name
            elif col == 13:
                # Row Total
                val = self._category_totals.iloc[df_row]
                if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                    return f"{float(val):,.2f}"
                return str(val)
            else:
                # Monthly Value
                val = self._view_df.iloc[df_row, col]
                if role == Qt.ItemDataRole.DisplayRole:
                    return f"{float(val):,.2f}"
                return str(val)

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col > 0:
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if section == 0:
                    return "Categoría"
                elif 1 <= section <= 12:
                    try:
                        return self.month_names.get(section, str(section))
                    except:
                        return str(section)
                elif section == 13:
                    return "Total Anual"
            if orientation == Qt.Orientation.Vertical:
                if section == 0:
                    return "Σ"
                return str(section)
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        
        row = index.row()
        col = index.column()
        
        # Row 0 (Totals) is Read-only
        if row == 0:
            return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
            
        # Col 13 (Total) is Read-only
        if col == 13:
            return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled

        # Phantom Row
        phantom_row_idx = self._view_df.shape[0] + 1
        if row == phantom_row_idx:
            # Only Name editable
            if col == 0:
                return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable
            else:
                return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
                
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
            
        row = index.row()
        col = index.column()
        
        # Prevent editing Totals
        if row == 0 or col == 13:
            return False
            
        # Phantom Row: Create Category
        phantom_row_idx = self._view_df.shape[0] + 1
        if row == phantom_row_idx:
            if col == 0:
                new_name = value.strip()
                if not new_name: return False
                
                # Attempt to create
                if em.db_add_category(new_name, ctype=self.category_type):
                    self.refresh_data()
                    return True
            return False
        
        # Standard Row: Update (Shift index back)
        df_row = row - 1
        current_category = self._view_df.iloc[df_row, 0]
        
        if col == 0: # Rename Category
            new_name = value.strip()
            if not new_name: return False
            if new_name == current_category: return False
            
            success, msg = em.db_rename_category(current_category, new_name)
            if success:
                self._view_df.iloc[df_row, 0] = new_name
                self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
                return True
            else:
                print(f"Rename failed: {msg}")
                return False
        else: # Update Budget Amount
            try:
                amount = float(value)
            except ValueError:
                return False
            
            # Map column index to dataframe column name (which are 1..12 ints)
            # col 1 -> month 1
            # But wait, view_df columns are ['category', 1, 2... 12]
            # so col index corresponds directly to month number
            month = col
            
            em.db_set_budget(current_category, month, self.year, amount)
            self._view_df.iloc[df_row, col] = amount
            
            # Recalculate Totals locally to update view without full DB reload
            self._monthly_totals[month] = self._view_df[month].sum()
            self._category_totals.iloc[df_row] = self._view_df.iloc[df_row, 1:].sum()
            self._grand_total = self._monthly_totals.sum()
            
            # Emit change for this cell
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
            
            # Emit changes for Totals Row and Column
            # Total for this Month (Row 0, this Col)
            idx_month_total = self.index(0, col)
            self.dataChanged.emit(idx_month_total, idx_month_total, [Qt.ItemDataRole.DisplayRole])
            
            # Total for this Category (this Row, Col 13)
            idx_cat_total = self.index(row, 13)
            self.dataChanged.emit(idx_cat_total, idx_cat_total, [Qt.ItemDataRole.DisplayRole])
            
            # Grand Total (Row 0, Col 13)
            idx_grand_total = self.index(0, 13)
            self.dataChanged.emit(idx_grand_total, idx_grand_total, [Qt.ItemDataRole.DisplayRole])
            
            return True
        return False
        
    def add_category(self, name):
        if em.db_add_category(name, ctype=self.category_type):
            self.refresh_data()
            return True
        return False
        
    def refresh_data(self):
        self.beginResetModel()
        self._df = em.db_get_budget_matrix(self.year, ctype=self.category_type)
        self.endResetModel()

class RealExpenseTableModel(BudgetTableModel):
    def __init__(self, year, data_df):
        # Category Type is 'Expense' for real expenses
        super().__init__(year, data_df, category_type="Expense")

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled

    def rowCount(self, parent=QModelIndex()):
        # No phantom row. Just totals (1) + Data Rows
        return self._view_df.shape[0] + 1
    
    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        return False
        
    def refresh_data(self):
        self.beginResetModel()
        self._df = em.db_get_real_expenses_matrix(self.year)
        self.endResetModel()

class RealIncomeTableModel(RealExpenseTableModel):
    def __init__(self, year, data_df):
        # Category Type is 'Income' for real income
        # We inherit from RealExpenseTableModel which inherits from BudgetTableModel
        # But we need to init BudgetTableModel with 'Income'
        super(BudgetTableModel, self).__init__() 
        
        self.year = year
        self.category_type = "Income"
        self.month_names = em.MONTH_MAP
        self.refresh_data_internal(data_df)

    def refresh_data(self):
        self.beginResetModel()
        self._df = em.db_get_real_income_matrix(self.year)
        self.refresh_data_internal(self._df)
        self.endResetModel()

class ComparisonTableModel(BudgetTableModel):
    def __init__(self, year, plan_df, real_df, mode="Expense"):
        # We don't call super().__init__ directly because we need to process data first
        # But we need to set up basics
        super(BudgetTableModel, self).__init__()
        self.year = year
        self.mode = mode
        self.month_names = em.MONTH_MAP
        
        # Align DataFrames
        # Ensure they have same index and columns
        common_index = plan_df.index.union(real_df.index)
        plan_aligned = plan_df.reindex(common_index).fillna(0.0)
        real_aligned = real_df.reindex(common_index).fillna(0.0)
        
        # Ensure columns 1..12
        for m in range(1, 13):
            if m not in plan_aligned.columns: plan_aligned[m] = 0.0
            if m not in real_aligned.columns: real_aligned[m] = 0.0
            
        plan_aligned = plan_aligned[range(1, 13)]
        real_aligned = real_aligned[range(1, 13)]
        
        if mode == "Expense":
            # Difference = Budget - Real (Positive is under budget)
            self.diff_df = plan_aligned - real_aligned
        else:
            # Difference = Real - Budget (Positive is over budget)
            self.diff_df = real_aligned - plan_aligned
            
        self.refresh_data_internal(self.diff_df)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
            
        # Get standard data first
        value = super().data(index, role)
        
        # Foreground Color Logic
        if role == Qt.ItemDataRole.ForegroundRole:
            row = index.row()
            col = index.column()
            
            # Skip Headers/Totals rows/cols for coloring if desired, 
            # OR color them too. Let's color them too as it's useful info.
            
            # Get numerical value
            try:
                # We need the raw value, not the string formatted one
                # super().data returns string for DisplayRole
                # Let's peek at underlying dataframe directly for efficiency
                
                val = 0.0
                if row == 0: # Totals Row
                    if 1 <= col <= 12:
                        val = self._monthly_totals.get(col, 0.0)
                    elif col == 13:
                        val = self._grand_total
                elif 1 <= row <= self._view_df.shape[0]: # Data Row
                    df_row = row - 1
                    if col == 13: # Row Total
                        val = self._category_totals.iloc[df_row]
                    elif 1 <= col <= 12: # Monthly Value
                        val = self._view_df.iloc[df_row, col]
                
                # Apply Color
                if val > 0:
                    return QColor("green")
                elif val < 0:
                    return QColor("red")
                # Zero is default text color
                
            except Exception:
                pass
                
        return value

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled

    def rowCount(self, parent=QModelIndex()):
        # Totals + Data Rows
        return self._view_df.shape[0] + 1

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        return False
        
    def refresh_data(self):
        # Data is static for the life of this model instance usually, 
        # or we need to re-fetch both plan/real.
        # For simplicity, we assume the parent widget recreates the model on refresh.
        pass