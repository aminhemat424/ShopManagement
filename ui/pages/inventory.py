# ui/pages/inventory.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QMessageBox,
    QFormLayout, QFrame, QSizePolicy, QScrollArea, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.database import (
    get_all_products, get_product_by_id, transfer_inventory,
    get_low_stock_products
)

class InventoryPage(QWidget):
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
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Inventory Management")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setStyleSheet("""
            background-color: #3498db;
            color: white;
        """)
        self.refresh_btn.clicked.connect(self._load_data)
        header_layout.addWidget(self.refresh_btn)
        layout.addLayout(header_layout)

        # Summary cards
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(15)
        
        self.warehouse_card = self._create_summary_card("Warehouse Stock", "0", "#8e44ad")
        self.store_card = self._create_summary_card("Store Stock", "0", "#16a085")
        self.low_stock_card = self._create_summary_card("Low Stock Items", "0", "#e74c3c")
        
        summary_layout.addWidget(self.warehouse_card)
        summary_layout.addWidget(self.store_card)
        summary_layout.addWidget(self.low_stock_card)
        summary_layout.addStretch()
        layout.addLayout(summary_layout)
        
        # Make cards expandable
        self.warehouse_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.store_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.low_stock_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Action buttons section
        actions_section = QFrame()
        actions_section.setStyleSheet("background-color: #34495e; border-radius: 2px; padding: 10px;")
        actions_layout = QVBoxLayout(actions_section)
        
        actions_title = QLabel("Inventory Actions click to transfer ")
        actions_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        actions_title.setStyleSheet("color: white; margin-bottom: 2px;")
        actions_layout.addWidget(actions_title)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        transfer_btn = QPushButton("Transfer Inventory")
        transfer_btn.setStyleSheet("background-color: #9b59b6; color: white; min-width: 150px;")
        transfer_btn.clicked.connect(self._show_transfer_dialog)
        buttons_layout.addWidget(transfer_btn)
        
        buttons_layout.addStretch()
        actions_layout.addLayout(buttons_layout)
        layout.addWidget(actions_section)

        # Inventory table
        table_title = QLabel("All Products Inventory")
        table_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        table_title.setStyleSheet("color: white; margin-top: 15px;")
        layout.addWidget(table_title)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Product ID", "Name", "Company", "Cost Price", "Warehouse", "Store", "Total"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.table)

        self._load_data()

    def _create_summary_card(self, title, value, color):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                stop:0 {color}, stop:1 {self._lighten_color(color, 0.3)});
                border-radius: 8px;
                padding: 4px;
                min-height: 15px;
                max-height: 100px;
            }}
            QLabel {{
                color: white;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 10, 10, 10)
        card_layout.setSpacing(5)
        
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        header_layout.addWidget(title_label)
        card_layout.addLayout(header_layout)
        
        # Value
        value_label = QLabel(value)
        value_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        value_label.setStyleSheet("color: white; margin-top: 5px;")
        card_layout.addWidget(value_label)
        
        card.value_label = value_label
        return card

    def _lighten_color(self, color, factor):
        """Lighten a color by a factor."""
        import colorsys
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        h, s, v = colorsys.rgb_to_hsv(*[x/255.0 for x in rgb])
        v = min(1.0, v + factor)
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

    def _show_transfer_dialog(self):
        """Show transfer inventory dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Transfer Inventory")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2c3e50;
            }
            QLabel {
                color: white;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        
        form_layout = QFormLayout()
        
        product_combo = QComboBox()
        product_combo.setMinimumWidth(300)
        product_combo.setStyleSheet("""
            background-color: #34495e;
            color: white;
            border: 1px solid #7f8c8d;
            border-radius: 4px;
            padding: 6px;
        """)
        
        stock_info_label = QLabel("Warehouse: 0 | Store: 0")
        stock_info_label.setStyleSheet("color: #f39c12; font-weight: bold; padding: 5px;")
        
        quantity_input = QLineEdit()
        quantity_input.setPlaceholderText("Enter quantity to transfer")
        quantity_input.setStyleSheet("""
            background-color: #34495e;
            color: white;
            border: 1px solid #7f8c8d;
            border-radius: 4px;
            padding: 6px;
        """)
        
        from_combo = QComboBox()
        from_combo.addItems(["Warehouse", "Store"])
        from_combo.setStyleSheet("""
            background-color: #34495e;
            color: white;
            border: 1px solid #7f8c8d;
            border-radius: 4px;
            padding: 6px;
        """)
        
        to_combo = QComboBox()
        to_combo.addItems(["Store"])
        to_combo.setStyleSheet("""
            background-color: #34495e;
            color: white;
            border: 1px solid #7f8c8d;
            border-radius: 4px;
            padding: 6px;
        """)
        
        def update_destinations():
            from_location = from_combo.currentText().lower()
            to_combo.clear()
            if from_location == "warehouse":
                to_combo.addItem("Store")
            else:
                to_combo.addItem("Warehouse")
        
        from_combo.currentTextChanged.connect(update_destinations)
        
        def update_stock_info():
            if product_combo.currentIndex() >= 0:
                product_id = product_combo.currentData()
                if product_id:
                    prod = get_product_by_id(product_id)
                    if prod:
                        warehouse_qty = prod.get('warehouse_quantity', 0)
                        store_qty = prod.get('store_quantity', 0)
                        stock_info_label.setText(f"Warehouse: {warehouse_qty} | Store: {store_qty}")
                        if store_qty < 10 or warehouse_qty < 10:
                            stock_info_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 5px;")
                        else:
                            stock_info_label.setStyleSheet("color: #f39c12; font-weight: bold; padding: 5px;")
        
        product_combo.currentIndexChanged.connect(update_stock_info)
        
        form_layout.addRow("Product:", product_combo)
        form_layout.addRow("Current Stock:", stock_info_label)
        form_layout.addRow("Quantity:", quantity_input)
        form_layout.addRow("From:", from_combo)
        form_layout.addRow("To:", to_combo)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
        """)
        
        button_box.accepted.connect(lambda: self._transfer_inventory(
            dialog, product_combo, quantity_input, from_combo, to_combo
        ))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        
        # Load products
        products = get_all_products()
        for p in products:
            display = f"{p['name']} ({p['company']})"
            product_combo.addItem(display, p['id'])
        
        dialog.exec()

    def _transfer_inventory(self, dialog, product_combo, quantity_input, from_combo, to_combo):
        """Handle inventory transfer."""
        try:
            if product_combo.currentIndex() == -1:
                raise ValueError("Select a product")
            
            quantity_text = quantity_input.text().strip()
            if not quantity_text:
                raise ValueError("Enter quantity to transfer")
            
            quantity = int(quantity_text)
            if quantity <= 0:
                raise ValueError("Quantity must be positive")

            product_id = product_combo.currentData()
            from_location = from_combo.currentText().lower()
            to_location = to_combo.currentText().lower()

            transfer_inventory(product_id, from_location, to_location, quantity)
            QMessageBox.information(self, "Success", f"Transferred {quantity} units from {from_location} to {to_location}!")
            
            dialog.accept()
            self._load_data()

        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to transfer inventory:\n{str(e)}")

    def _load_data(self):
        try:
            products = get_all_products()
            
            # Calculate totals
            warehouse_total = sum(p.get('warehouse_quantity', 0) for p in products)
            store_total = sum(p.get('store_quantity', 0) for p in products)
            low_stock_items = get_low_stock_products(threshold=10, location='store')
            
            # Update summary cards
            self.warehouse_card.value_label.setText(str(warehouse_total))
            self.store_card.value_label.setText(str(store_total))
            self.low_stock_card.value_label.setText(str(len(low_stock_items)))
            
            # Update table
            self.table.setRowCount(len(products))
            for row, prod in enumerate(products):
                warehouse_qty = prod.get('warehouse_quantity', 0)
                store_qty = prod.get('store_quantity', 0)
                total_qty = prod.get('quantity', 0)
                cost_price = prod.get('cost_price', 0)
                
                self.table.setItem(row, 0, QTableWidgetItem(str(prod["id"])))
                self.table.setItem(row, 1, QTableWidgetItem(prod["name"]))
                self.table.setItem(row, 2, QTableWidgetItem(prod["company"]))
                self.table.setItem(row, 3, QTableWidgetItem(f"${cost_price:.2f}"))
                
                # Warehouse quantity with low stock alert
                warehouse_item = QTableWidgetItem(str(warehouse_qty))
                if warehouse_qty <= 10:
                    warehouse_item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(row, 4, warehouse_item)
                
                # Store quantity with low stock alert
                store_item = QTableWidgetItem(str(store_qty))
                if store_qty <= 10:
                    store_item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(row, 5, store_item)
                
                self.table.setItem(row, 6, QTableWidgetItem(str(total_qty)))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load inventory:\n{str(e)}")
