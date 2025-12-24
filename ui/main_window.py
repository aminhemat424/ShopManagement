# ui/main_window.py
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QStackedWidget, QPushButton, QLabel,QMessageBox
)
from PyQt6.QtCore import Qt

from ui.pages import (
    DashboardPage, CustomersPage, ProductsPage,PurchasePage,
    SalesPage, DailyProfitPage, MonthlyProfitPage,SalesReportPage,SettingsPage,
    ExpensesPage, InventoryPage
)
from ui.pages.dues import DuesPage
from ui.style import SIDEBAR_BUTTON_STYLE, ACTION_BUTTON_STYLE
from ui.dialogs.add_customer import AddCustomerDialog
from ui.dialogs.add_product import AddProductDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shop_APP")
        self.resize(1150, 800)
        self.setStyleSheet("Background-color: #111C27")
        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = self._create_sidebar()
        main_layout.addWidget(self.sidebar)

        # Content area
        content_frame = self._create_content_area()
        main_layout.addWidget(content_frame)

    def _create_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("background-color: #2c3e50; border-right: 1px solid #34495e;")
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title1 = QLabel("شلګر چیني فروشي")
        title1.setStyleSheet("color: white; font-size: 22px; font-weight: bold; padding: 25px 0 20px 25px;")
        layout.addWidget(title1)

        self.nav_buttons = []
        pages = [
            ("Dashboard", DashboardPage),
            ("Customers", CustomersPage),
            ("Products", ProductsPage),
            ("Perchase", PurchasePage),
            ("Sales repots", SalesReportPage),
            ("Dues ",DuesPage),
            ("Expenses", ExpensesPage),
            ("Inventory", InventoryPage),
            ("Daily Profit", DailyProfitPage),
            ("Monthly Profit", MonthlyProfitPage),
            ("Settings", SettingsPage),
        ]

        for text, page_class in pages:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setStyleSheet(SIDEBAR_BUTTON_STYLE)
            btn.clicked.connect(lambda _, p=page_class, b=btn: self._switch_page(p, b))
            layout.addWidget(btn)
            self.nav_buttons.append(btn)

        layout.addStretch()
        self.nav_buttons[0].setChecked(True)
        return sidebar

    def _create_content_area(self):
        # Top action bar
        top_bar = QFrame()
        top_bar.setFixedHeight(65)
        top_bar.setStyleSheet("background-color: white; border-bottom: 1px solid #e0e0e0;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(25, 10, 25, 10)
        top_layout.setSpacing(12)

        actions = [
            ("Add Product", self._add_product),
            ("Add Customer", self._add_customer),
            ("New Sale", self._new_sale),
            ("Weekly Report", self._weekly_report),
        ]

        for text, handler in actions:
            btn = QPushButton(text)
            btn.setStyleSheet(ACTION_BUTTON_STYLE)
            btn.clicked.connect(handler)
            top_layout.addWidget(btn)
        top_layout.addStretch()

        # Stacked widget
        self.stack = QStackedWidget()
        self.pages = {}
        for _, PageClass in [
            (None, DashboardPage),
            (None, CustomersPage),
            (None, ProductsPage),
            (None, PurchasePage),
            (None, SalesPage),
            (None, DuesPage),
            (None, ExpensesPage),
            (None, InventoryPage),
            (None, SalesReportPage),
            (None, DailyProfitPage),
            (None, MonthlyProfitPage),
            (None, SettingsPage),
        ]:
            page = PageClass()
            self.stack.addWidget(page)
            self.pages[PageClass] = page

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(top_bar)
        content_layout.addWidget(self.stack)

        frame = QFrame()
        frame.setLayout(content_layout)
        return frame
    

    
    def _apply_theme(self,is_dark):
        if is_dark:
            # Dark theme
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2c3e50;
                }
                QLabel {
                    color: #ecf0f1;
                }
                QLineEdit {
                    background-color: #34495e;
                    color: #ecf0f1;
                    border: 1px solid #7f8c8d;
                }
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                }
                QTableWidget {
                    background-color: #34495e;
                    color: #ecf0f1;
                    gridline-color: #7f8c8d;
                }
                QHeaderView::section {
                    background-color: #3c5a75;
                    color: #ecf0f1;
                }
            """)
        else:
            self.setStyleSheet("")


    def _switch_page(self, page_class, active_btn):
        for btn in self.nav_buttons:
            btn.setChecked(btn == active_btn)
        self.stack.setCurrentWidget(self.pages[page_class])

    def _add_product(self):
        dialog = AddProductDialog(self)
        dialog.exec()
        if hasattr(self.pages[ProductsPage], 'load_data'):
            self.pages[ProductsPage].load_data()

    def _add_customer(self):
        dialog = AddCustomerDialog(self)
        dialog.exec()
        if hasattr(self.pages[CustomersPage], 'load_data'):
            self.pages[CustomersPage].load_data()

    def _new_sale(self):
        self._switch_page(SalesPage, self.nav_buttons[3])

    def _sales_report(self):
        self._switch_page(SalesReportPage, self.nav_buttons[4])  

    def _weekly_report(self):
        print("Weekly report clicked")