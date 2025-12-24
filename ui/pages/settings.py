# ui/pages/settings.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, 
    QCheckBox, QMessageBox, QFileDialog, QComboBox, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, QDate, QSize
from PyQt6.QtGui import QFont
import csv
import os
import shutil
from datetime import datetime
from core.database import (
    get_all_products, get_all_customers, get_sales_by_date_range,
    get_expenses_by_date_range, get_db_connection, DB_FILE
)

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.is_dark_theme = False
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                color: white;
            }
            QLabel {
                color: white;
            }
            QComboBox, QLineEdit {
                background-color: #34495e;
                color: white;
                border: 1px solid #7f8c8d;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        
        # Main scrollable layout
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Settings")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        
        # Export Section - CSV
        export_csv_section = self._create_section("Export to CSV", [
            ("Export Products", lambda: self._export_data("CSV", "All Products"), "#3498db"),
            ("Export Customers", lambda: self._export_data("CSV", "All Customers"), "#27ae60"),
            ("Export Sales", lambda: self._export_data("CSV", "All Sales"), "#e74c3c"),
            ("Export Expenses", lambda: self._export_data("CSV", "All Expenses"), "#f39c12"),
            ("Export Sales Report", lambda: self._export_data("CSV", "Sales Report"), "#9b59b6"),
            ("Export Expenses Report", lambda: self._export_data("CSV", "Expenses Report"), "#8e44ad"),
            ("Export Inventory Report", lambda: self._export_data("CSV", "Inventory Report"), "#16a085"),
        ])
        layout.addWidget(export_csv_section)

        # Export Section - PDF
        export_pdf_section = self._create_section("Export to PDF", [
            ("Export Products", lambda: self._export_data("PDF", "All Products"), "#3498db"),
            ("Export Sales", lambda: self._export_data("PDF", "All Sales"), "#e74c3c"),
            ("Export Expenses", lambda: self._export_data("PDF", "All Expenses"), "#f39c12"),
            ("Export Inventory Report", lambda: self._export_data("PDF", "Inventory Report"), "#16a085"),
        ])
        layout.addWidget(export_pdf_section)

        # Database Management Section
        db_section = self._create_section("Database Management", [
            ("Backup Database", self._backup_database, "#3498db"),
            ("Restore Database", self._restore_database, "#f39c12"),
        ])
        layout.addWidget(db_section)

        # System Information
        info_section = self._create_section("System Information", [
            ("Database Size", self._show_db_size, "#95a5a6"),
            ("Database Path", self._show_db_path, "#95a5a6"),
        ])
        layout.addWidget(info_section)

        layout.addStretch()
        
        scroll.setWidget(content)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _create_section(self, title, buttons):
        """Create a section with title and buttons."""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: #34495e;
                border-radius: 10px;
                border: 1px solid #7f8c8d;
                padding: 15px;
            }
        """)
        section.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        layout = QVBoxLayout(section)
        layout.setSpacing(12)
        
        section_title = QLabel(title)
        section_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        section_title.setStyleSheet("color: white; margin-bottom: 5px;")
        layout.addWidget(section_title)
        
        # Create buttons grid
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        for btn_text, handler, color in buttons:
            btn = QPushButton(btn_text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    padding: 10px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 12px;
                    min-width: 120px;
                }}
                QPushButton:hover {{
                    background-color: {self._darken_color(color, 0.1)};
                }}
            """)
            btn.clicked.connect(handler)
            buttons_layout.addWidget(btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        return section

    def _darken_color(self, color, factor):
        """Darken a color by a factor."""
        import colorsys
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        h, s, v = colorsys.rgb_to_hsv(*[x/255.0 for x in rgb])
        v = max(0.0, v - factor)
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

    def _toggle_theme(self):
        """Toggle between dark and light theme."""
        self.is_dark_theme = not self.is_dark_theme
        if hasattr(self.parent().parent(), '_apply_theme'):
            self.parent().parent()._apply_theme(self.is_dark_theme)
        # Update button text
        self.theme_btn.setText("Toggle Light Theme" if self.is_dark_theme else "Toggle Dark Theme")
        QMessageBox.information(
            self, "Theme Changed", 
            f"Theme changed to {'Dark' if self.is_dark_theme else 'Light'} mode."
        )

    def _show_db_size(self):
        """Show database size information."""
        size = self._get_database_size()
        QMessageBox.information(self, "Database Size", f"Database Size: {size}")

    def _show_db_path(self):
        """Show database path information."""
        path = os.path.abspath(DB_FILE)
        QMessageBox.information(self, "Database Path", f"Database Path:\n{path}")

    def _get_database_size(self):
        """Get database file size in human-readable format."""
        try:
            if os.path.exists(DB_FILE):
                size = os.path.getsize(DB_FILE)
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size < 1024.0:
                        return f"{size:.2f} {unit}"
                    size /= 1024.0
                return f"{size:.2f} TB"
            return "0 B"
        except:
            return "Unknown"

    def _backup_database(self):
        try:
            if not os.path.exists(DB_FILE):
                QMessageBox.warning(self, "Error", "Database file not found!")
                return

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"shop_backup_{timestamp}.db"
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Database Backup", default_name, "Database Files (*.db);;All Files (*)"
            )

            if file_path:
                shutil.copy2(DB_FILE, file_path)
                QMessageBox.information(self, "Success", f"Database backed up successfully!\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to backup database:\n{str(e)}")

    def _restore_database(self):
        try:
            reply = QMessageBox.question(
                self, "Confirm Restore",
                "This will replace your current database with the backup.\n"
                "Are you sure you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "Select Backup File", "", "Database Files (*.db);;All Files (*)"
                )

                if file_path:
                    shutil.copy2(file_path, DB_FILE)
                    QMessageBox.information(
                        self, "Success", 
                        "Database restored successfully!\nPlease restart the application."
                    )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to restore database:\n{str(e)}")

    def _export_data(self, export_format, export_type):
        """Export data handler."""
        try:
            if export_format == "CSV":
                self._export_to_csv(export_type)
            else:
                self._export_to_pdf(export_type)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export data:\n{str(e)}")

    def _export_to_csv(self, export_type):
        """Export data to CSV file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if export_type == "All Products":
            data = get_all_products()
            headers = ["ID", "Name", "Company", "Cost Price", "Quantity", "Warehouse", "Store", "Balance"]
            rows = []
            for item in data:
                rows.append([
                    item.get('id', ''),
                    item.get('name', ''),
                    item.get('company', ''),
                    item.get('cost_price', 0),
                    item.get('quantity', 0),
                    item.get('warehouse_quantity', 0),
                    item.get('store_quantity', 0),
                    item.get('balance', 0)
                ])
            default_name = f"products_{timestamp}.csv"

        elif export_type == "All Customers":
            data = get_all_customers()
            headers = ["ID", "Full Name", "WhatsApp", "Phone", "Address"]
            rows = []
            for item in data:
                rows.append([
                    item.get('id', ''),
                    item.get('full_name', ''),
                    item.get('whatsapp_number', ''),
                    item.get('phone_number', ''),
                    item.get('address', '')
                ])
            default_name = f"customers_{timestamp}.csv"

        elif export_type == "All Sales":
            data = get_sales_by_date_range("2000-01-01", datetime.now().strftime("%Y-%m-%d"))
            headers = ["Date", "Product", "Customer", "Quantity", "Total", "Profit", "Type", "Due Amount"]
            rows = []
            for item in data:
                rows.append([
                    item.get('date', ''),
                    item.get('product_name', ''),
                    item.get('customer_name', 'N/A'),
                    item.get('quantity', 0),
                    item.get('total', 0),
                    item.get('profit', 0),
                    item.get('sale_type', ''),
                    item.get('due_amount', 0)
                ])
            default_name = f"sales_{timestamp}.csv"

        elif export_type == "All Expenses":
            data = get_expenses_by_date_range("2000-01-01", datetime.now().strftime("%Y-%m-%d"))
            headers = ["Date", "Category", "Description", "Amount", "Notes"]
            rows = []
            for item in data:
                rows.append([
                    item.get('date', ''),
                    item.get('category', ''),
                    item.get('description', ''),
                    item.get('amount', 0),
                    item.get('notes', '')
                ])
            default_name = f"expenses_{timestamp}.csv"

        elif export_type == "Sales Report":
            data = get_sales_by_date_range("2000-01-01", datetime.now().strftime("%Y-%m-%d"))
            headers = ["Date", "Product", "Customer", "Quantity", "Total", "Profit", "Type"]
            rows = []
            for item in data:
                rows.append([
                    item.get('date', ''),
                    item.get('product_name', ''),
                    item.get('customer_name', 'N/A'),
                    item.get('quantity', 0),
                    item.get('total', 0),
                    item.get('profit', 0),
                    item.get('sale_type', '')
                ])
            default_name = f"sales_report_{timestamp}.csv"

        elif export_type == "Expenses Report":
            data = get_expenses_by_date_range("2000-01-01", datetime.now().strftime("%Y-%m-%d"))
            headers = ["Date", "Category", "Description", "Amount", "Notes"]
            rows = []
            for item in data:
                rows.append([
                    item.get('date', ''),
                    item.get('category', ''),
                    item.get('description', ''),
                    item.get('amount', 0),
                    item.get('notes', '')
                ])
            default_name = f"expenses_report_{timestamp}.csv"

        elif export_type == "Inventory Report":
            data = get_all_products()
            headers = ["ID", "Name", "Company", "Warehouse Qty", "Store Qty", "Total Qty", "Cost Price", "Total Value"]
            rows = []
            for item in data:
                warehouse_qty = item.get('warehouse_quantity', 0)
                store_qty = item.get('store_quantity', 0)
                total_qty = item.get('quantity', 0)
                cost_price = item.get('cost_price', 0)
                total_value = cost_price * total_qty
                rows.append([
                    item.get('id', ''),
                    item.get('name', ''),
                    item.get('company', ''),
                    warehouse_qty,
                    store_qty,
                    total_qty,
                    cost_price,
                    total_value
                ])
            default_name = f"inventory_report_{timestamp}.csv"

        else:
            QMessageBox.warning(self, "Error", "Invalid export type selected!")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV File", default_name, "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                writer.writerows(rows)
            
            QMessageBox.information(self, "Success", f"Data exported successfully!\n{file_path}")

    def _export_to_pdf(self, export_type):
        """Export data to PDF file."""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors
            from reportlab.lib.units import inch

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if export_type == "All Products":
                data = get_all_products()
                headers = ["ID", "Name", "Company", "Cost Price", "Qty", "Warehouse", "Store"]
                rows = [[item.get('id', ''), item.get('name', ''), item.get('company', ''), 
                         item.get('cost_price', 0), item.get('quantity', 0),
                         item.get('warehouse_quantity', 0), item.get('store_quantity', 0)] 
                        for item in data]
                title = "Products Report"
                default_name = f"products_{timestamp}.pdf"

            elif export_type == "All Sales":
                data = get_sales_by_date_range("2000-01-01", datetime.now().strftime("%Y-%m-%d"))
                headers = ["Date", "Product", "Customer", "Qty", "Total", "Profit", "Type"]
                rows = [[item.get('date', ''), item.get('product_name', ''), 
                         item.get('customer_name', 'N/A'), item.get('quantity', 0),
                         item.get('total', 0), item.get('profit', 0), item.get('sale_type', '')] 
                        for item in data]
                title = "Sales Report"
                default_name = f"sales_{timestamp}.pdf"

            elif export_type == "All Expenses":
                data = get_expenses_by_date_range("2000-01-01", datetime.now().strftime("%Y-%m-%d"))
                headers = ["Date", "Category", "Description", "Amount"]
                rows = [[item.get('date', ''), item.get('category', ''), 
                         item.get('description', ''), item.get('amount', 0)] 
                        for item in data]
                title = "Expenses Report"
                default_name = f"expenses_{timestamp}.pdf"

            elif export_type == "Inventory Report":
                data = get_all_products()
                headers = ["ID", "Name", "Company", "Warehouse", "Store", "Total"]
                rows = [[item.get('id', ''), item.get('name', ''), item.get('company', ''),
                         item.get('warehouse_quantity', 0), item.get('store_quantity', 0),
                         item.get('quantity', 0)] 
                        for item in data]
                title = "Inventory Report"
                default_name = f"inventory_{timestamp}.pdf"

            else:
                QMessageBox.warning(self, "Error", "PDF export not available for this type!")
                return

            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save PDF File", default_name, "PDF Files (*.pdf);;All Files (*)"
            )

            if file_path:
                doc = SimpleDocTemplate(file_path, pagesize=A4)
                elements = []
                styles = getSampleStyleSheet()

                title_para = Paragraph(title, styles['Title'])
                elements.append(title_para)
                elements.append(Spacer(1, 0.2*inch))

                table_data = [headers] + rows
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                ]))

                elements.append(table)
                doc.build(elements)
                
                QMessageBox.information(self, "Success", f"PDF exported successfully!\n{file_path}")

        except ImportError:
            QMessageBox.warning(
                self, "Missing Library", 
                "PDF export requires 'reportlab' library.\n"
                "Please install it using: pip install reportlab"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export PDF:\n{str(e)}")
