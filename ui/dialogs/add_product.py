# ui/dialogs/add_product.py
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QVBoxLayout, QMessageBox, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.database import add_product, update_product

class AddProductDialog(QDialog):
    def __init__(self, parent=None, product=None):
        super().__init__(parent)
        self.product = product
        self.setWindowTitle("Add Product" if not product else "Edit Product")
        self.setModal(True)
        self.resize(400, 200)
        self._init_ui()

    def _init_ui(self):
        
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

        self.id_input = QLineEdit()
        self.name_input = QLineEdit()
        self.company_input = QLineEdit()
        self.cost_price_input = QLineEdit()
        self.quantity_input = QLineEdit()
        self.warehouse_quantity_input = QLineEdit()
        self.store_quantity_input = QLineEdit()

        # for placeholder to give for clinets\
        self.id_input.setPlaceholderText("دجنس ای ډي ضروري ده ")
        self.name_input.setPlaceholderText("د جنس نوم دننه کړئ ")
        self.company_input.setPlaceholderText("د جنس د کمپنئ نوم دننه کړئ ")
        self.cost_price_input.setPlaceholderText("د جنس نهایی قیمت داخل کړئ ")
        self.quantity_input.setPlaceholderText("د جنس مقدار وټاکئ ")
        self.warehouse_quantity_input.setPlaceholderText("Warehouse quantity")
        self.store_quantity_input.setPlaceholderText("Store quantity")

        if self.product:
            self.id_input.setText(self.product["id"])
            self.id_input.setReadOnly(True)  # Don't allow editing ID
            self.name_input.setText(self.product["name"])
            self.company_input.setText(self.product["company"])
            self.cost_price_input.setText(str(self.product["cost_price"]))
            self.quantity_input.setText(str(self.product["quantity"]))
            self.warehouse_quantity_input.setText(str(self.product.get("warehouse_quantity", 0)))
            self.store_quantity_input.setText(str(self.product.get("store_quantity", 0)))
        else:
            # New product: default to warehouse
            self.warehouse_quantity_input.setText("0")
            self.store_quantity_input.setText("0")

        layout.addRow("Product ID:", self.id_input)
        layout.addRow("Product Name:", self.name_input)
        layout.addRow("Company:", self.company_input)
        layout.addRow("Cost_Price ($):", self.cost_price_input)
        layout.addRow("Total Quantity:", self.quantity_input)
        layout.addRow("Warehouse Quantity:", self.warehouse_quantity_input)
        layout.addRow("Store Quantity:", self.store_quantity_input)

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
            Product_ID= self.id_input.text().strip()
            if not Product_ID:
                raise ValueError("د جنس ای ډی ضرور ده")
            name = self.name_input.text().strip()
            company = self.company_input.text().strip()
            price_str = self.cost_price_input.text().strip()
            quantity_str = self.quantity_input.text().strip()
            warehouse_qty_str = self.warehouse_quantity_input.text().strip() or "0"
            store_qty_str = self.store_quantity_input.text().strip() or "0"

            # Validation
            if not Product_ID or not company:
                raise ValueError("Product ID and company are required.")
            
            try:
                price = float(price_str)
                quantity = int(quantity_str)
                warehouse_qty = int(warehouse_qty_str)
                store_qty = int(store_qty_str)
                
                if price < 0 or quantity < 0 or warehouse_qty < 0 or store_qty < 0:
                    raise ValueError("All values must be non-negative.")
                
                if warehouse_qty + store_qty != quantity:
                    raise ValueError(f"Warehouse quantity ({warehouse_qty}) + Store quantity ({store_qty}) must equal Total quantity ({quantity})")
            except ValueError as e:
                if "must equal" in str(e):
                    raise
                raise ValueError("Price must be a number, quantities must be integers.")

            # Save to database
            if self.product:
                update_product(
                    product_id=self.product["id"], 
                    name=name, 
                    company=company, 
                    cost_price=price, 
                    quantity=quantity,
                    warehouse_quantity=warehouse_qty,
                    store_quantity=store_qty
                )
                QMessageBox.information(self, "Success", "Product updated successfully!")
            else:
                # Add new product - default to warehouse if not specified
                if warehouse_qty == 0 and store_qty == 0:
                    warehouse_qty = quantity
                add_product(Product_ID, name, company, price, quantity, warehouse_qty, store_qty)
                QMessageBox.information(self, "Success", "Product added successfully!")
            self.accept()

        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save product:\n{str(e)}")