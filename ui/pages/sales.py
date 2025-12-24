# ui/pages/sales.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QMessageBox,
    QFormLayout, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.database import get_all_customers, get_all_products, get_product_by_id, add_sale

class SalesPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                color: white;
            }
            QLineEdit, QComboBox {
                background-color: #34495e;
                color: white;
                border: 1px solid #7f8c8d;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton {
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QTableWidget {
                background-color: #34495e;
                color: white;
                gridline-color: #7f8c8d;
            }
            QHeaderView::section {
                background-color: #3c5a75;
                color: white;
                padding: 6px;
                border: 1px solid #7f8c8d;
            }
        """)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Sales Menu")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: white; margin-bottom: 20px;")
        layout.addWidget(title)

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setStyleSheet("""
            background-color: #3498db;
            color: white;
            border: 5px;
            padding: 6px 12px;
            border-radius: 5px;
            font-weight: bold;
        """)
        self.refresh_btn.clicked.connect(self.load_data)
        layout.addWidget(self.refresh_btn)

        # Sale type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Sale Type:"))
        self.sale_type_combo = QComboBox()
        self.sale_type_combo.addItems(["Retail", "Wholesale"])
        type_layout.addWidget(self.sale_type_combo)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        # Customer (wholesale only)
        customer_layout = QHBoxLayout()
        customer_layout.addWidget(QLabel("Customer:"))
        self.customer_combo = QComboBox()
        self.customer_combo.setMinimumWidth(300)
        customer_layout.addWidget(self.customer_combo)
        customer_layout.addStretch()
        layout.addLayout(customer_layout)

        # Product selection
        form_layout = QFormLayout()

        self.product_combo = QComboBox()
        self.product_combo.setMinimumWidth(300)
        self.selling_price_input = QLineEdit()
        self.selling_price_input.setPlaceholderText("Enter selling price")
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("Enter quantity")

        form_layout.addRow("Product:", self.product_combo)
        form_layout.addRow("Selling Price ($):", self.selling_price_input)
        form_layout.addRow("Quantity:", self.quantity_input)
        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.add_to_cart_btn = QPushButton("Add to Cart")
        self.add_to_cart_btn.setStyleSheet("background-color: #3498db; color: white;")
        self.add_to_cart_btn.clicked.connect(self._add_to_cart)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setStyleSheet("background-color: #95a5a6; color: white;")
        self.clear_btn.clicked.connect(self._clear_form)

        button_layout.addWidget(self.add_to_cart_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Cart
        cart_title = QLabel("Sale Cart")
        cart_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(cart_title)

        self.cart_table = QTableWidget(0, 6)
        self.cart_table.setHorizontalHeaderLabels(
            ["Product", "Qty", "Cost", "Sell", "Total", "Actions"]
        )
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.cart_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.cart_table)

        # Paid amount & total
        payment_layout = QHBoxLayout()
        payment_layout.addWidget(QLabel("Amount Paid ($):"))
        self.paid_input = QLineEdit()
        self.paid_input.setPlaceholderText("0.00")
        payment_layout.addWidget(self.paid_input)

        self.total_label = QLabel("Total: $0.00")
        self.total_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.total_label.setStyleSheet("color: #27ae60;")
        payment_layout.addWidget(self.total_label)
        layout.addLayout(payment_layout)

        # Save button
        save_layout = QHBoxLayout()
        self.save_sale_btn = QPushButton("Save Sale")
        self.save_sale_btn.setStyleSheet("background-color: #27ae60; color: white;")
        self.save_sale_btn.clicked.connect(self._save_sale)
        save_layout.addWidget(self.save_sale_btn)
        save_layout.addStretch()
        layout.addLayout(save_layout)

        # Load data
        self._load_customers()
        self._load_products()
        self.sale_type_combo.currentTextChanged.connect(self._on_sale_type_changed)
        self._on_sale_type_changed("Retail")  # init visibility
    def load_data(self):
        self._load_customers()
        self._load_products()

    def _on_sale_type_changed(self, text):
        is_wholesale = (text == "Wholesale")
        self.customer_combo.setVisible(is_wholesale)
        self.customer_combo.setHidden(not is_wholesale)

    def _load_customers(self):
        try:
            customers = get_all_customers()
            self.customer_combo.clear()
            for c in customers:
                self.customer_combo.addItem(f"{c['full_name']} - {c['phone_number']}", c['id'])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load customers:\n{str(e)}")

    def _load_products(self):
        try:
            products = get_all_products()
            self.product_combo.clear()
            for p in products:
                # Show name, company, cost
                display = f"{p['name']} ({p['company']}) - Cost: ${p.get('cost_price', 0):.2f}"
                self.product_combo.addItem(display, p['id'])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load products:\n{str(e)}")

    def _add_to_cart(self):
        try:
            # Validate
            if self.product_combo.currentIndex() == -1:
                raise ValueError("Select a product")
            quantity = int(self.quantity_input.text())
            selling_price = float(self.selling_price_input.text())
            if quantity <= 0 or selling_price <= 0:
                raise ValueError("Quantity and price must be positive")

            # Get product - use direct lookup instead of loading all products
            product_id = self.product_combo.currentData()
            prod = get_product_by_id(product_id)
            if not prod:
                raise ValueError("Product not found")
            
            # Check store quantity (sales come from store)
            store_qty = prod.get('store_quantity', 0)
            if store_qty < quantity:
                raise ValueError(f"Only {store_qty} units available in store. Warehouse has {prod.get('warehouse_quantity', 0)} units.")

            cost_price = prod.get('cost_price', 0)
            total = selling_price * quantity

            # Add to cart
            row = self.cart_table.rowCount()
            self.cart_table.insertRow(row)
            
            self.cart_table.setItem(row, 0, QTableWidgetItem(prod['name']))
            self.cart_table.setItem(row, 1, QTableWidgetItem(str(quantity)))
            self.cart_table.setItem(row, 2, QTableWidgetItem(f"{cost_price:.2f}"))
            self.cart_table.setItem(row, 3, QTableWidgetItem(f"{selling_price:.2f}"))
            self.cart_table.setItem(row, 4, QTableWidgetItem(f"{total:.2f}"))
            
            # Store hidden data
            self.cart_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, {
                'product_id': product_id,
                'cost_price': cost_price,
                'selling_price': selling_price,
                'quantity': quantity,
                'product_name': prod['name']
            })

            # Remove button
            remove_btn = QPushButton("Remove")
            remove_btn.setStyleSheet("background-color: #e74c3c; color: white;")
            remove_btn.clicked.connect(lambda _, r=row: self._remove_from_cart(r))
            self.cart_table.setCellWidget(row, 5, remove_btn)

            self._update_total()
            self._clear_form()

        except Exception as e:
            QMessageBox.warning(self, "Input Error", str(e))

    def _remove_from_cart(self, row):
        self.cart_table.removeRow(row)
        self._update_total()

    def _update_total(self):
        total = sum(float(self.cart_table.item(row, 4).text()) for row in range(self.cart_table.rowCount()))
        self.total_label.setText(f"Total: ${total:.2f}")

    def _clear_form(self):
        self.quantity_input.clear()
        self.selling_price_input.clear()

    def _save_sale(self):
        try:
            if self.cart_table.rowCount() == 0:
                raise ValueError("Cart is empty")

            paid = float(self.paid_input.text() or "0")
            total = float(self.total_label.text().replace("Total: $", ""))
            if paid > total:
                raise ValueError("Paid amount cannot exceed total")

            sale_type = "wholesale" if self.sale_type_combo.currentText() == "Wholesale" else "retail"
            customer_name = None
            if sale_type == "wholesale":
                if self.customer_combo.currentIndex() == -1:
                    raise ValueError("Select a customer")
                customer_name = self.customer_combo.currentText().split(" - ")[0]

            # Save each cart item
            for row in range(self.cart_table.rowCount()):
                data = self.cart_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                add_sale(
                    sale_type=sale_type,
                    product_id=data['product_id'],
                    product_name=data['product_name'],
                    selling_price=data['selling_price'],
                    cost_price=data['cost_price'],
                    quantity=data['quantity'],
                    paid_amount=paid if row == 0 else 0,  # Only first item gets paid (for due tracking)
                    customer_name=customer_name
                )
                # For multi-item, paid is applied to first; due logic can be enhanced later

            QMessageBox.information(self, "Success", "Sale saved successfully!")
            self.cart_table.setRowCount(0)
            self.paid_input.clear()
            self._update_total()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))