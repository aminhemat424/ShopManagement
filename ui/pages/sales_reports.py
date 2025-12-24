# ui/pages/sales_report.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QMessageBox, QFrame,
    QComboBox, QDateEdit, QSizePolicy
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from core.database import get_sales_by_date_range

class SalesReportPage(QWidget):
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
            QComboBox, QDateEdit {
                background-color: #34495e;
                color: white;
                border: 1px solid #7f8c8d;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Sales Reports")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: white; margin-bottom: 20px;")
        layout.addWidget(title)

        # Date filter controls
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("From:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.start_date.setCalendarPopup(True)
        filter_layout.addWidget(self.start_date)
        
        filter_layout.addWidget(QLabel("To:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        filter_layout.addWidget(self.end_date)
        
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All Sales", "Retail", "Wholesale"])
        filter_layout.addWidget(self.type_filter)
        
        self.refresh_btn = QPushButton("🔄 Refresh Report")
        self.refresh_btn.setStyleSheet("""
            background-color: #9b59b6;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 5px;
            font-weight: bold;
        """)
        self.refresh_btn.clicked.connect(self._load_data)
        filter_layout.addWidget(self.refresh_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Summary cards
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(20)

        self.wholesale_card = self._create_summary_card("Wholesale Sales", "$0.00", "#3498db")
        self.retail_card = self._create_summary_card("Retail Sales", "$0.00", "#27ae60")
        self.total_sales_card = self._create_summary_card("Total Sales", "$0.00", "#9b59b6")

        summary_layout.addWidget(self.wholesale_card)
        summary_layout.addWidget(self.retail_card)
        summary_layout.addWidget(self.total_sales_card)
        layout.addLayout(summary_layout)

        # Sales table
        breakdown_title = QLabel("Sales Breakdown")
        breakdown_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        breakdown_title.setStyleSheet("color: white; margin: 20px 0 10px 0;")
        layout.addWidget(breakdown_title)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "Date", "Product", "Customer", "Qty", "Total", "Profit", "Type", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        self.table.setStyleSheet("""
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
                border: 1px solid #7f8c8d;
                font-weight: bold;
            }
        """)
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
                padding: 10px;
                min-height: 10px;
                max-height: 100px
            }}
            QLabel {{
                color: white;
                font-weight: bold;
            }}
        """)
        card_layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; color: white;")
        
        self.value_labels = getattr(self, 'value_labels', {})
        value_key = title.replace(" ", "_").lower()
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 20px; font-weight: bold; color: white; margin-top: 5px;")
        self.value_labels[value_key] = value_label
        
        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)
        card_layout.addStretch()
        
        return card

    def _lighten_color(self, color, factor):
        """Lighten a hex color by blending with white."""
        color = color.lstrip('#')
        if len(color) != 6:
            return "#ffffff"
        r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _load_data(self):
        try:
            # Load main sales data
            start_date = self.start_date.date().toString("yyyy-MM-dd")
            end_date = self.end_date.date().toString("yyyy-MM-dd")
            sale_type_filter = self.type_filter.currentText()
            
            type_map = {
                "All Sales": None,
                "Retail": "retail",
                "Wholesale": "wholesale"
            }
            sale_type = type_map.get(sale_type_filter)
            
            sales_data = get_sales_by_date_range(start_date, end_date, sale_type)
            
            # Sort by date descending (most recent first)
            # Handle date strings properly
            def get_sort_key(sale):
                date_str = sale.get("date", "")
                if not date_str:
                    return ""
                # Return as-is for sorting (already in YYYY-MM-DD format)
                return str(date_str)
            
            sales_data.sort(key=get_sort_key, reverse=True)
            
            # Calculate totals
            wholesale_total = 0.0
            retail_total = 0.0
            
            self.table.setRowCount(len(sales_data))
            for row, sale in enumerate(sales_data):
                date_str = sale.get("date", "")
                if date_str:
                    # Format date for better display
                    try:
                        from datetime import datetime
                        dt = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
                        date_str = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        pass
                
                self.table.setItem(row, 0, QTableWidgetItem(date_str))
                self.table.setItem(row, 1, QTableWidgetItem(sale.get("product_name", "")))
                self.table.setItem(row, 2, QTableWidgetItem(sale.get("customer_name") or "N/A"))
                self.table.setItem(row, 3, QTableWidgetItem(str(sale.get("quantity", 0))))
                self.table.setItem(row, 4, QTableWidgetItem(f"${sale.get('total', 0):.2f}"))
                self.table.setItem(row, 5, QTableWidgetItem(f"${sale.get('profit', 0):.2f}"))
                self.table.setItem(row, 6, QTableWidgetItem(sale.get("sale_type", "").title()))
                
                due_amount = sale.get("due_amount", 0)
                status = "Paid" if abs(float(due_amount)) < 0.01 else "Partial"
                self.table.setItem(row, 7, QTableWidgetItem(status))
                
                sale_type_str = sale.get("sale_type", "")
                if sale_type_str == "wholesale":
                    wholesale_total += float(sale.get("total", 0))
                else:
                    retail_total += float(sale.get("total", 0))
            
            total_total = wholesale_total + retail_total
            
            # Update summary cards
            self.value_labels["wholesale_sales"].setText(f"${wholesale_total:.2f}")
            self.value_labels["retail_sales"].setText(f"${retail_total:.2f}")
            self.value_labels["total_sales"].setText(f"${total_total:.2f}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load report:\n{str(e)}")