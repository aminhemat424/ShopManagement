# ui/pages/dues.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QMessageBox, QFrame,
    QComboBox, QLineEdit, QFormLayout, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.database import (
    get_customer_dues_with_payments, 
    get_dues_payment_history,
    add_dues_payment
)

class DuesPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                color: white;
            }
            QLabel {
                color: white;
            }
            QLineEdit, QComboBox {
                background-color: #34495e;
                color: white;
                border: 1px solid #7f8c8d;
                border-radius: 4px;
                padding: 4px;
            }
            QPushButton {
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
        """)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header with title and refresh button
        header_layout = QHBoxLayout()
        
        title = QLabel("Customer Dues Management")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setStyleSheet("""
            background-color: #B34338;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 3px;
            font-weight: bold;
        """)
        self.refresh_btn.clicked.connect(self._load_data)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)

        # Receive Payment Section
        payment_section = self._create_payment_section()
        layout.addWidget(payment_section)

        # Current Dues Table
        dues_title = QLabel("Outstanding Customer Dues")
        dues_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        dues_title.setStyleSheet("color: #e74c3c; margin-top: 20px;")
        layout.addWidget(dues_title)

        self.dues_table = QTableWidget(0, 5)
        self.dues_table.setHorizontalHeaderLabels([
            "Customer", "Total Due", "Received", "Remaining", "Last Sale"
        ])
        self.dues_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        
        self.dues_table.setStyleSheet("""
            QTableWidget {
                background-color: #34495e;
                color: white;
                gridline-color: #7f8c8d;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #c0392b;
                color: white;
                padding: 4px;
                border: none;
                font-weight: bold;
            }
        """)
        self.dues_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.dues_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.dues_table)

        # Payment History Table
        history_title = QLabel("Payment History")
        history_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        history_title.setStyleSheet("color: white; margin-top: 20px;")
        layout.addWidget(history_title)

        self.history_table = QTableWidget(0, 4)
        self.history_table.setHorizontalHeaderLabels([
            "Date", "Customer", "Amount", "Notes"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        self.history_table.setStyleSheet("""
            QTableWidget {
                background-color: #34495e;
                color: white;
                gridline-color: #7f8c8d;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #3c5a75;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.history_table)

        self._load_data()

    def _create_payment_section(self):
        section_widget = QFrame()
        section_widget.setStyleSheet("background-color: #34495e; border-radius: 8px; padding: 10px;")
        layout = QVBoxLayout(section_widget)
        
        title = QLabel("Receive Payment")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        layout.addWidget(title)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        self.customer_combo = QComboBox()
        self.customer_combo.setMinimumWidth(250)
        form_layout.addRow("Customer:", self.customer_combo)
        
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Enter amount received")
        form_layout.addRow("Amount ($):", self.amount_input)
        
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Optional notes (e.g., payment method)")
        form_layout.addRow("Notes:", self.notes_input)
        
        self.receive_btn = QPushButton("Record Payment")
        self.receive_btn.setStyleSheet("""
            background-color: #27ae60;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 3px;
            font-weight: bold;
        """)
        self.receive_btn.clicked.connect(self._receive_payment)
        form_layout.addRow("", self.receive_btn)
        
        layout.addLayout(form_layout)
        return section_widget

    def _load_data(self):
        try:
            dues_data = get_customer_dues_with_payments()  # Fixed: removed extra 't'
            self.customer_combo.clear()
            self.customer_combo.addItem("-- Select Customer --")
            # uniqe customers 
            dues_customers = [due["customer_name"] for due in dues_data]
            for customer_name in sorted(set(dues_customers)):  # Remove duplicates and sort
                self.customer_combo.addItem(customer_name)  # Don't add cust['id'] since we're using names
            
            # Load current dues table
            self.dues_table.setRowCount(len(dues_data))
            for row, due in enumerate(dues_data):
                self.dues_table.setItem(row, 0, QTableWidgetItem(due["customer_name"]))
                self.dues_table.setItem(row, 1, QTableWidgetItem(f"${due['total_due']:.2f}"))
                self.dues_table.setItem(row, 2, QTableWidgetItem(f"${due['total_received']:.2f}"))
                self.dues_table.setItem(row, 3, QTableWidgetItem(f"${due['remaining_due']:.2f}"))
                
                last_date = due["last_sale_date"]
                if last_date:
                    date_only = last_date.split(" ")[0] if " " in last_date else last_date
                    self.dues_table.setItem(row, 4, QTableWidgetItem(date_only))
                else:
                    self.dues_table.setItem(row, 4, QTableWidgetItem("N/A"))
            
            # Load payment history
            history_data = get_dues_payment_history()
            self.history_table.setRowCount(len(history_data))
            for row, payment in enumerate(history_data):
                date_str = payment["received_date"]
                if date_str:
                    date_display = date_str.replace("T", " ") if "T" in date_str else date_str
                    self.history_table.setItem(row, 0, QTableWidgetItem(date_display))
                else:
                    self.history_table.setItem(row, 0, QTableWidgetItem("N/A"))
                    
                self.history_table.setItem(row, 1, QTableWidgetItem(payment["customer_name"]))
                self.history_table.setItem(row, 2, QTableWidgetItem(f"${payment['amount_received']:.2f}"))
                self.history_table.setItem(row, 3, QTableWidgetItem(payment.get("notes", "")))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load dues data:\n{str(e)}")
        
    def _receive_payment(self):

        try:
            # Validate customer selection
            if self.customer_combo.currentIndex() <= 0:
                raise ValueError("Please select a customer")
            
            customer_name = self.customer_combo.currentText()
            amount_text = self.amount_input.text().strip()
            
            if not amount_text:
                raise ValueError("Please enter payment amount")
            
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError("Payment amount must be positive")
            
            notes = self.notes_input.text().strip()
            
            # Record payment
            add_dues_payment(customer_name, amount, notes)
            
            # Show success message
            QMessageBox.information(
                self, "Success", 
                f"Payment of ${amount:.2f} recorded for {customer_name}!"
            )
            
            # Clear form and refresh
            self.amount_input.clear()
            self.notes_input.clear()
            self._load_data()
            
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to record payment:\n{str(e)}")