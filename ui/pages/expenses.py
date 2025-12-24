# ui/pages/expenses.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QMessageBox,
    QFormLayout, QDateEdit, QFrame, QSizePolicy, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from core.database import (
    add_expense, get_expenses_by_date_range, delete_expense,
    calculate_total_expenses, get_expenses_by_category_summary
)

class ExpensesPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                color: white;
            }
            QLineEdit, QComboBox, QDateEdit {
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
        title = QLabel("Expenses Management")
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
        
        self.today_expense_card = self._create_summary_card("Today's Expenses", "$0.00", "#e74c3c")
        self.month_expense_card = self._create_summary_card("This Month", "$0.00", "#c0392b")
        self.total_expense_card = self._create_summary_card("Total (Period)", "$0.00", "#8e44ad")
        
        summary_layout.addWidget(self.today_expense_card)
        summary_layout.addWidget(self.month_expense_card)
        summary_layout.addWidget(self.total_expense_card)
        summary_layout.addStretch()
        layout.addLayout(summary_layout)
        
        # Make cards expandable
        self.today_expense_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.month_expense_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.total_expense_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Action buttons section
        actions_section = QFrame()
        actions_section.setStyleSheet("background-color: #34495e; border-radius: 2px; padding: 10px;")
        actions_layout = QVBoxLayout(actions_section)
        
        actions_title = QLabel("Expense Actions click to add expense")
        actions_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        actions_title.setStyleSheet("color: white; margin-bottom: 2px;")
        actions_layout.addWidget(actions_title)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        add_expense_btn = QPushButton("Add Expense")
        add_expense_btn.setStyleSheet("background-color: #27ae60; color: white; min-width: 150px;")
        add_expense_btn.clicked.connect(self._show_add_expense_dialog)
        buttons_layout.addWidget(add_expense_btn)
        
        buttons_layout.addStretch()
        actions_layout.addLayout(buttons_layout)
        layout.addWidget(actions_section)

        # Filters
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("From:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        filter_layout.addWidget(self.start_date)

        filter_layout.addWidget(QLabel("To:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        filter_layout.addWidget(self.end_date)

        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        self.category_filter.addItems([
            "Rent", "Utilities", "Salaries", "Supplies", "Marketing", 
            "Transportation", "Maintenance", "Other"
        ])
        filter_layout.addWidget(self.category_filter)

        filter_btn = QPushButton("Filter")
        filter_btn.setStyleSheet("background-color: #9b59b6; color: white;")
        filter_btn.clicked.connect(self._load_data)
        filter_layout.addWidget(filter_btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Expenses table
        table_title = QLabel("Expenses List")
        table_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        table_title.setStyleSheet("color: white; margin-top: 15px;")
        layout.addWidget(table_title)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "Date", "Category", "Description", "Amount", "Notes", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
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

    def _show_add_expense_dialog(self):
        """Show add expense dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Expense")
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
        form_layout.setSpacing(10)
        
        date_input = QDateEdit()
        date_input.setDate(QDate.currentDate())
        date_input.setCalendarPopup(True)
        date_input.setStyleSheet("""
            background-color: #34495e;
            color: white;
            border: 1px solid #7f8c8d;
            border-radius: 4px;
            padding: 6px;
        """)
        form_layout.addRow("Date:", date_input)
        
        category_combo = QComboBox()
        category_combo.setEditable(True)
        category_combo.addItems([
            "Rent", "Utilities", "Salaries", "Supplies", "Marketing", 
            "Transportation", "Maintenance", "Other"
        ])
        category_combo.setStyleSheet("""
            background-color: #34495e;
            color: white;
            border: 1px solid #7f8c8d;
            border-radius: 4px;
            padding: 6px;
        """)
        form_layout.addRow("Category:", category_combo)
        
        description_input = QLineEdit()
        description_input.setPlaceholderText("Enter expense description")
        description_input.setStyleSheet("""
            background-color: #34495e;
            color: white;
            border: 1px solid #7f8c8d;
            border-radius: 4px;
            padding: 6px;
        """)
        form_layout.addRow("Description:", description_input)
        
        amount_input = QLineEdit()
        amount_input.setPlaceholderText("0.00")
        amount_input.setStyleSheet("""
            background-color: #34495e;
            color: white;
            border: 1px solid #7f8c8d;
            border-radius: 4px;
            padding: 6px;
        """)
        form_layout.addRow("Amount ($):", amount_input)
        
        notes_input = QLineEdit()
        notes_input.setPlaceholderText("Optional notes")
        notes_input.setStyleSheet("""
            background-color: #34495e;
            color: white;
            border: 1px solid #7f8c8d;
            border-radius: 4px;
            padding: 6px;
        """)
        form_layout.addRow("Notes:", notes_input)
        
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
        
        button_box.accepted.connect(lambda: self._add_expense(
            dialog, date_input, category_combo, description_input, amount_input, notes_input
        ))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        dialog.exec()

    def _add_expense(self, dialog, date_input, category_combo, description_input, amount_input, notes_input):
        """Handle adding expense."""
        try:
            category = category_combo.currentText().strip()
            description = description_input.text().strip()
            amount_text = amount_input.text().strip()
            notes = notes_input.text().strip()
            expense_date = date_input.date().toString("yyyy-MM-dd")

            if not category:
                raise ValueError("Category is required")
            if not description:
                raise ValueError("Description is required")
            if not amount_text:
                raise ValueError("Amount is required")
            
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError("Amount must be positive")

            add_expense(category, description, amount, notes, expense_date)
            QMessageBox.information(self, "Success", "Expense added successfully!")
            
            dialog.accept()
            self._load_data()

        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add expense:\n{str(e)}")

    def _load_data(self):
        try:
            start_date = self.start_date.date().toString("yyyy-MM-dd")
            end_date = self.end_date.date().toString("yyyy-MM-dd")
            category_filter = self.category_filter.currentText()

            # Get expenses
            category = None if category_filter == "All Categories" else category_filter
            expenses = get_expenses_by_date_range(start_date, end_date, category)

            # Calculate totals
            total_period = calculate_total_expenses(start_date, end_date)
            
            # Today's expenses
            today = QDate.currentDate().toString("yyyy-MM-dd")
            today_total = calculate_total_expenses(today, today)
            
            # This month's expenses
            month_start = QDate.currentDate().addDays(-QDate.currentDate().day() + 1).toString("yyyy-MM-dd")
            month_end = QDate.currentDate().toString("yyyy-MM-dd")
            month_total = calculate_total_expenses(month_start, month_end)

            # Update summary cards
            self.today_expense_card.value_label.setText(f"${today_total:.2f}")
            self.month_expense_card.value_label.setText(f"${month_total:.2f}")
            self.total_expense_card.value_label.setText(f"${total_period:.2f}")

            # Update table
            self.table.setRowCount(len(expenses))
            for row, expense in enumerate(expenses):
                self.table.setItem(row, 0, QTableWidgetItem(expense['date']))
                self.table.setItem(row, 1, QTableWidgetItem(expense['category']))
                self.table.setItem(row, 2, QTableWidgetItem(expense['description']))
                self.table.setItem(row, 3, QTableWidgetItem(f"${expense['amount']:.2f}"))
                self.table.setItem(row, 4, QTableWidgetItem(expense.get('notes', '')))

                # Delete button
                delete_btn = QPushButton("Delete")
                delete_btn.setStyleSheet("background-color: #e74c3c; color: white;")
                delete_btn.clicked.connect(lambda _, eid=expense['id']: self._delete_expense(eid))
                self.table.setCellWidget(row, 5, delete_btn)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load expenses:\n{str(e)}")

    def _delete_expense(self, expense_id: int):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this expense?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                delete_expense(expense_id)
                QMessageBox.information(self, "Success", "Expense deleted successfully!")
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete expense:\n{str(e)}")
