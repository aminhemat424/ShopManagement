# main.py
import sys
from PyQt6.QtWidgets import QApplication
from core.database import init_database
from ui.main_window import MainWindow
from ui.style import apply_global_style

def main():
    init_database()
    app = QApplication(sys.argv)
    apply_global_style(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()