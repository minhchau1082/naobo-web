# -*- coding: utf-8 -*-
"""Script khởi tạo các bảng cần thiết trong brain.db nếu chưa có."""
import sqlite3
import os

DB_PATH = "brain.db"

def setup():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL DEFAULT 0,
            quantity INTEGER NOT NULL DEFAULT 0,
            description TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            zalo TEXT DEFAULT '',
            email TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            product_id INTEGER,
            amount REAL NOT NULL DEFAULT 0,
            qty INTEGER DEFAULT 1,
            status TEXT DEFAULT 'pending',
            notes TEXT DEFAULT '',
            purchased_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(customer_id) REFERENCES customers(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """)

    conn.commit()

    # Kiểm tra kết quả
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    print(f"OK - Cac bang hien co: {tables}")

    # Kiểm tra dữ liệu mẫu
    cursor.execute("SELECT COUNT(*) FROM products")
    print(f"   San pham: {cursor.fetchone()[0]} ban ghi")
    cursor.execute("SELECT COUNT(*) FROM customers")
    print(f"   Khach hang: {cursor.fetchone()[0]} ban ghi")
    cursor.execute("SELECT COUNT(*) FROM orders")
    print(f"   Don hang: {cursor.fetchone()[0]} ban ghi")

    conn.close()

if __name__ == "__main__":
    setup()
