# ui/pages/customers.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QMessageBox, QAbstractItemView, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.database import get_all_customers, delete_customer, get_customer_dues_by_name
from ui.dialogs.add_customer import AddCustomerDialog

class CustomersPage(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header_layout = QHBoxLayout()
        title = QLabel("Customer Data")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        header_layout.addWidget(title)

        # Search
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("search for customers ...")
        self.search_bar.setStyleSheet("""
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
        """)
        self.search_bar.textChanged.connect(self.load_data)
        header_layout.addWidget(self.search_bar)

        # Add button
        self.add_btn = QPushButton("Add Customer")
        self.add_btn.setStyleSheet("""
            background-color: #27ae60;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
        """)
        self.add_btn.clicked.connect(self._add_customer)
        header_layout.addWidget(self.add_btn)

        layout.addLayout(header_layout)

        # Table - Now 7 columns (added Due Amount)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Full Name", "WhatsApp", "Phone", "Address", "Due Amount", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: 1px solid #dee2e6;
                font-weight: bold;
                color: #495057;
            }
            /* Style for due amount column - red text for outstanding dues */
            QTableWidget::item:nth-column(6) {
                color: #e74c3c;
                font-weight: bold;
            }
        """)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.table)

        self.load_data()

    def load_data(self):
        try:
            search = self.search_bar.text().strip()
            customers = get_all_customers(search)
            self.table.setRowCount(len(customers))
            
            for row, cust in enumerate(customers):
                self.table.setItem(row, 0, QTableWidgetItem(str(cust["id"])))
                self.table.setItem(row, 1, QTableWidgetItem(cust["full_name"]))
                self.table.setItem(row, 2, QTableWidgetItem(cust["whatsapp_number"]))
                self.table.setItem(row, 3, QTableWidgetItem(cust["phone_number"]))
                self.table.setItem(row, 4, QTableWidgetItem(cust["address"]))
                
                # Calculate and display due amount
                due_amount = get_customer_dues_by_name(cust["full_name"])
                if due_amount > 0:
                    due_item = QTableWidgetItem(f"${due_amount:.2f}")
                    due_item.setForeground(Qt.GlobalColor.red)  # Red color for outstanding dues
                    due_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    due_item = QTableWidgetItem("-")
                    due_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 5, due_item)
                
                # Action buttons
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(5, 2, 5, 2)
                action_layout.setSpacing(5)
                
                edit_btn = QPushButton("Edit")
                edit_btn.setStyleSheet("""
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                """)
                edit_btn.clicked.connect(lambda _, c=cust: self._edit_customer(c))
                
                delete_btn = QPushButton("Delete")
                delete_btn.setStyleSheet("""
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                """)
                delete_btn.clicked.connect(lambda _, c=cust: self._delete_customer(c))
                
                action_layout.addWidget(edit_btn)
                action_layout.addWidget(delete_btn)
                action_layout.addStretch()
                
                self.table.setCellWidget(row, 6, action_widget)  # Actions now in column 6 (0-indexed)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load customers:\n{str(e)}")

    def _add_customer(self):
        dialog = AddCustomerDialog(self)
        if dialog.exec():
            self.load_data()

    def _edit_customer(self, customer):
        dialog = AddCustomerDialog(self, customer)
        if dialog.exec():
            self.load_data()

    def _delete_customer(self, customer):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete '{customer['full_name']}'?\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                delete_customer(customer["id"])
                self.load_data()
                QMessageBox.information(self, "Success", "Customer deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete customer:\n{str(e)}")