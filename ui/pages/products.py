# ui/pages/products.py code 
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QMessageBox, QAbstractItemView, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from core.database import get_all_products, delete_product
from ui.dialogs.add_product import AddProductDialog

class ProductsPage(QWidget):
    def __init__(self):
        super().__init__()
        # Add search debouncing timer (300ms delay)
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.load_data)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Products list")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        header_layout.addWidget(title)

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setStyleSheet("""
            background-color: #3498db;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 5px;
            font-weight: bold;
        """)
        self.refresh_btn.clicked.connect(self.load_data)
        header_layout.addWidget(self.refresh_btn)

        # Search
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search products...")
        self.search_bar.setStyleSheet("""
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
        """)
        # Use debounced search to avoid excessive queries while typing
        self.search_bar.textChanged.connect(lambda: self.search_timer.start(300))
        header_layout.addWidget(self.search_bar)

        # Add button
        self.add_btn = QPushButton("Add Product")
        self.add_btn.setStyleSheet("""
            background-color: #27ae60;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
        """)
        self.add_btn.clicked.connect(self._add_product)
        header_layout.addWidget(self.add_btn)

        layout.addLayout(header_layout)

        # Table
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["Product ID", "Name", "Company", "Cost_Price", "Total Qty", "Warehouse", "Store", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
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
        """)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.table)

        self.load_data()

    def load_data(self):
        try:
            search = self.search_bar.text().strip()
            products = get_all_products(search)
            self.table.setRowCount(len(products))
            
            for row, prod in enumerate(products):
                self.table.setItem(row, 0, QTableWidgetItem(str(prod["id"])))
                self.table.setItem(row, 1, QTableWidgetItem(prod["name"]))
                self.table.setItem(row, 2, QTableWidgetItem(prod["company"]))
                self.table.setItem(row, 3, QTableWidgetItem(f"{prod['cost_price']:.2f}"))
                self.table.setItem(row, 4, QTableWidgetItem(str(prod["quantity"])))
                
                # Warehouse quantity with low stock alert
                warehouse_qty = prod.get("warehouse_quantity", 0)
                warehouse_item = QTableWidgetItem(str(warehouse_qty))
                if warehouse_qty <= 10:
                    warehouse_item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(row, 5, warehouse_item)
                
                # Store quantity with low stock alert
                store_qty = prod.get("store_quantity", 0)
                store_item = QTableWidgetItem(str(store_qty))
                if store_qty <= 10:
                    store_item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(row, 6, store_item)
                
                # Action buttons
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(4, 2, 4, 2)
                action_layout.setSpacing(6)
                
                edit_btn = QPushButton("Edit")
                edit_btn.setStyleSheet("""
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                """)
                edit_btn.clicked.connect(lambda _, p=prod: self._edit_product(p))
                
                delete_btn = QPushButton("Delete")
                delete_btn.setStyleSheet("""
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                """)
                delete_btn.clicked.connect(lambda _, p=prod: self._delete_product(p))
                
                action_layout.addWidget(edit_btn)
                action_layout.addWidget(delete_btn)
                action_layout.addStretch()
                
                self.table.setCellWidget(row, 7, action_widget)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load products:\n{str(e)}")

    def _add_product(self):
        dialog = AddProductDialog(self)
        if dialog.exec():
            self.load_data()

    def _edit_product(self, product):
        dialog = AddProductDialog(self, product)
        if dialog.exec():
            self.load_data()

    def _delete_product(self, product):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete '{product['name']}'?\n This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                delete_product(product["id"])
                self.load_data()
                QMessageBox.information(self, "Success", "Product deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete product: \n{str(e)}")