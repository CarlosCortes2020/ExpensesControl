import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTableView, QVBoxLayout, 
                             QWidget, QHeaderView, QMessageBox, QDateEdit, 
                             QStyledItemDelegate, QComboBox, QFileDialog, QLabel,
                             QTabWidget, QSpinBox, QHBoxLayout, QPushButton, QInputDialog,
                             QAbstractItemView, QSplitter, QGroupBox, QCheckBox, QDialog,
                             QFormLayout, QLineEdit, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QAction, QKeySequence, QShortcut

# Matplotlib integration
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from .. import core as em
from .models import ExpenseTableModel, BudgetTableModel

# --- Delegates ---

class DateDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QDateEdit(parent)
        editor.setDisplayFormat("yyyy-MM-dd")
        editor.setCalendarPopup(True)
        return editor

    def setEditorData(self, editor, index):
        val = index.model().data(index, Qt.ItemDataRole.EditRole)
        qdate = QDate.fromString(val, "yyyy-MM-dd")
        if qdate.isValid():
            editor.setDate(qdate)
        else:
            editor.setDate(QDate.currentDate())

    def setModelData(self, editor, model, index):
        model.setData(index, editor.date().toString("yyyy-MM-dd"), Qt.ItemDataRole.EditRole)

class CategoryDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        categories = em.db_get_categories()
        editor.addItems(categories)
        editor.setEditable(True)  # Allow free text
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        editor.setCurrentText(value)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)

class TypeDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(["Gasto", "Ingreso"])
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        editor.setCurrentText(value)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)

# --- Dialogs ---

class AddExpenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar Nuevo Movimiento")
        self.resize(400, 300)
        self.layout = QFormLayout(self)
        
        # Fields
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setCalendarPopup(True)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Gasto", "Ingreso"])
        self.type_combo.currentTextChanged.connect(self.update_categories)
        
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 1000000.00)
        self.amount_spin.setPrefix("$")
        self.amount_spin.setDecimals(2)
        
        self.desc_edit = QLineEdit()
        self.member_edit = QLineEdit()
        
        # Layout
        self.layout.addRow("Fecha:", self.date_edit)
        self.layout.addRow("Tipo:", self.type_combo)
        self.layout.addRow("Categoría:", self.category_combo)
        self.layout.addRow("Monto:", self.amount_spin)
        self.layout.addRow("Descripción:", self.desc_edit)
        self.layout.addRow("Miembro (Opcional):", self.member_edit)
        
        # Buttons
        self.btn_box = QHBoxLayout()
        self.btn_save = QPushButton("Guardar")
        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_box.addWidget(self.btn_save)
        self.btn_box.addWidget(self.btn_cancel)
        self.layout.addRow(self.btn_box)
        
        # Init Categories
        self.update_categories(self.type_combo.currentText())

    def update_categories(self, type_text):
        self.category_combo.clear()
        # Map "Gasto" -> "Expense", "Ingreso" -> "Income" for DB query
        db_type = "Expense" if type_text == "Gasto" else "Income"
        categories = em.db_get_categories(db_type)
        self.category_combo.addItems(categories)

    def get_data(self):
        return {
            'date': self.date_edit.date().toString("yyyy-MM-dd"),
            'type': self.type_combo.currentText(),
            'category': self.category_combo.currentText(),
            'amount': self.amount_spin.value(),
            'description': self.desc_edit.text(),
            'member': self.member_edit.text()
        }

# --- Widgets ---

class ExpensesWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        # self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        toolbar = QHBoxLayout()
        self.btn_add = QPushButton("+ Nuevo Registro")
        self.btn_add.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 5px;")
        self.btn_add.clicked.connect(self.open_add_dialog)
        
        self.btn_del = QPushButton("Borrar Seleccionados")
        self.btn_del.clicked.connect(self.delete_rows)
        
        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_del)
        toolbar.addStretch()
        
        self.layout.addLayout(toolbar)
        
        self.table_view = QTableView()
        self.layout.addWidget(self.table_view)
        
        # Status Bar reference (can be set by Main Window)
        self.status_bar_updater = None

        # Load Data
        self.refresh_data()

    def refresh_data(self):
        self.df = em.db_get_all_expenses_df()
        self.model = ExpenseTableModel(self.df)
        self.table_view.setModel(self.model)
        self.setup_table()
        
        if self.status_bar_updater:
            self.model.dataChanged.connect(self.status_bar_updater)
            self.model.rowsInserted.connect(self.status_bar_updater)
            self.model.rowsRemoved.connect(self.status_bar_updater)
            self.status_bar_updater()

    def setup_table(self):
        # Delegates
        self.table_view.setItemDelegateForColumn(1, DateDelegate(self.table_view)) # Date is col 1
        self.table_view.setItemDelegateForColumn(2, CategoryDelegate(self.table_view)) # Category is col 2
        # Type is likely col 5 or 6 depending on schema.
        # Check model headers: id, Fecha, Categoría, Descripción, Miembro, Monto, Tipo
        # id=0, Fecha=1, Cat=2, Desc=3, Mem=4, Monto=5, Tipo=6
        self.table_view.setItemDelegateForColumn(6, TypeDelegate(self.table_view))

        # Styling
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSortingEnabled(True)
        self.table_view.verticalHeader().setVisible(True)
        self.table_view.setColumnHidden(0, True) # Hide ID column
        
        # Column sizing
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        self.table_view.setColumnWidth(1, 100) # Date
        self.table_view.setColumnWidth(2, 150) # Category
        self.table_view.setColumnWidth(3, 250) # Description
        self.table_view.setColumnWidth(4, 120) # Member
        self.table_view.setColumnWidth(5, 100) # Amount
        self.table_view.setColumnWidth(6, 100) # Type

    def open_add_dialog(self):
        dialog = AddExpenseDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            # db_add_expense(date, category, amount, description, expense_type="Gasto", member="")
            em.db_add_expense(
                data['date'],
                data['category'],
                data['amount'],
                data['description'],
                data['type'],
                data['member']
            )
            self.refresh_data()
            
            # Auto-scroll to top to see new entry (since we order by Date DESC usually)
            self.table_view.scrollToTop()

    def delete_rows(self):
        selection = self.table_view.selectionModel()
        if not selection.hasSelection():
            return
        
        rows = sorted(set(index.row() for index in selection.selectedRows()), reverse=True)
        if not rows:
            QMessageBox.warning(self, "Aviso", "Seleccione filas completas para borrar.")
            return

        confirm = QMessageBox.question(self, "Confirmar", f"¿Borrar {len(rows)} registro(s)?", 
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            self.model.remove_rows(rows)

class BudgetWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Top Bar
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Año:"))
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2000, 2100)
        self.year_spin.setValue(QDate.currentDate().year())
        self.year_spin.valueChanged.connect(self.refresh_data)
        top_bar.addWidget(self.year_spin)
        top_bar.addStretch()
        
        self.btn_resize = QPushButton("Ajustar Tamaño")
        self.btn_resize.clicked.connect(self.resize_tables)
        top_bar.addWidget(self.btn_resize)
        
        self.layout.addLayout(top_bar)
        
        # Splitter for Income/Expenses Tables
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.layout.addWidget(splitter)
        
        # Income Table
        income_group = QGroupBox("Ingresos")
        income_layout = QVBoxLayout(income_group)
        self.income_table = QTableView()
        income_layout.addWidget(self.income_table)
        splitter.addWidget(income_group)
        
        # Expense Table
        expense_group = QGroupBox("Gastos")
        expense_layout = QVBoxLayout(expense_group)
        self.expense_table = QTableView()
        expense_layout.addWidget(self.expense_table)
        splitter.addWidget(expense_group)
        
        # Shortcuts (Bind to window or specific widgets)
        self.setup_shortcuts(self.income_table)
        self.setup_shortcuts(self.expense_table)

        # Chart Controls
        chart_controls = QHBoxLayout()
        self.chk_expenses = QCheckBox("Gastos")
        self.chk_expenses.setChecked(True)
        self.chk_expenses.stateChanged.connect(self.update_chart)
        chart_controls.addWidget(self.chk_expenses)
        
        self.chk_budget = QCheckBox("Presupuesto")
        self.chk_budget.setChecked(True)
        self.chk_budget.stateChanged.connect(self.update_chart)
        chart_controls.addWidget(self.chk_budget)

        self.chk_income = QCheckBox("Ingresos")
        self.chk_income.setChecked(True)
        self.chk_income.stateChanged.connect(self.update_chart)
        chart_controls.addWidget(self.chk_income)
        
        chart_controls.addStretch()
        self.layout.addLayout(chart_controls)

        # Chart
        self.figure = Figure(figsize=(5, 3), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        
        self.refresh_data()

    def setup_shortcuts(self, table_view):
        copy_shortcut = QShortcut(QKeySequence.StandardKey.Copy, table_view, context=Qt.ShortcutContext.WidgetWithChildrenShortcut)
        copy_shortcut.activated.connect(lambda: self.copy_selection(table_view))
        
        paste_shortcut = QShortcut(QKeySequence.StandardKey.Paste, table_view, context=Qt.ShortcutContext.WidgetWithChildrenShortcut)
        paste_shortcut.activated.connect(lambda: self.paste_selection(table_view))

    def refresh_data(self):
        year = self.year_spin.value()
        
        # Update Income Table
        df_income = em.db_get_budget_matrix(year, ctype='Income')
        self.income_model = BudgetTableModel(year, df_income, category_type="Income")
        self.income_table.setModel(self.income_model)
        self.income_model.dataChanged.connect(self.update_chart)
        self.setup_table_view(self.income_table)
        
        # Update Expense Table
        df_expense = em.db_get_budget_matrix(year, ctype='Expense')
        self.expense_model = BudgetTableModel(year, df_expense, category_type="Expense")
        self.expense_table.setModel(self.expense_model)
        self.expense_model.dataChanged.connect(self.update_chart)
        self.setup_table_view(self.expense_table)
        
        # Update Chart
        self.update_chart()
        
        # Auto resize
        self.resize_tables()

    def setup_table_view(self, table_view):
        table_view.setAlternatingRowColors(True)
        table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectItems)
        table_view.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked | 
            QAbstractItemView.EditTrigger.AnyKeyPressed |
            QAbstractItemView.EditTrigger.EditKeyPressed
        )

    def resize_tables(self):
        for tv in [self.income_table, self.expense_table]:
            tv.resizeColumnsToContents()
            tv.resizeRowsToContents()

    def update_chart(self):
        year = self.year_spin.value()
        
        # Fetch data
        df_expenses, df_income, df_budget_expenses, df_budget_income = em.db_get_analytics_data(year)
        analysis = em.process_monthly_summary(df_expenses, df_income, df_budget_expenses, df_budget_income)
        
        # Clear and Plot
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        x = range(len(months))
        
        # Plot Lines based on checkboxes
        if self.chk_budget.isChecked():
            ax.plot(x, analysis['budget_amount'], label='Presupuesto Gastos', marker='o', linestyle='--', color='green')
        
        if self.chk_expenses.isChecked():
            ax.plot(x, analysis['expense_amount'], label='Gastos Reales', marker='s', linestyle='-', color='red')
            
        if self.chk_income.isChecked():
             # User requested "table values" which are BUDGETED Income
             ax.plot(x, analysis['budget_income_amount'], label='Presupuesto Ingresos', marker='^', linestyle='--', color='blue')
             # Optional: Show real income too?
             # ax.plot(x, analysis['income_amount'], label='Ingresos Reales', marker='.', linestyle=':', color='cyan')
        
        ax.set_xticks(x)
        ax.set_xticklabels(months)
        ax.set_title(f"Análisis Financiero {year}")
        ax.set_ylabel("Monto ($)")
        ax.legend()
        ax.grid(True, linestyle=':', alpha=0.6)
        
        self.canvas.draw()

    def add_category(self, ctype):
        title = f"Nueva Categoría ({'Ingreso' if ctype == 'Income' else 'Gasto'})"
        name, ok = QInputDialog.getText(self, title, "Nombre:")
        if ok and name:
            if em.db_add_category(name, ctype=ctype):
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Error", "No se pudo crear (quizás ya existe).")

    def copy_selection(self, table_view):
        selection = table_view.selectionModel()
        indexes = selection.selectedIndexes()
        if not indexes: return

        model = table_view.model()
        indexes.sort(key=lambda x: (x.row(), x.column()))
        
        rows = sorted(list(set(index.row() for index in indexes)))
        cols = sorted(list(set(index.column() for index in indexes)))
        
        text_table = []
        for r in rows:
            row_data = []
            for c in cols:
                idx = model.index(r, c)
                if idx in indexes:
                    val = model.data(idx, Qt.ItemDataRole.EditRole)
                    if val is None: val = ""
                    row_data.append(str(val))
                else:
                    row_data.append("")
            text_table.append("\t".join(row_data))
        
        QApplication.clipboard().setText("\n".join(text_table))

    def paste_selection(self, table_view):
        text = QApplication.clipboard().text()
        if not text: return

        model = table_view.model()
        selection = table_view.selectionModel()
        indexes = selection.selectedIndexes()
        if not indexes: return

        indexes.sort(key=lambda x: (x.row(), x.column()))
        start_row = indexes[0].row()
        start_col = indexes[0].column()

        rows_data = text.split('\n')
        for r_offset, row_text in enumerate(rows_data):
            if not row_text: continue
            cols_data = row_text.split('\t')
            for c_offset, cell_data in enumerate(cols_data):
                r = start_row + r_offset
                c = start_col + c_offset
                if r >= model.rowCount() or c >= model.columnCount(): continue
                
                clean_val = cell_data.replace('$', '').replace(',', '').strip()
                model.setData(model.index(r, c), clean_val, Qt.ItemDataRole.EditRole)

# --- Main Window ---

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control de Gastos & Presupuesto")
        self.resize(1200, 800)
        
        # Init DB
        em.init_db()
        
        # Central Widget & Tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self.expenses_tab = ExpensesWidget()
        self.budget_tab = BudgetWidget()
        
        self.tabs.addTab(self.expenses_tab, "Gastos")
        self.tabs.addTab(self.budget_tab, "Presupuesto")
        
        # Status Bar
        self.status_label = QLabel()
        self.statusBar().addWidget(self.status_label)
        
        # Link status bar to expenses
        self.expenses_tab.status_bar_updater = self.update_status
        self.expenses_tab.refresh_data() # Re-hook signals
        self.update_status()

        # Menus
        self.create_menus()

    def create_menus(self):
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&Archivo")
        
        exit_action = QAction("&Salir", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = menu_bar.addMenu("&Edición")
        
        add_row_action = QAction("Agregar Gasto", self)
        add_row_action.setShortcut(QKeySequence.StandardKey.New)
        add_row_action.triggered.connect(self.add_expense_row)
        edit_menu.addAction(add_row_action)

        del_row_action = QAction("Borrar Gasto(s)", self)
        del_row_action.setShortcut(QKeySequence.StandardKey.Delete)
        del_row_action.triggered.connect(self.delete_expense_rows)
        edit_menu.addAction(del_row_action)

        # View Menu
        view_menu = menu_bar.addMenu("&Ver")
        totals_action = QAction("Ver Totales (Popup)", self)
        totals_action.triggered.connect(self.show_totals)
        view_menu.addAction(totals_action)

    def add_expense_row(self):
        self.tabs.setCurrentWidget(self.expenses_tab)
        # self.expenses_tab.model.add_row() # OLD
        # Redirect to dialog
        self.expenses_tab.open_add_dialog()

    def delete_expense_rows(self):
        if self.tabs.currentWidget() != self.expenses_tab:
            QMessageBox.information(self, "Info", "Cambie a la pestaña 'Gastos' para borrar registros.")
            return
        # Redirect to widget method
        self.expenses_tab.delete_rows()

    def show_totals(self):
        if self.tabs.currentWidget() == self.expenses_tab:
            total = self.expenses_tab.model.get_total_amount()
            count = self.expenses_tab.model.rowCount()
            QMessageBox.information(self, "Totales", f"Registros: {count}\nMonto Total: ${total:,.2f}")
        else:
             QMessageBox.information(self, "Info", "Totales disponibles solo en pestaña Gastos.")

    def update_status(self):
        total = self.expenses_tab.model.get_total_amount()
        count = self.expenses_tab.model.rowCount()
        self.status_label.setText(f"Gastos: {count} registros | Total: ${total:,.2f}")

    def closeEvent(self, event):
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
