# ui/pages/daily_profit.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QMessageBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.database import get_db_connection, calculate_daily_profit, calculate_total_expenses
from datetime import datetime

class DailyProfitPage(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header: title + small refresh button on top right
        header_layout = QHBoxLayout()

        title = QLabel("Daily Sales & Profit")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setStyleSheet("""
            background-color: #3498db;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 5px;
            font-weight: bold;
        """)
        self.refresh_btn.clicked.connect(self._load_data)
        header_layout.addWidget(self.refresh_btn)

        layout.addLayout(header_layout)

        # State cards
        state_layout = QHBoxLayout()
        state_layout.setSpacing(20)

        # Store card references so we can update them later
        self.total_sales_card = self._create_state_card("Total Sales", "total_sales", "#3498db")
        self.total_profit_card = self._create_state_card("Gross Profit", "total_profit", "#27ae60")
        self.expenses_card = self._create_state_card("Expenses", "expenses", "#e74c3c")
        self.net_profit_card = self._create_state_card("Net Profit", "net_profit", "#16a085")
        self.profit_margin_card = self._create_state_card("Profit Margin", "profit_margin", "#9b59b6")

        state_layout.addWidget(self.total_sales_card)
        state_layout.addWidget(self.total_profit_card)
        state_layout.addWidget(self.expenses_card)
        state_layout.addWidget(self.net_profit_card)
        state_layout.addWidget(self.profit_margin_card)
        layout.addLayout(state_layout)

        # Daily breakdown
        breakdown_title = QLabel("Today's Sales Breakdown")
        breakdown_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        breakdown_title.setStyleSheet("color: #2c3e50; margin: 20px 0 10px 0;")
        layout.addWidget(breakdown_title)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Time", "Sale Type", "Amount", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.table)

        self._load_data()

    def _create_state_card(self, title, value_type, color):
        card = QFrame()
        # Use gradient that works in both themes
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
        value_label.setStyleSheet("color: white; margin-top: 5px;")  # Explicitly set white text
        card_layout.addWidget(value_label)
        
        # Store reference to value label so we can update it later
        card.value_label = value_label
        card.value_type = value_type  # Store the type for later use
        
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

    def _load_data(self):
        try:
            # Get profit data
            profit_data = calculate_daily_profit()
            
            # Get today's expenses
            today = datetime.now().strftime("%Y-%m-%d")
            today_expenses = calculate_total_expenses(today, today)
            
            # Calculate net profit
            gross_profit = profit_data['profit']
            net_profit = gross_profit - today_expenses
            
            # Update all card values
            for card in [self.total_sales_card, self.total_profit_card, self.expenses_card, self.net_profit_card, self.profit_margin_card]:
                value_type = card.value_type
                if value_type == "total_sales":
                    card.value_label.setText(f"${profit_data['total_sales']:.2f}")
                elif value_type == "total_profit":
                    card.value_label.setText(f"${gross_profit:.2f}")
                elif value_type == "expenses":
                    card.value_label.setText(f"${today_expenses:.2f}")
                elif value_type == "net_profit":
                    card.value_label.setText(f"${net_profit:.2f}")
                elif value_type == "profit_margin":
                    if profit_data['total_sales'] > 0:
                        margin_percent = (net_profit / profit_data['total_sales']) * 100
                        card.value_label.setText(f"{margin_percent:.1f}%")
                    else:
                        card.value_label.setText("0%")
            
            # Get detailed sales for the table
            with get_db_connection() as conn:
                # Get today's sales
                cursor = conn.execute("""
                    SELECT date, sale_type, total, paid_amount
                    FROM sales
                    WHERE date(date) = date('now')
                    ORDER BY date DESC
                """)
                sales_data = cursor.fetchall()
                
                # Format sales for display
                all_sales = []
                for sale in sales_data:
                    sale_type_display = "Wholesale" if sale['sale_type'] == 'wholesale' else "Retail"
                    all_sales.append((sale['date'], sale_type_display, sale['total'], 
                                    "Paid" if sale['paid_amount'] >= sale['total'] else "Partial"))
                
                # Sort by time (newest first)
                all_sales.sort(key=lambda x: x[0], reverse=True)
                
                # Update table
                self.table.setRowCount(len(all_sales))
                for row, (date, sale_type, total, status) in enumerate(all_sales):
                    self.table.setItem(row, 0, QTableWidgetItem(date))
                    self.table.setItem(row, 1, QTableWidgetItem(sale_type))
                    self.table.setItem(row, 2, QTableWidgetItem(f"${total:.2f}"))
                    self.table.setItem(row, 3, QTableWidgetItem(status))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load report:\n{str(e)}")