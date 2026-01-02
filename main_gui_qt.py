import sys
from PyQt6.QtWidgets import QApplication
from src.expenses_control.gui.qt_app import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
