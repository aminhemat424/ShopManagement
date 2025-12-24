# ui/pages/dashboard.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.database import (
    get_all_products, get_all_customers, calculate_daily_profit,
    calculate_total_expenses, get_low_stock_products
)
from datetime import datetime


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self.value_labels = {}
        self._init_ui()
        self.setStyleSheet("background-color: #2c3e50;")
        self._refresh_page()  # Load data immediately

    def _init_ui(self):
        # Main scrollable layout
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)

        # ===== HEADER: Title + Refresh Button =====
        header_layout = QHBoxLayout()

        title = QLabel("د حساب خلاصه")
        title.setFont(QFont("Segoe UI", 25, QFont.Weight.Bold))
        title.setStyleSheet("background-color: #111C27; color: white; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setObjectName("refreshButton")
        self.refresh_btn.setStyleSheet("""
            QPushButton#refreshButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton#refreshButton:hover {
                background-color: #2980b9;
            }
        """)
        self.refresh_btn.clicked.connect(self._refresh_page)
        header_layout.addWidget(self.refresh_btn)

        layout.addLayout(header_layout)

        # ===== STATS ROW 1 =====
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)

        products_card = self._create_stat_card("Products", "total_products", "#3498db", "")
        customers_card = self._create_stat_card("Customers", "total_customers", "#27ae60", "")
        sales_card = self._create_stat_card("Today's Sales", "today_sales", "#e74c3c", "")
        profit_card = self._create_stat_card("Today's Profit", "today_profit", "#f39c12", "")

        stats_layout.addWidget(products_card)
        stats_layout.addWidget(customers_card)
        stats_layout.addWidget(sales_card)
        stats_layout.addWidget(profit_card)
        stats_layout.addStretch()

        layout.addLayout(stats_layout)
        
        # Make cards expandable
        products_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        customers_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sales_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        profit_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # ===== STATS ROW 2 =====
        stats_layout2 = QHBoxLayout()
        stats_layout2.setSpacing(15)

        expenses_card = self._create_stat_card("Today's Expenses", "today_expenses", "#e74c3c", "")
        warehouse_card = self._create_stat_card("Warehouse Stock", "warehouse_stock", "#8e44ad", "")
        store_card = self._create_stat_card("Store Stock", "store_stock", "#16a085", "")
        low_stock_card = self._create_stat_card("Low Stock Items", "low_stock", "#d35400", "")

        stats_layout2.addWidget(expenses_card)
        stats_layout2.addWidget(warehouse_card)
        stats_layout2.addWidget(store_card)
        stats_layout2.addWidget(low_stock_card)
        stats_layout2.addStretch()

        layout.addLayout(stats_layout2)
        
        # Make cards expandable
        expenses_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        warehouse_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        store_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        low_stock_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Store card references for refresh
        self.value_labels = {
            "total_products": products_card,
            "total_customers": customers_card,
            "today_sales": sales_card,
            "today_profit": profit_card,
            "today_expenses": expenses_card,
            "warehouse_stock": warehouse_card,
            "store_stock": store_card,
            "low_stock": low_stock_card
        }

        layout.addStretch()  # Push everything to top
        
        scroll.setWidget(content)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _refresh_page(self):
        try:
            products = get_all_products()
            customers = get_all_customers()
            daily_data = calculate_daily_profit()
            
            # Today's expenses
            today = datetime.now().strftime("%Y-%m-%d")
            today_expenses = calculate_total_expenses(today, today)
            
            # Calculate warehouse and store stock quantities (not values)
            warehouse_qty = sum(p.get('warehouse_quantity', 0) for p in products)
            store_qty = sum(p.get('store_quantity', 0) for p in products)
            
            # Low stock items (store quantity <= 10)
            low_stock_items = get_low_stock_products(threshold=10, location='store')

            # Update all card values
            for value_type, card in self.value_labels.items():
                if value_type == "total_products":
                    card.value_label.setText(str(len(products)))
                elif value_type == "total_customers":
                    card.value_label.setText(str(len(customers)))
                elif value_type == "today_sales":
                    card.value_label.setText(f"${daily_data['total_sales']:.2f}")
                elif value_type == "today_profit":
                    card.value_label.setText(f"${daily_data['profit']:.2f}")
                elif value_type == "today_expenses":
                    card.value_label.setText(f"${today_expenses:.2f}")
                elif value_type == "warehouse_stock":
                    card.value_label.setText(str(warehouse_qty))
                elif value_type == "store_stock":
                    card.value_label.setText(str(store_qty))
                elif value_type == "low_stock":
                    card.value_label.setText(str(len(low_stock_items)))
        except Exception as e:
            print(f"Refresh error: {e}")

    def _create_stat_card(self, title, value_type, color, icon):
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
        value_label = QLabel("0")
        value_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        value_label.setStyleSheet("color: white; margin-top: 5px;")
        card_layout.addWidget(value_label)
        
        # Store reference to value label so we can update it later
        card.value_label = value_label
        card.value_type = value_type
        
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