# ui/style.py
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

def apply_global_style(app: QApplication):
  
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet("""
        QMainWindow, QDialog {
            background-color: #f8f9fa;
        }
        QTableWidget {
            gridline-color: #e0e0e0;
            font-size: 13px;
        }
        QHeaderView::section {
            background-color: #f1f3f5;
            padding: 6px;
            border: 1px solid #dfe3e8;
            font-weight: bold;
            color: #495057;
        }
        QLineEdit {
            padding: 6px;
            border: 1px solid #AECAE5;
            border-radius: 4px;
        }
        QPushButton {
            padding: 8px 16px;
            border-radius: 5px;
            font-weight: bold;
        }
    """)

SIDEBAR_BUTTON_STYLE = """
    QPushButton {
        text-align: left;
        padding: 14px 25px;
        color: #ecf0f1;
        font-size: 14px;
        border: none;
    }
    QPushButton:hover {
        background-color: #34495e;
    }
    QPushButton:checked {
        background-color: #3498db;
        font-weight: bold;
    }
"""

ACTION_BUTTON_STYLE = """
    QPushButton {
        background-color: #3498db;
        color: black;
        border: none;
        padding: 8px 18px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 13px;
    }
    QPushButton:hover {
        background-color: #2980b9;
    }
"""