# ui/dialogs/add_customer.py
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QVBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt
from core.database import add_customer, update_customer

class AddCustomerDialog(QDialog):
    def __init__(self, parent=None, customer=None):
        super().__init__(parent)
        self.customer = customer
        self.setWindowTitle("Add Customer" if not customer else "Edit Customer")
        self.setModal(True)
        self.resize(400, 200)
        self._init_ui()

    def _init_ui(self):
        # Set background color for the dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #38444F;
            }
            QLineEdit {
                background-color: #38444F;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px;
            }
        """)

        layout = QFormLayout()
        
        # Input fields
        self.name_input = QLineEdit()
        self.whatsapp_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.address_input = QLineEdit()

        # set place holder for add customer menue\
        self.name_input.setPlaceholderText("د مشتري مکمل نوم دننه کړئ ")
        self.whatsapp_input.setPlaceholderText("د مشتري د واتساپ شمیره دننه کړئ ")
        self.phone_input.setPlaceholderText("د مشتري د مبایل شمیره دننه کړئ ")
        self.address_input.setPlaceholderText("د مشتري مکمل ادرس دننه کړئ ")

        # Set values if editing
        if self.customer:
            self.name_input.setText(self.customer["full_name"])
            self.whatsapp_input.setText(self.customer["whatsapp_number"])
            self.phone_input.setText(self.customer["phone_number"])
            self.address_input.setText(self.customer["address"])

        layout.addRow("Full Name:", self.name_input)
        layout.addRow("WhatsApp:", self.whatsapp_input)
        layout.addRow("Phone:", self.phone_input)
        layout.addRow("Address:", self.address_input)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._save)
        button_box.rejected.connect(self.reject)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)

    def _save(self):
        try:
            full_name = self.name_input.text().strip()
            whatsapp = self.whatsapp_input.text().strip()
            phone = self.phone_input.text().strip()
            address = self.address_input.text().strip()

            # Validation
            if not full_name or not whatsapp or not phone or not address:
                raise ValueError("All fields are required.")

            # Save to database
            if self.customer:
                # Update existing customer
                update_customer(self.customer["id"], full_name, whatsapp, phone, address)
                QMessageBox.information(self, "Success", "Customer updated successfully!")
            else:
                # Add new customer
                add_customer(full_name, whatsapp, phone, address)
                QMessageBox.information(self, "Success", "Customer added successfully!")

            self.accept()

        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save customer:\n{str(e)}")