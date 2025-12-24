# ui/pages/purchase.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QMessageBox, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.database import get_all_products, update_product

class PurchasePage(QWidget):
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
                padding: 6px 12px;
                font-weight: bold;
            }
            #refreshButton {
                background-color: #3498db;
                color: white;
            }
            #saveButton {
                background-color: #27ae60;
                color: white;
            }
            #clearButton {
                background-color: #95a5a6;
                color: white;
            }
        """)
        self.products = []
        self._init_ui()
        self._load_products()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(0)  # We'll control spacing manually

        # === HEADER: Title + Refresh Button ===
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        title = QLabel("Purchase List")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Refresh button (top-right)
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setObjectName("refreshButton")
        self.refresh_btn.clicked.connect(self._refresh_page)
        header_layout.addWidget(self.refresh_btn)

        main_layout.addLayout(header_layout)
        main_layout.addSpacing(15)  # Small space after title

        # === FORM: 3 rows ===
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.product_combo = QComboBox()
        self.product_combo.setMinimumWidth(300)
        form_layout.addRow("Product:", self.product_combo)

        self.cost_price_input = QLineEdit()
        self.cost_price_input.setPlaceholderText("e.g. 20.00")
        form_layout.addRow("Cost Price ($):", self.cost_price_input)

        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("e.g. 10")
        form_layout.addRow("Quantity Purchased:", self.quantity_input)

        main_layout.addLayout(form_layout)
        main_layout.addSpacing(20)  # Space before buttons

        # === BUTTONS: Save + Clear ===
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.save_btn = QPushButton("Save Purchase")
        self.save_btn.setObjectName("saveButton")
        self.save_btn.clicked.connect(self._save_purchase)
        button_layout.addWidget(self.save_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setObjectName("clearButton")
        self.clear_btn.clicked.connect(self._clear_form)
        button_layout.addWidget(self.clear_btn)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        main_layout.addStretch()  # Push everything to top

    def _refresh_page(self):
        """Refresh all data on the page."""
        self._load_products()
        self._clear_form()

    def _load_products(self):
        try:
            self.products = get_all_products()
            self.product_combo.clear()
            for prod in self.products:
                display = f"{prod['name']} ({prod['company']})"
                self.product_combo.addItem(display, prod["id"])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load products:\n{str(e)}")

    def _clear_form(self):
        self.cost_price_input.clear()
        self.quantity_input.clear()
        if self.product_combo.count() > 0:
            self.product_combo.setCurrentIndex(0)

    def _save_purchase(self):
        try:
            if self.product_combo.currentIndex() == -1:
                raise ValueError("Please select a product")

            cost_price = float(self.cost_price_input.text().strip())
            quantity = int(self.quantity_input.text().strip())

            if cost_price <= 0:
                raise ValueError("Cost price must be greater than zero")
            if quantity <= 0:
                raise ValueError("Quantity must be a positive number")

            product_id = self.product_combo.currentData()
            current_prod = next((p for p in self.products if p["id"] == product_id), None)
            if not current_prod:
                raise ValueError("Selected product not found")

            # Add to warehouse (new purchases go to warehouse first)
            new_total_quantity = current_prod["quantity"] + quantity
            new_warehouse_quantity = current_prod.get("warehouse_quantity", 0) + quantity
            current_store_quantity = current_prod.get("store_quantity", 0)

            update_product(
                product_id=product_id,
                name=current_prod["name"],
                company=current_prod["company"],
                cost_price=cost_price,
                quantity=new_total_quantity,
                warehouse_quantity=new_warehouse_quantity,
                store_quantity=current_store_quantity
            )

            QMessageBox.information(
                self, "Success",
                f"Purchase recorded!\n"
                f"Added {quantity} units of '{current_prod['name']}' at ${cost_price:.2f} each.\n"
                f"New total stock: {new_total_quantity} units (Warehouse: {new_warehouse_quantity}, Store: {current_store_quantity})."
            )

            self._refresh_page()  # Auto-refresh after save

        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save purchase:\n{str(e)}")