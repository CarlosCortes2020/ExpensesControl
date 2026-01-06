import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTableView, QVBoxLayout, 
                             QWidget, QHeaderView, QMessageBox, QDateEdit, 
                             QStyledItemDelegate, QComboBox, QFileDialog, QLabel,
                             QTabWidget, QSpinBox, QHBoxLayout, QPushButton, QInputDialog,
                             QAbstractItemView, QSplitter, QGroupBox, QCheckBox, QDialog,
                             QFormLayout, QLineEdit, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence, QShortcut, QColor, QPalette

# Matplotlib integration
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from .. import core as em
from .models import ExpenseTableModel, BudgetTableModel, RealExpenseTableModel, RealIncomeTableModel

# --- CHART STYLING ---

class ChartStyler:
    # Professional Palette (Flat Design)
    COLOR_BUDGET = "#34495E" # Navy Blue / Charcoal
    COLOR_REAL_EXP = "#E74C3C" # Alizarin Red (Elegant)
    COLOR_INCOME = "#27AE60" # Nephritis Green
    COLOR_TEXT_LIGHT = "#2c3e50"
    COLOR_TEXT_DARK = "#ecf0f1"
    
    @staticmethod
    def style_axis(ax, is_dark=False):
        # Remove top and right spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Color spines and ticks based on theme
        text_color = ChartStyler.COLOR_TEXT_DARK if is_dark else ChartStyler.COLOR_TEXT_LIGHT
        
        ax.spines['bottom'].set_color(text_color)
        ax.spines['left'].set_color(text_color)
        ax.tick_params(axis='x', colors=text_color)
        ax.tick_params(axis='y', colors=text_color)
        ax.yaxis.label.set_color(text_color)
        ax.xaxis.label.set_color(text_color)
        ax.title.set_color(text_color)
        
        # Minimalist Grid (Horizontal only)
        ax.grid(axis='y', linestyle='--', alpha=0.3, color=text_color)
        ax.grid(axis='x', visible=False) # Disable vertical grid

    @staticmethod
    def add_value_labels(ax, is_dark=False):
        """Add value labels above bars."""
        text_color = ChartStyler.COLOR_TEXT_DARK if is_dark else ChartStyler.COLOR_TEXT_LIGHT
        
        for rect in ax.patches:
            height = rect.get_height()
            if height > 0:
                ax.annotate(f'${height:,.0f}',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom',
                            color=text_color, fontsize=8, fontweight='bold')

# --- THEMES ---

class ThemeManager:
    LIGHT_THEME = """
        QMainWindow, QWidget { background-color: #f5f5f5; color: #000000; }
        QTabWidget::pane { border: 1px solid #c0c0c0; background: #ffffff; }
        QTabBar::tab {
            background: #e1e1e1;
            color: #333;
            border: 1px solid #acacac;
            padding: 8px 12px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background: #ffffff;
            border-bottom-color: #ffffff;
            font-weight: bold;
        }
        QTableView {
            background-color: #ffffff;
            alternate-background-color: #f9f9f9;
            gridline-color: #d0d0d0;
            selection-background-color: #a6d8ff;
            selection-color: #000000;
            color: #000000;
        }
        QHeaderView::section {
            background-color: #e0e0e0;
            color: #000000;
            padding: 4px;
            border: 1px solid #c0c0c0;
            font-weight: bold;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #aaa;
            border-radius: 6px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QLabel, QCheckBox, QRadioButton { color: #000000; }
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #c0c0c0;
            padding: 2px;
        }
        QPushButton {
            background-color: #e0e0e0;
            border: 1px solid #c0c0c0;
            padding: 4px 8px;
            border-radius: 3px;
        }
        QPushButton:hover { background-color: #d0d0d0; }
    """

    DARK_THEME = """
        QMainWindow, QWidget { background-color: #2b2b2b; color: #ffffff; }
        QTabWidget::pane { border: 1px solid #444; background: #333; }
        QTabBar::tab {
            background: #3c3c3c;
            color: #bbb;
            border: 1px solid #444;
            padding: 8px 12px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background: #333;
            color: #fff;
            border-bottom-color: #333;
            font-weight: bold;
        }
        QTableView {
            background-color: #333333;
            alternate-background-color: #3a3a3a;
            gridline-color: #555555;
            selection-background-color: #3d5afe;
            selection-color: #ffffff;
            color: #ffffff;
        }
        QHeaderView::section {
            background-color: #444444;
            color: #ffffff;
            padding: 4px;
            border: 1px solid #555;
            font-weight: bold;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #555;
            border-radius: 6px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QLabel, QCheckBox, QRadioButton { color: #ffffff; }
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {
            background-color: #444;
            color: #ffffff;
            border: 1px solid #555;
            padding: 2px;
        }
        QPushButton {
            background-color: #444;
            color: #fff;
            border: 1px solid #555;
            padding: 4px 8px;
            border-radius: 3px;
        }
        QPushButton:hover { background-color: #555; }
    """

    def __init__(self):
        self.is_dark = False

    def toggle(self):
        self.is_dark = not self.is_dark
        return self.DARK_THEME if self.is_dark else self.LIGHT_THEME

    def get_mpl_params(self):
        if self.is_dark:
            return {
                'figure.facecolor': '#2b2b2b',
                'axes.facecolor': '#2b2b2b',
                'axes.edgecolor': 'white',
                'axes.labelcolor': 'white',
                'xtick.color': 'white',
                'ytick.color': 'white',
                'text.color': 'white',
                'grid.color': '#555555',
                'legend.facecolor': '#333333',
                'legend.edgecolor': '#555555'
            }
        else:
            return {
                'figure.facecolor': '#f5f5f5',
                'axes.facecolor': '#f5f5f5',
                'axes.edgecolor': 'black',
                'axes.labelcolor': 'black',
                'xtick.color': 'black',
                'ytick.color': 'black',
                'text.color': 'black',
                'grid.color': '#d0d0d0',
                'legend.facecolor': '#ffffff',
                'legend.edgecolor': '#cccccc'
            }

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
        self.resize(400, 350)
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
        
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(em.DEFAULT_PAYMENT_METHODS)
        
        # Layout
        self.layout.addRow("Fecha:", self.date_edit)
        self.layout.addRow("Tipo:", self.type_combo)
        self.layout.addRow("Categoría:", self.category_combo)
        self.layout.addRow("Monto:", self.amount_spin)
        self.layout.addRow("Método Pago:", self.payment_combo)
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
            'member': self.member_edit.text(),
            'payment_method': self.payment_combo.currentText()
        }

class IncomeWidget(QWidget):
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Controls (Year, Resize)
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

        # Vertical Splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.layout.addWidget(splitter)

        # 1. Planned Income (Budget)
        self.plan_group = QGroupBox("Ingresos Planificados (Presupuesto)")
        plan_layout = QVBoxLayout(self.plan_group)
        self.plan_table = QTableView()
        plan_layout.addWidget(self.plan_table)
        splitter.addWidget(self.plan_group)

        # 2. Real Income (Executed)
        self.real_group = QGroupBox("Ingresos Reales (Ejecutado)")
        real_layout = QVBoxLayout(self.real_group)
        self.real_table = QTableView()
        real_layout.addWidget(self.real_table)
        splitter.addWidget(self.real_group)

        # Shortcuts
        self.setup_shortcuts(self.plan_table)
        self.setup_shortcuts(self.real_table)
        
        # Initial Data
        self.refresh_data()

    def refresh_data(self):
        year = self.year_spin.value()
        
        # Planned
        df_plan = em.db_get_budget_matrix(year, ctype='Income')
        self.plan_model = BudgetTableModel(year, df_plan, category_type="Income")
        self.plan_table.setModel(self.plan_model)
        self.plan_model.dataChanged.connect(lambda: self.data_changed.emit())
        self.setup_table_view(self.plan_table)
        
        # Real
        df_real = em.db_get_real_income_matrix(year)
        self.real_model = RealIncomeTableModel(year, df_real)
        self.real_table.setModel(self.real_model)
        self.setup_table_view(self.real_table)
        
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
        for tv in [self.plan_table, self.real_table]:
            tv.resizeColumnsToContents()
            tv.resizeRowsToContents()
            
    def setup_shortcuts(self, table_view):
        copy_shortcut = QShortcut(QKeySequence.StandardKey.Copy, table_view, context=Qt.ShortcutContext.WidgetWithChildrenShortcut)
        copy_shortcut.activated.connect(lambda: self.copy_selection(table_view))
        paste_shortcut = QShortcut(QKeySequence.StandardKey.Paste, table_view, context=Qt.ShortcutContext.WidgetWithChildrenShortcut)
        paste_shortcut.activated.connect(lambda: self.paste_selection(table_view))

    def copy_selection(self, table_view):
        # ... (Duplicate logic from BudgetWidget, maybe refactor later into mixin or helper)
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
    
    def update_groupbox_styles(self, is_dark):
        if is_dark:
            bg_alpha = "rgba(255, 255, 255, 0.05)"
            plan_border = "#66bb6a"
            plan_text = "#81c784"
            real_border = "#81c784"
            real_text = "#a5d6a7"
        else:
            bg_alpha = "rgba(0, 0, 0, 0.02)"
            plan_border = "#388E3C"
            plan_text = "#2E7D32"
            real_border = "#2E7D32"
            real_text = "#1B5E20"

        self._apply_style(self.plan_group, plan_border, plan_text, bg_alpha)
        self._apply_style(self.real_group, real_border, real_text, bg_alpha)

    def _apply_style(self, group, border, text_col, bg_alpha):
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {border};
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 10px;
                background-color: {bg_alpha};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {text_col};
            }}
        """)

# --- Widgets ---

class ExpensesWidget(QWidget):
    data_changed = pyqtSignal()

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
        self.table_view.setItemDelegateForColumn(6, TypeDelegate(self.table_view))
        
        # Payment Method Delegate
        payment_delegate = QStyledItemDelegate(self.table_view)
        def create_payment_editor(parent, option, index):
            editor = QComboBox(parent)
            editor.addItems(em.DEFAULT_PAYMENT_METHODS)
            return editor
        payment_delegate.createEditor = create_payment_editor
        self.table_view.setItemDelegateForColumn(7, payment_delegate)

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
        self.table_view.setColumnWidth(3, 200) # Description
        self.table_view.setColumnWidth(4, 100) # Member
        self.table_view.setColumnWidth(5, 100) # Amount
        self.table_view.setColumnWidth(6, 100) # Type
        self.table_view.setColumnWidth(7, 150) # Payment Method

    def open_add_dialog(self):
        dialog = AddExpenseDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            em.db_add_expense(
                data['date'],
                data['category'],
                data['amount'],
                data['description'],
                data['type'],
                data['member'],
                data['payment_method']
            )
            self.refresh_data()
            self.data_changed.emit()
            self.table_view.scrollToTop()

    def delete_rows(self):
        selection = self.table_view.selectionModel()
        if not selection.hasSelection():
            return
        
        indexes = selection.selectedIndexes()
        rows = sorted(list(set(index.row() for index in indexes)), reverse=True)
        
        if not rows:
            return

        confirm = QMessageBox.question(self, "Confirmar", f"¿Borrar {len(rows)} registro(s)?", 
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            self.model.remove_rows(rows)
            self.data_changed.emit()

class ExpenseAnalysisWidget(QWidget):
    data_changed = pyqtSignal()

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
        
        # Vertical Splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.layout.addWidget(splitter)
        
        # 1. Planned Expenses (Budget)
        self.plan_group = QGroupBox("Gastos Planificados (Presupuesto)")
        plan_layout = QVBoxLayout(self.plan_group)
        self.plan_table = QTableView()
        plan_layout.addWidget(self.plan_table)
        splitter.addWidget(self.plan_group)

        # 2. Real Expenses (Executed)
        self.real_group = QGroupBox("Gastos Reales (Ejecutado)")
        real_layout = QVBoxLayout(self.real_group)
        self.real_table = QTableView()
        real_layout.addWidget(self.real_table)
        splitter.addWidget(self.real_group)
        
        # Shortcuts
        self.setup_shortcuts(self.plan_table)
        self.setup_shortcuts(self.real_table)

        # Initial Data
        self.refresh_data()

    def apply_chart_theme(self, mpl_params):
        pass

    def update_groupbox_styles(self, is_dark):
        if is_dark:
            bg_alpha = "rgba(255, 255, 255, 0.05)"
            plan_border = "#42a5f5"
            plan_text = "#90caf9"
            real_border = "#ef5350"
            real_text = "#ef9a9a"
        else:
            bg_alpha = "rgba(0, 0, 0, 0.02)"
            plan_border = "#1565C0"
            plan_text = "#0D47A1"
            real_border = "#C62828"
            real_text = "#B71C1C"

        self._apply_style(self.plan_group, plan_border, plan_text, bg_alpha)
        self._apply_style(self.real_group, real_border, real_text, bg_alpha)

    def _apply_style(self, group, border, text_col, bg_alpha):
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {border};
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 10px;
                background-color: {bg_alpha};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {text_col};
            }}
        """)

    def setup_shortcuts(self, table_view):
        copy_shortcut = QShortcut(QKeySequence.StandardKey.Copy, table_view, context=Qt.ShortcutContext.WidgetWithChildrenShortcut)
        copy_shortcut.activated.connect(lambda: self.copy_selection(table_view))
        paste_shortcut = QShortcut(QKeySequence.StandardKey.Paste, table_view, context=Qt.ShortcutContext.WidgetWithChildrenShortcut)
        paste_shortcut.activated.connect(lambda: self.paste_selection(table_view))

    def refresh_data(self):
        year = self.year_spin.value()
        
        # Planned
        df_plan = em.db_get_budget_matrix(year, ctype='Expense')
        self.plan_model = BudgetTableModel(year, df_plan, category_type="Expense")
        self.plan_table.setModel(self.plan_model)
        self.plan_model.dataChanged.connect(lambda: self.data_changed.emit())
        self.setup_table_view(self.plan_table)

        # Real
        df_real = em.db_get_real_expenses_matrix(year)
        self.real_model = RealExpenseTableModel(year, df_real)
        self.real_table.setModel(self.real_model)
        self.setup_table_view(self.real_table)
        
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
        for tv in [self.plan_table, self.real_table]:
            tv.resizeColumnsToContents()
            tv.resizeRowsToContents()

    def update_chart(self, mpl_params=None):
        pass 

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

class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dark = False # Track theme state
        self.layout = QVBoxLayout(self)
        
        # Top Metrics Frame
        metrics_frame = QHBoxLayout()
        self.total_income_label = QLabel("Ingresos: $0")
        self.total_expense_label = QLabel("Gastos: $0")
        self.balance_label = QLabel("Balance: $0")
        
        for lbl in [self.total_income_label, self.total_expense_label, self.balance_label]:
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px; border: 1px solid #ccc; border-radius: 5px;")
            metrics_frame.addWidget(lbl)
            
        self.layout.addLayout(metrics_frame)
        
        # Year Selection for Dashboard
        year_layout = QHBoxLayout()
        year_layout.addWidget(QLabel("Año:"))
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2000, 2100)
        self.year_spin.setValue(QDate.currentDate().year())
        self.year_spin.valueChanged.connect(self.refresh_data)
        year_layout.addWidget(self.year_spin)
        year_layout.addStretch()
        self.layout.addLayout(year_layout)

        # Charts Area
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        
        self.refresh_data()

    def refresh_data(self):
        year = self.year_spin.value()
        
        # Fetch Data
        df_expenses, df_income, df_budget_expenses, df_budget_income = em.db_get_analytics_data(year)
        analysis = em.process_monthly_summary(df_expenses, df_income, df_budget_expenses, df_budget_income)
        
        # Calculate Metrics
        total_income = analysis['income_amount'].sum()
        total_expense = analysis['expense_amount'].sum()
        balance = total_income - total_expense
        
        self.total_income_label.setText(f"Ingresos Reales: ${total_income:,.2f}")
        self.total_expense_label.setText(f"Gastos Reales: ${total_expense:,.2f}")
        self.balance_label.setText(f"Balance: ${balance:,.2f}")
        
        # Color code balance
        if balance >= 0:
            self.balance_label.setStyleSheet("color: green; font-size: 18px; font-weight: bold; padding: 10px; border: 1px solid #ccc; border-radius: 5px;")
        else:
            self.balance_label.setStyleSheet("color: red; font-size: 18px; font-weight: bold; padding: 10px; border: 1px solid #ccc; border-radius: 5px;")

        # Update Charts
        self.update_charts(analysis, df_expenses)

    def update_charts(self, analysis, df_expenses):
        self.figure.clear()
        
        # Colors
        c_inc = ChartStyler.COLOR_INCOME
        c_exp = ChartStyler.COLOR_REAL_EXP
        c_bud = ChartStyler.COLOR_BUDGET
        
        gs = self.figure.add_gridspec(2, 2, height_ratios=[1, 1])
        ax1 = self.figure.add_subplot(gs[0, :]) # Top wide: Trend
        ax2 = self.figure.add_subplot(gs[1, 0]) # Bottom Left: Pie
        ax3 = self.figure.add_subplot(gs[1, 1]) # Bottom Right: Bar
        
        # Apply Styling to Axes
        for ax in [ax1, ax3]:
            ChartStyler.style_axis(ax, self.is_dark)
            ax.set_facecolor("none") # Transparent background for axes
            
        # 1. Monthly Trend (Line Chart)
        months = range(1, 13)
        month_labels = em.MONTH_NAMES
        
        ax1.plot(months, analysis['income_amount'], label='Ingresos', color=c_inc, linewidth=2.5, marker='o', markersize=6)
        ax1.plot(months, analysis['expense_amount'], label='Gastos', color=c_exp, linewidth=2.5, marker='o', markersize=6)
        ax1.set_xticks(months)
        ax1.set_xticklabels(month_labels)
        ax1.set_title("Evolución Financiera Anual", pad=10, fontsize=10, fontweight='bold')
        
        # Simplified Legend
        leg1 = ax1.legend(frameon=False, loc='upper left', ncol=2)
        if self.is_dark:
             for text in leg1.get_texts(): text.set_color("white")

        # 2. Expense Categories (Pie - Donut Style for modern look)
        if not df_expenses.empty:
            cat_summary = df_expenses.groupby('category')['amount'].sum()
            wedges, texts, autotexts = ax2.pie(cat_summary, labels=cat_summary.index, autopct='%1.1f%%', 
                                              startangle=90, pctdistance=0.85,
                                              wedgeprops=dict(width=0.4, edgecolor='white'))
            
            total_val = cat_summary.sum()
            center_color = "white" if self.is_dark else "#333"
            ax2.text(0, 0, f"${total_val:,.0f}", ha='center', va='center', fontsize=12, fontweight='bold', color=center_color)
            ax2.set_title("Distribución de Gastos", pad=10, fontsize=10, fontweight='bold')
            
            for t in texts + autotexts:
                t.set_color("white" if self.is_dark else "#333")
                t.set_fontsize(8)
        else:
            ax2.text(0.5, 0.5, "Sin Datos", ha='center', color="white" if self.is_dark else "#333")
            ax2.axis('off')

        # 3. Budget vs Real (Grouped Bar Chart)
        width = 0.35
        x = range(len(months))
        
        rects1 = ax3.bar([m - width/2 for m in months], analysis['budget_amount'], width, label='Presupuesto', color=c_bud)
        rects2 = ax3.bar([m + width/2 for m in months], analysis['expense_amount'], width, label='Real', color=c_exp)
        
        ax3.set_xticks(months)
        ax3.set_xticklabels(month_labels, fontsize=8)
        ax3.set_title("Presupuesto vs Ejecución", pad=10, fontsize=10, fontweight='bold')
        
        leg3 = ax3.legend(frameon=False, fontsize=8)
        if self.is_dark:
             for text in leg3.get_texts(): text.set_color("white")

        self.figure.tight_layout()
        self.canvas.draw()
    
    def apply_chart_theme(self, mpl_params):
        self.is_dark = (mpl_params['figure.facecolor'] == '#2b2b2b')
        self.figure.set_facecolor(mpl_params['figure.facecolor'])
        self.refresh_data() # Redraw charts with new theme settings

# --- Main Window ---

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control de Gastos & Presupuesto")
        self.resize(1200, 800)
        
        # Init DB
        em.init_db()
        
        # Theme Manager
        self.theme_manager = ThemeManager()

        # Central Widget & Tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self.dashboard_tab = DashboardWidget()
        self.income_tab = IncomeWidget()
        self.expenses_analysis_tab = ExpenseAnalysisWidget()
        self.registry_tab = ExpensesWidget() # The data entry widget
        
        self.tabs.addTab(self.dashboard_tab, "Tablero de Control")
        self.tabs.addTab(self.income_tab, "Ingresos")
        self.tabs.addTab(self.expenses_analysis_tab, "Gastos")
        self.tabs.addTab(self.registry_tab, "Registro Diario")
        
        # Connect Signals for Auto-Update
        self.registry_tab.data_changed.connect(self.dashboard_tab.refresh_data)
        self.registry_tab.data_changed.connect(self.income_tab.refresh_data)
        self.registry_tab.data_changed.connect(self.expenses_analysis_tab.refresh_data)
        self.income_tab.data_changed.connect(self.dashboard_tab.refresh_data)
        self.expenses_analysis_tab.data_changed.connect(self.dashboard_tab.refresh_data)
        
        # Status Bar
        self.status_label = QLabel()
        self.statusBar().addWidget(self.status_label)
        
        # Link status bar to registry
        self.registry_tab.status_bar_updater = self.update_status
        self.registry_tab.refresh_data() 
        self.update_status()

        # Menus
        self.create_menus()
        
        # Apply Initial Theme (Light)
        self.toggle_theme(initial=True)

    def create_menus(self):
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&Archivo")
        
        export_action = QAction("Exportar a CSV...", self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)

        file_menu.addSeparator()
        
        exit_action = QAction("&Salir", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = menu_bar.addMenu("&Edición")
        
        add_row_action = QAction("Agregar Registro", self)
        add_row_action.setShortcut(QKeySequence.StandardKey.New)
        add_row_action.triggered.connect(self.add_expense_row)
        edit_menu.addAction(add_row_action)

        del_row_action = QAction("Borrar Seleccionados", self)
        del_row_action.setShortcut(QKeySequence.StandardKey.Delete)
        del_row_action.triggered.connect(self.delete_expense_rows)
        edit_menu.addAction(del_row_action)

        # View Menu
        view_menu = menu_bar.addMenu("&Ver")
        totals_action = QAction("Ver Totales (Popup)", self)
        totals_action.triggered.connect(self.show_totals)
        view_menu.addAction(totals_action)
        
        view_menu.addSeparator()
        
        theme_action = QAction("Alternar Tema (Claro/Oscuro)", self)
        theme_action.setShortcut("Ctrl+T")
        theme_action.triggered.connect(lambda: self.toggle_theme(initial=False))
        view_menu.addAction(theme_action)

    def toggle_theme(self, initial=False):
        if initial:
            # Set default without toggling
            sheet = self.theme_manager.LIGHT_THEME
        else:
            sheet = self.theme_manager.toggle()
            
        QApplication.instance().setStyleSheet(sheet)
        
        # Update Matplotlib Chart
        mpl_params = self.theme_manager.get_mpl_params()
        self.dashboard_tab.apply_chart_theme(mpl_params)
        
        # Update GroupBox Colors
        is_dark = self.theme_manager.is_dark
        self.income_tab.update_groupbox_styles(is_dark)
        self.expenses_analysis_tab.update_groupbox_styles(is_dark)

    def export_data(self):
        options = ["Movimientos (Todos)", "Presupuesto de Gastos Planeado", "Presupuesto Gastos Reales", "Presupuesto de Ingresos Planeado", "Presupuesto Ingresos Reales"]
        export_type, ok = QInputDialog.getItem(self, "Exportar Datos", "Seleccione datos a exportar:", options, 0, False)
        
        if not ok: return

        year = QDate.currentDate().year()
        if "Presupuesto" in export_type:
            year, ok = QInputDialog.getInt(self, "Seleccionar Año", "Año Fiscal:", year, 2000, 2100)
            if not ok: return

        try:
            if export_type == "Movimientos (Todos)":
                df = em.db_get_all_expenses_df()
                filename_hint = f"movimientos_{QDate.currentDate().toString('yyyy-MM-dd')}.csv"
            elif export_type == "Presupuesto de Gastos Planeado":
                df = em.db_get_budget_matrix(year, ctype="Expense")
                df.columns = [em.MONTH_MAP.get(c, c) for c in df.columns]
                filename_hint = f"presupuesto_gastos_planeado_{year}.csv"
            elif export_type == "Presupuesto Gastos Reales":
                df = em.db_get_real_expenses_matrix(year)
                df.columns = [em.MONTH_MAP.get(c, c) for c in df.columns]
                filename_hint = f"presupuesto_gastos_reales_{year}.csv"
            elif export_type == "Presupuesto de Ingresos Planeado":
                df = em.db_get_budget_matrix(year, ctype="Income")
                df.columns = [em.MONTH_MAP.get(c, c) for c in df.columns]
                filename_hint = f"presupuesto_ingresos_planeado_{year}.csv"
            else: # Presupuesto Ingresos Reales
                df = em.db_get_real_income_matrix(year)
                df.columns = [em.MONTH_MAP.get(c, c) for c in df.columns]
                filename_hint = f"presupuesto_ingresos_reales_{year}.csv"

            file_path, _ = QFileDialog.getSaveFileName(self, "Guardar CSV", filename_hint, "CSV Files (*.csv)")
            if file_path:
                if 'id' in df.columns:
                    df = df.drop(columns=['id'])
                save_index = "Presupuesto" in export_type
                df.to_csv(file_path, index=save_index, encoding='utf-8-sig')
                QMessageBox.showinfo("Éxito", f"Datos exportados a:\n{file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar:\n{str(e)}")

    def add_expense_row(self):
        self.tabs.setCurrentWidget(self.registry_tab)
        self.registry_tab.open_add_dialog()

    def delete_expense_rows(self):
        if self.tabs.currentWidget() != self.registry_tab:
            QMessageBox.information(self, "Info", "Cambie a la pestaña 'Registro Diario' para borrar.")
            return
        self.registry_tab.delete_rows()

    def show_totals(self):
        if self.tabs.currentWidget() == self.registry_tab:
            total = self.registry_tab.model.get_total_amount()
            count = self.registry_tab.model.rowCount()
            QMessageBox.information(self, "Totales", f"Registros: {count}\nMonto Total: ${total:,.2f}")
        else:
             QMessageBox.information(self, "Info", "Totales disponibles solo en pestaña Registro Diario.")

    def update_status(self):
        total = self.registry_tab.model.get_total_amount()
        count = self.registry_tab.model.rowCount()
        self.status_label.setText(f"Registros: {count} | Total Histórico: ${total:,.2f}")

    def closeEvent(self, event):
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
