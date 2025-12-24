# core/database.py
import sqlite3
import os
import logging
from contextlib import contextmanager
from typing import List, Dict, Optional

def get_app_data_dir():
    """Get application data directory (user-writable location).
    
    This ensures the database can be written even when app is installed in Program Files.
    Uses AppData/Local/ShopManagement on Windows, ~/.shopmanagement on Linux/Mac.
    """
    if os.name == 'nt':  # Windows
        app_data = os.path.join(os.path.expanduser("~"), "AppData", "Local", "ShopManagement")
    else:  # Linux/Mac
        app_data = os.path.join(os.path.expanduser("~"), ".shopmanagement")
    
    # Create directory if it doesn't exist
    try:
        os.makedirs(app_data, exist_ok=True)
    except Exception as e:
        # Fallback to current directory if AppData creation fails
        logging.warning(f"Could not create AppData directory: {e}. Using current directory.")
        app_data = os.path.dirname(os.path.abspath(__file__))
    
    return app_data

# Database file path in user-writable location
DB_DIR = get_app_data_dir()
DB_FILE = os.path.join(DB_DIR, "shop_data.db")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize all tables."""
    try:
        _create_products_table()
        _create_customers_table()
        _create_sales_table()
        _create_dues_received_table()
        _create_expenses_table()
        _add_due_amount_to_sales_table()
        _add_warehouse_store_columns()
        _create_indexes()  # Add indexes for better performance
        logger.info(" Database initialized successfully.")
    except Exception as e:
        logger.error(f" Failed to initialize database: {e}")
        raise

def _create_products_table():
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY, -- changed to TEXT and removed AUTPINCREMENT
                name TEXT NOT NULL COLLATE NOCASE,
                company TEXT NOT NULL COLLATE NOCASE,
                cost_price REAL NOT NULL CHECK(cost_price >= 0),
                quantity INTEGER NOT NULL CHECK(quantity >= 0),
                warehouse_quantity INTEGER NOT NULL DEFAULT 0 CHECK(warehouse_quantity >= 0),
                store_quantity INTEGER NOT NULL DEFAULT 0 CHECK(store_quantity >= 0),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def _create_customers_table():
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL COLLATE NOCASE,
                whatsapp_number TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                address TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def _create_sales_table():
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sale_type TEXT NOT NULL CHECK(sale_type IN ('retail', 'wholesale')),
                customer_name TEXT,  -- NULL for retail
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                selling_price REAL NOT NULL CHECK(selling_price >= 0),
                cost_price REAL NOT NULL CHECK(cost_price >= 0),
                quantity INTEGER NOT NULL CHECK(quantity >= 0),
                total REAL NOT NULL,
                profit REAL NOT NULL,
                paid_amount REAL NOT NULL CHECK(paid_amount >= 0),
                due_amount REAL NOT NULL
            )
        """)
        conn.commit()

@contextmanager
def get_db_connection():
    """Context manager for safe DB connections."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        # Enable WAL mode for better concurrency and performance
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")  # Faster writes
        conn.execute("PRAGMA cache_size=10000")  # Larger cache (10MB)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        yield conn
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()

# ===== PRODUCT FUNCTIONS =====
def add_product(product_id: str, name: str, company: str, cost_price: float, quantity: int, warehouse_quantity: int = None, store_quantity: int = None) -> int:
    """Add a new product to database."""
    try:
        if not product_id.strip():
            raise ValueError("Product id is required and cannot be empty")
        if cost_price < 0 or quantity < 0:
            raise ValueError("cost_price and quantity must be non-negative.")
        if not name.strip() or not company.strip():
            raise ValueError("Product name and company are required.")
        
        # If warehouse/store quantities not provided, default to warehouse
        if warehouse_quantity is None:
            warehouse_quantity = quantity
        if store_quantity is None:
            store_quantity = 0
        
        if warehouse_quantity < 0 or store_quantity < 0:
            raise ValueError("warehouse_quantity and store_quantity must be non-negative.")
        
        if warehouse_quantity + store_quantity != quantity:
            raise ValueError("warehouse_quantity + store_quantity must equal total quantity")
        
        with get_db_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO products (id, name, company, cost_price, quantity, warehouse_quantity, store_quantity)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (product_id.strip(), name.strip(), company.strip(), cost_price, quantity, warehouse_quantity, store_quantity))
            conn.commit()
            return cursor.lastrowid
    except sqlite3.Error as e:
        logger.error(f"Failed to add product: {e}")
        raise
    except ValueError as e:
        logger.error(f"Invalid product data: {e}")
        raise

def update_product(product_id: str, name: str, company: str, cost_price: float, quantity: int = None, warehouse_quantity: int = None, store_quantity: int = None):
    """Update an existing product."""
    try:
        if cost_price < 0:
            raise ValueError("cost_price must be non-negative.")
        if not name.strip() or not company.strip():
            raise ValueError("Product name and company are required.")
        
        with get_db_connection() as conn:
            # Get current product data
            current = get_product_by_id(product_id)
            if not current:
                raise ValueError(f"Product with ID {product_id} not found")
            
            # If quantities not provided, keep existing values
            if quantity is None:
                quantity = current.get('quantity', 0)
            if warehouse_quantity is None:
                warehouse_quantity = current.get('warehouse_quantity', 0)
            if store_quantity is None:
                store_quantity = current.get('store_quantity', 0)
            
            if quantity < 0 or warehouse_quantity < 0 or store_quantity < 0:
                raise ValueError("All quantities must be non-negative.")
            
            if warehouse_quantity + store_quantity != quantity:
                raise ValueError("warehouse_quantity + store_quantity must equal total quantity")
            
            conn.execute("""
                UPDATE products 
                SET name = ?, company = ?, cost_price = ?, quantity = ?, 
                    warehouse_quantity = ?, store_quantity = ?
                WHERE id = ?
            """, (name.strip(), company.strip(), cost_price, quantity, warehouse_quantity, store_quantity, product_id))
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Failed to update product: {e}")
        raise
    except ValueError as e:
        logger.error(f"Invalid product data: {e}")
        raise

def delete_product(product_id: str):
    """Delete a product from database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
            if cursor.rowcount == 0:
                raise ValueError(f"Product with ID {product_id} not found")
    except sqlite3.Error as e:
        logger.error(f"Failed to delete product: {e}")
        raise

def get_all_products(search_term: str = "") -> List[Dict]:
    """Get all products with computed balance."""
    try:
        with get_db_connection() as conn:
            if search_term:
                cursor = conn.execute("""
                    SELECT id, name, company, cost_price, quantity, warehouse_quantity, store_quantity, created_at,
                           (cost_price * quantity) AS balance
                    FROM products
                    WHERE name LIKE ? OR company LIKE ?
                    ORDER BY name
                """, (f"%{search_term}%", f"%{search_term}%"))
            else:
                cursor = conn.execute("""
                    SELECT id, name, company, cost_price, quantity, warehouse_quantity, store_quantity, created_at,
                           (cost_price * quantity) AS balance
                    FROM products ORDER BY name
                """)
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Failed to get products: {e}")
        raise

def get_product_by_id(product_id: str) -> Optional[Dict]:
    """Get a specific product by ID."""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except sqlite3.Error as e:
        logger.error(f"Failed to get product: {e}")
        raise

# ===== CUSTOMER FUNCTIONS =====
def add_customer(full_name: str, whatsapp: str, phone: str, address: str) -> int:
    """Add a new customer to database."""
    try:
        if not full_name.strip() or not whatsapp.strip() or not phone.strip() or not address.strip():
            raise ValueError("All customer fields are required.")
        
        with get_db_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO customers (full_name, whatsapp_number, phone_number, address)
                VALUES (?, ?, ?, ?)
            """, (full_name.strip(), whatsapp.strip(), phone.strip(), address.strip()))
            conn.commit()
            return cursor.lastrowid
    except sqlite3.Error as e:
        logger.error(f"Failed to add customer: {e}")
        raise
    except ValueError as e:
        logger.error(f"Invalid customer data: {e}")
        raise

def update_customer(customer_id: int, full_name: str, whatsapp: str, phone: str, address: str):
    """Update an existing customer."""
    try:
        if not full_name.strip() or not whatsapp.strip() or not phone.strip() or not address.strip():
            raise ValueError("All customer fields are required.")
        
        with get_db_connection() as conn:
            conn.execute("""
                UPDATE customers 
                SET full_name = ?, whatsapp_number = ?, phone_number = ?, address = ?
                WHERE id = ?
            """, (full_name.strip(), whatsapp.strip(), phone.strip(), address.strip(), customer_id))
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Failed to update customer: {e}")
        raise
    except ValueError as e:
        logger.error(f"Invalid customer data: {e}")
        raise

def delete_customer(customer_id: int):
    """Delete a customer from database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
            conn.commit()
            if cursor.rowcount == 0:
                raise ValueError(f"Customer with ID {customer_id} not found")
    except sqlite3.Error as e:
        logger.error(f"Failed to delete customer: {e}")
        raise

def get_all_customers(search_term: str = "") -> List[Dict]:
    """Get all customers, optionally filtered by search term."""
    try:
        with get_db_connection() as conn:
            if search_term:
                cursor = conn.execute("""
                    SELECT id, full_name, whatsapp_number, phone_number, address
                    FROM customers
                    WHERE full_name LIKE ? OR phone_number LIKE ?
                    ORDER BY full_name
                """, (f"%{search_term}%", f"%{search_term}%"))
            else:
                cursor = conn.execute("""
                    SELECT id, full_name, whatsapp_number, phone_number, address
                    FROM customers ORDER BY full_name
                """)
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Failed to get customers: {e}")
        raise

def get_customer_by_id(customer_id: int) -> Optional[Dict]:
    """Get a specific customer by ID."""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except sqlite3.Error as e:
        logger.error(f"Failed to get customer: {e}")
        raise

# ===== SALES FUNCTIONS =====


def add_sale(
    sale_type: str,
    product_id: int,
    product_name: str,
    selling_price: float,
    cost_price: float,
    quantity: int,
    paid_amount: float,
    customer_name: str = None
):
    total = selling_price * quantity
    profit = (selling_price - cost_price) * quantity
    due_amount = total - paid_amount

    if due_amount < 0:
        raise ValueError("Paid amount cannot exceed total amount")

    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO sales (
                sale_type, customer_name, product_id, product_name,
                selling_price, cost_price, quantity, total, profit,
                paid_amount, due_amount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sale_type, customer_name, product_id, product_name,
            selling_price, cost_price, quantity, total, profit,
            paid_amount, due_amount
        ))
        conn.commit()

        # Also update product quantity - deduct from store!
        prod = get_product_by_id(product_id)
        if not prod:
            raise ValueError(f"Product with ID {product_id} not found")
        
        current_store_qty = prod.get("store_quantity", 0)
        if current_store_qty < quantity:
            raise ValueError(f"Not enough stock in store for {product_name}. Available: {current_store_qty}, Required: {quantity}")
        
        new_store_quantity = current_store_qty - quantity
        new_total_quantity = prod["quantity"] - quantity

        update_product(
            product_id=product_id,
            name=prod["name"],
            company=prod["company"],
            cost_price=prod["cost_price"],  
            quantity=new_total_quantity,
            warehouse_quantity=prod.get("warehouse_quantity", 0),
            store_quantity=new_store_quantity
        )
def calculate_daily_profit():
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    COALESCE(SUM(total), 0) as total_sales,
                    COALESCE(SUM(profit), 0) as profit
                FROM sales 
                WHERE date(date) = date('now')
            """)
            row = cursor.fetchone()
            return {
                'total_sales': float(row['total_sales']),
                'profit': float(row['profit'])
            }
    except sqlite3.Error as e:
        logger.error(f"Failed to calculate daily profit: {e}")
        return {'total_sales': 0.0, 'profit': 0.0}

def calculate_monthly_profit():
    """Calculate current month's profit from the new 'sales' table."""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    COALESCE(SUM(total), 0) as total_sales,
                    COALESCE(SUM(profit), 0) as profit
                FROM sales 
                WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
            """)
            row = cursor.fetchone()
            return {
                'total_sales': float(row['total_sales']),
                'profit': float(row['profit'])
            }
    except sqlite3.Error as e:
        logger.error(f"Failed to calculate monthly profit: {e}")
        return {'total_sales': 0.0, 'profit': 0.0}
    
def get_sales_by_date_range(start_date: str, end_date: str, sale_type: str = None) -> List[Dict]:
    """Get sales within a date range, optionally filtered by type."""
    try:
        with get_db_connection() as conn:
            if sale_type:
                cursor = conn.execute("""
                    SELECT date, product_name, customer_name, quantity, 
                           total, profit, sale_type, due_amount
                    FROM sales
                    WHERE date BETWEEN ? AND ?
                    AND sale_type = ?
                    ORDER BY date DESC
                """, (start_date, end_date, sale_type))
            else:
                cursor = conn.execute("""
                    SELECT date, product_name, customer_name, quantity, 
                           total, profit, sale_type, due_amount
                    FROM sales
                    WHERE date BETWEEN ? AND ?
                    ORDER BY date DESC
                """, (start_date, end_date))
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Failed to get sales by date range: {e}")
        return []

def get_customer_dues() -> List[Dict]:
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    customer_name,
                    SUM(due_amount) as total_due,
                    MAX(date) as last_sale_date
                FROM sales 
                WHERE sale_type = 'wholesale' 
                AND due_amount > 0
                AND customer_name IS NOT NULL
                GROUP BY customer_name
                ORDER BY SUM(due_amount) DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Failed to get customer dues: {e}")
        return []
    
    # due part of customers .....

def _create_dues_received_table():
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dues_received (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                amount_received REAL NOT NULL CHECK(amount_received >= 0),
                received_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        """)
        conn.commit()

def get_customer_dues_with_payments() -> List[Dict]:
    """Get customers with dues, including received payments."""
    try:
        with get_db_connection() as conn:
            # Get total dues per customer
            dues_cursor = conn.execute("""
                SELECT 
                    customer_name,
                    SUM(due_amount) as total_due,
                    MAX(date) as last_sale_date
                FROM sales 
                WHERE sale_type = 'wholesale' 
                AND due_amount > 0
                AND customer_name IS NOT NULL
                GROUP BY customer_name
            """)
            dues_data = {row['customer_name']: dict(row) for row in dues_cursor.fetchall()}
            
            # Get total received per customer
            received_cursor = conn.execute("""
                SELECT 
                    customer_name,
                    SUM(amount_received) as total_received
                FROM dues_received
                GROUP BY customer_name
            """)
            received_data = {row['customer_name']: row['total_received'] for row in received_cursor.fetchall()}
            
            # Combine data
            result = []
            all_customers = set(list(dues_data.keys()) + list(received_data.keys()))
            
            for customer in all_customers:
                total_due = dues_data.get(customer, {}).get('total_due', 0)
                total_received = received_data.get(customer, 0)
                remaining_due = total_due - total_received
                
                # Only show customers with remaining dues
                if remaining_due > 0.01:  # Account for floating point errors
                    result.append({
                        'customer_name': customer,
                        'total_due': total_due,
                        'total_received': total_received,
                        'remaining_due': remaining_due,
                        'last_sale_date': dues_data.get(customer, {}).get('last_sale_date', None)
                    })
            
            return sorted(result, key=lambda x: x['remaining_due'], reverse=True)
    except sqlite3.Error as e:
        logger.error(f"Failed to get customer dues with payments: {e}")
        return []

def get_dues_payment_history() -> List[Dict]:
    """Get all received payments, newest first."""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("""
                SELECT customer_name, amount_received, received_date, notes
                FROM dues_received
                ORDER BY received_date DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Failed to get dues payment history: {e}")
        return []

def add_dues_payment(customer_name: str, amount: float, notes: str = ""):
    """Record a payment received from a customer."""
    try:
        if amount <= 0:
            raise ValueError("Payment amount must be positive")
        if not customer_name.strip():
            raise ValueError("Customer name is required")
            
        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO dues_received (customer_name, amount_received, notes)
                VALUES (?, ?, ?)
            """, (customer_name.strip(), amount, notes.strip()))
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Failed to add dues payment: {e}")
        raise
    except ValueError as e:
        logger.error(f"Invalid payment data: {e}")
        raise
def get_customer_dues_by_name(customer_name: str) -> float:
    """Get total outstanding due amount for a specific customer."""
    try:
        with get_db_connection() as conn:
            # Get total dues from sales
            sales_cursor = conn.execute("""
                SELECT COALESCE(SUM(due_amount), 0) as total_dues
                FROM sales 
                WHERE sale_type = 'wholesale' 
                AND customer_name = ?
                AND due_amount > 0
            """, (customer_name,))
            total_dues = sales_cursor.fetchone()["total_dues"]
            
            # Get total received payments
            received_cursor = conn.execute("""
                SELECT COALESCE(SUM(amount_received), 0) as total_received
                FROM dues_received 
                WHERE customer_name = ?
            """, (customer_name,))
            total_received = received_cursor.fetchone()["total_received"]
            
            return max(0, total_dues - total_received)  # Never negative
    except sqlite3.Error as e:
        logger.error(f"Failed to get customer dues by name: {e}")
        return 0.0
# ===== EXPENSE FUNCTIONS =====
def add_expense(category: str, description: str, amount: float, notes: str = "", expense_date: str = None) -> int:
    """Add a new expense."""
    try:
        if amount <= 0:
            raise ValueError("Expense amount must be positive")
        if not category.strip() or not description.strip():
            raise ValueError("Category and description are required")
        
        with get_db_connection() as conn:
            if expense_date:
                cursor = conn.execute("""
                    INSERT INTO expenses (date, category, description, amount, notes)
                    VALUES (?, ?, ?, ?, ?)
                """, (expense_date, category.strip(), description.strip(), amount, notes.strip()))
            else:
                cursor = conn.execute("""
                    INSERT INTO expenses (category, description, amount, notes)
                    VALUES (?, ?, ?, ?)
                """, (category.strip(), description.strip(), amount, notes.strip()))
            conn.commit()
            return cursor.lastrowid
    except sqlite3.Error as e:
        logger.error(f"Failed to add expense: {e}")
        raise
    except ValueError as e:
        logger.error(f"Invalid expense data: {e}")
        raise

def get_expenses_by_date_range(start_date: str, end_date: str, category: str = None) -> List[Dict]:
    """Get expenses within a date range, optionally filtered by category."""
    try:
        with get_db_connection() as conn:
            if category:
                cursor = conn.execute("""
                    SELECT id, date, category, description, amount, notes
                    FROM expenses
                    WHERE date BETWEEN ? AND ?
                    AND category = ?
                    ORDER BY date DESC
                """, (start_date, end_date, category))
            else:
                cursor = conn.execute("""
                    SELECT id, date, category, description, amount, notes
                    FROM expenses
                    WHERE date BETWEEN ? AND ?
                    ORDER BY date DESC
                """, (start_date, end_date))
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Failed to get expenses: {e}")
        return []

def calculate_total_expenses(start_date: str = None, end_date: str = None) -> float:
    """Calculate total expenses for a date range."""
    try:
        with get_db_connection() as conn:
            if start_date and end_date:
                cursor = conn.execute("""
                    SELECT COALESCE(SUM(amount), 0) as total
                    FROM expenses
                    WHERE date BETWEEN ? AND ?
                """, (start_date, end_date))
            elif start_date:
                cursor = conn.execute("""
                    SELECT COALESCE(SUM(amount), 0) as total
                    FROM expenses
                    WHERE date >= ?
                """, (start_date,))
            elif end_date:
                cursor = conn.execute("""
                    SELECT COALESCE(SUM(amount), 0) as total
                    FROM expenses
                    WHERE date <= ?
                """, (end_date,))
            else:
                cursor = conn.execute("""
                    SELECT COALESCE(SUM(amount), 0) as total
                    FROM expenses
                """)
            row = cursor.fetchone()
            return float(row['total'])
    except sqlite3.Error as e:
        logger.error(f"Failed to calculate total expenses: {e}")
        return 0.0

def get_expenses_by_category_summary(start_date: str = None, end_date: str = None) -> List[Dict]:
    """Get expenses grouped by category with totals."""
    try:
        with get_db_connection() as conn:
            if start_date and end_date:
                cursor = conn.execute("""
                    SELECT category, SUM(amount) as total, COUNT(*) as count
                    FROM expenses
                    WHERE date BETWEEN ? AND ?
                    GROUP BY category
                    ORDER BY total DESC
                """, (start_date, end_date))
            else:
                cursor = conn.execute("""
                    SELECT category, SUM(amount) as total, COUNT(*) as count
                    FROM expenses
                    GROUP BY category
                    ORDER BY total DESC
                """)
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Failed to get expenses by category: {e}")
        return []

def delete_expense(expense_id: int):
    """Delete an expense."""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            conn.commit()
            if cursor.rowcount == 0:
                raise ValueError(f"Expense with ID {expense_id} not found")
    except sqlite3.Error as e:
        logger.error(f"Failed to delete expense: {e}")
        raise

# ===== INVENTORY TRANSFER FUNCTIONS =====
def transfer_inventory(product_id: str, from_location: str, to_location: str, quantity: int, notes: str = ""):
    """Transfer inventory between warehouse and store."""
    try:
        if quantity <= 0:
            raise ValueError("Transfer quantity must be positive")
        if from_location not in ['warehouse', 'store'] or to_location not in ['warehouse', 'store']:
            raise ValueError("Locations must be 'warehouse' or 'store'")
        if from_location == to_location:
            raise ValueError("Source and destination locations must be different")
        
        prod = get_product_by_id(product_id)
        if not prod:
            raise ValueError(f"Product with ID {product_id} not found")
        
        # Check available quantity
        if from_location == 'warehouse':
            available = prod.get('warehouse_quantity', 0)
            if available < quantity:
                raise ValueError(f"Not enough stock in warehouse. Available: {available}, Required: {quantity}")
        else:
            available = prod.get('store_quantity', 0)
            if available < quantity:
                raise ValueError(f"Not enough stock in store. Available: {available}, Required: {quantity}")
        
        # Update quantities
        if from_location == 'warehouse':
            new_warehouse_qty = prod.get('warehouse_quantity', 0) - quantity
            new_store_qty = prod.get('store_quantity', 0) + quantity
        else:
            new_warehouse_qty = prod.get('warehouse_quantity', 0) + quantity
            new_store_qty = prod.get('store_quantity', 0) - quantity
        
        # Total quantity remains the same
        total_quantity = prod.get('quantity', 0)
        
        update_product(
            product_id=product_id,
            name=prod['name'],
            company=prod['company'],
            cost_price=prod['cost_price'],
            quantity=total_quantity,
            warehouse_quantity=new_warehouse_qty,
            store_quantity=new_store_qty
        )
        
        logger.info(f"Transferred {quantity} units of {prod['name']} from {from_location} to {to_location}")
        
    except sqlite3.Error as e:
        logger.error(f"Failed to transfer inventory: {e}")
        raise
    except ValueError as e:
        logger.error(f"Invalid transfer data: {e}")
        raise

def get_low_stock_products(threshold: int = 10, location: str = 'store') -> List[Dict]:
    """Get products with low stock."""
    try:
        with get_db_connection() as conn:
            if location == 'store':
                cursor = conn.execute("""
                    SELECT id, name, company, cost_price, quantity, warehouse_quantity, store_quantity
                    FROM products
                    WHERE store_quantity <= ?
                    ORDER BY store_quantity ASC
                """, (threshold,))
            else:
                cursor = conn.execute("""
                    SELECT id, name, company, cost_price, quantity, warehouse_quantity, store_quantity
                    FROM products
                    WHERE warehouse_quantity <= ?
                    ORDER BY warehouse_quantity ASC
                """, (threshold,))
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Failed to get low stock products: {e}")
        return []

def _add_due_amount_to_sales_table():
    """Add due_amount column to existing sales table."""
    with get_db_connection() as conn:
        # Check if column already exists
        cursor = conn.execute("PRAGMA table_info(sales)")
        columns = [row['name'] for row in cursor.fetchall()]
        
        if 'due_amount' not in columns:
            conn.execute("ALTER TABLE sales ADD COLUMN due_amount REAL NOT NULL DEFAULT 0")
            conn.commit()
            logger.info("Added due_amount column to sales table")

def _create_expenses_table():
    """Create expenses table."""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount >= 0),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def _add_warehouse_store_columns():
    """Add warehouse_quantity and store_quantity columns to products table if they don't exist."""
    with get_db_connection() as conn:
        cursor = conn.execute("PRAGMA table_info(products)")
        columns = [row['name'] for row in cursor.fetchall()]
        
        if 'warehouse_quantity' not in columns:
            conn.execute("ALTER TABLE products ADD COLUMN warehouse_quantity INTEGER NOT NULL DEFAULT 0")
            logger.info("Added warehouse_quantity column to products table")
        
        if 'store_quantity' not in columns:
            conn.execute("ALTER TABLE products ADD COLUMN store_quantity INTEGER NOT NULL DEFAULT 0")
            logger.info("Added store_quantity column to products table")
        
        # Migrate existing data: split 50/50 between warehouse and store
        if 'warehouse_quantity' in columns or 'store_quantity' in columns:
            # Check if migration is needed
            cursor = conn.execute("SELECT COUNT(*) as count FROM products WHERE warehouse_quantity = 0 AND store_quantity = 0 AND quantity > 0")
            result = cursor.fetchone()
            if result and result['count'] > 0:
                # Split 50/50: half to warehouse, half to store
                conn.execute("""
                    UPDATE products 
                    SET warehouse_quantity = quantity / 2,
                        store_quantity = quantity / 2 + (quantity % 2)
                    WHERE warehouse_quantity = 0 AND store_quantity = 0 AND quantity > 0
                """)
                logger.info("Migrated existing product quantities: 50% to warehouse, 50% to store")
        
        conn.commit()

def _create_indexes():
    """Create indexes for better query performance."""
    with get_db_connection() as conn:
        # Indexes for products table
        conn.execute("CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_products_company ON products(company)")
        
        # Indexes for sales table
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sales_product_id ON sales(product_id)")
        
        # Indexes for customers table
        conn.execute("CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(full_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone_number)")
        
        # Indexes for dues_received table
        conn.execute("CREATE INDEX IF NOT EXISTS idx_dues_customer ON dues_received(customer_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_dues_date ON dues_received(received_date)")
        
        # Indexes for expenses table
        conn.execute("CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category)")
        
        conn.commit()