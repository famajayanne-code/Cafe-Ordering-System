import os
import sqlite3
from flask import g

DATABASE = os.path.join(os.path.dirname(__file__), "cafe.db")

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL COLLATE NOCASE UNIQUE,
        category TEXT NOT NULL,
        price REAL NOT NULL CHECK(price >= 0),
        available INTEGER NOT NULL DEFAULT 1 CHECK(available IN (0,1))
    );
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        total REAL NOT NULL CHECK(total >= 0),
        payment_method TEXT NOT NULL CHECK(payment_method IN ('Cash','GCash')),
        payment_status TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending','Completed','Cancelled')),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        menu_item_id INTEGER,
        item_name TEXT NOT NULL,
        unit_price REAL NOT NULL CHECK(unit_price >= 0),
        quantity INTEGER NOT NULL CHECK(quantity > 0),
        line_total REAL NOT NULL CHECK(line_total >= 0),
        FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
        FOREIGN KEY(menu_item_id) REFERENCES menu_items(id) ON DELETE SET NULL
    );
    """)
    db.commit()
    db.close()

def seed_menu():
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    examples = [
        ("Espresso", "Coffee", 70.00),
        ("Americano", "Coffee", 85.00),
        ("Cafe Latte", "Coffee", 110.00),
        ("Cappuccino", "Coffee", 110.00),
        ("Spanish Latte", "Coffee", 120.00),
        ("Caramel Macchiato", "Coffee", 130.00),
        ("Mocha Latte", "Coffee", 120.00),
        ("Vanilla Latte", "Coffee", 120.00),
        ("Hazelnut Latte", "Coffee", 125.00),
        ("White Chocolate Mocha", "Coffee", 130.00),
        ("Matcha Latte", "Non-Coffee", 130.00),
        ("Strawberry Milk", "Non-Coffee", 100.00),
        ("Chocolate Milk", "Non-Coffee", 95.00),
        ("Iced Matcha", "Non-Coffee", 110.00),
        ("Hot Chocolate", "Non-Coffee", 90.00),
        ("Taro Milk", "Non-Coffee", 100.00),
        ("Blueberry Soda", "Non-Coffee", 95.00),
        ("Strawberry Soda", "Non-Coffee", 95.00),
        ("Mango Smoothie", "Non-Coffee", 110.00),
        ("Cookies and Cream Frappe", "Non-Coffee", 130.00),
        ("Chocolate Chip Cookies", "Pastry", 45.00),
        ("Red Velvet Cookies", "Pastry", 50.00),
        ("Butter Croissant", "Pastry", 65.00),
        ("Blueberry Muffin", "Pastry", 55.00),
        ("Cinnamon Roll", "Pastry", 60.00),
        ("Chocolate Brownies", "Pastry", 50.00),
        ("Classic Cheesecake", "Pastry", 95.00),
        ("Strawberry Shortcake", "Pastry", 100.00),
        ("Banana Bread", "Pastry", 45.00),
        ("Almond Biscotti", "Pastry", 40.00),
        ("Cheese Danish", "Pastry", 65.00),
        ("Mini Chocolate Donuts", "Pastry", 45.00),
        ("Red Velvet Cupcake", "Pastry", 55.00),
        ("Garlic Cream Cheese Bread", "Pastry", 60.00),
        (" Ham and Cheese Sandwich", "Pastry", 85.00),
    ]
    for row in examples:
        db.execute("INSERT OR IGNORE INTO menu_items(name,category,price) VALUES(?,?,?)", row)
    db.commit()
    db.close()
