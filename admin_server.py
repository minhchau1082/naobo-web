# -*- coding: utf-8 -*-
from http.server import HTTPServer, BaseHTTPRequestHandler
import sqlite3
import json
import os
import sys
import mimetypes
from urllib.parse import urlparse, parse_qs
from datetime import datetime

# Configuration
DB_PATH = "brain.db"
PORT = int(os.environ.get("PORT", 8080))  # Tự động nhận PORT từ Render/Hosting
ADMIN_HTML_PATH = "admin/index.html"
CHECKOUT_HTML_PATH = "checkout.html"
# MẬT MÃ BẢO MẬT WEBHOOK (Bạn cần điền mã này vào SePay)
SEPAY_WEBHOOK_TOKEN = "naobokhoemanh_secret_2024"

class AdminHandler(BaseHTTPRequestHandler):
    def _send_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # Serve Landing Page
        if path == '/' or path == '/index.html':
            try:
                with open('index.html', 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404, "index.html not found")
            return

        # Serve Admin Page
        if path == '/admin' or path == '/admin/':
            try:
                with open(ADMIN_HTML_PATH, 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404, "Admin HTML not found")
            return

        # Serve Checkout Page
        if path == '/thanh-toan' or path == '/thanh-toan/':
            try:
                with open(CHECKOUT_HTML_PATH, 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404, "Checkout HTML not found")
            return

        # Serve Static Files (CSS, JS, Images)
        static_path = path.lstrip('/')
        if os.path.isfile(static_path):
            mime_type, _ = mimetypes.guess_type(static_path)
            with open(static_path, 'rb') as f:
                self.send_response(200)
                self.send_header('Content-type', mime_type or 'application/octet-stream')
                self.end_headers()
                self.wfile.write(f.read())
            return

        # API Handlers
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if path == '/api/products' or path == '/api/public/products':
                cursor.execute("SELECT id, name, price, quantity, description FROM products WHERE quantity > 0 ORDER BY id DESC")
                data = [dict(row) for row in cursor.fetchall()]
                self._send_response(data)
            
            elif path == '/api/customers':
                cursor.execute("SELECT * FROM customers ORDER BY id DESC")
                data = [dict(row) for row in cursor.fetchall()]
                self._send_response(data)
            
            elif path == '/api/orders':
                cursor.execute("""
                    SELECT o.*, c.name as customer_name, p.name as product_name 
                    FROM orders o
                    LEFT JOIN customers c ON o.customer_id = c.id
                    LEFT JOIN products p ON o.product_id = p.id
                    ORDER BY o.id DESC
                """)
                data = [dict(row) for row in cursor.fetchall()]
                self._send_response(data)
            
            elif path == '/api/public/order-status':
                query = parse_qs(parsed_path.query)
                order_id = query.get('id', [None])[0]
                if not order_id:
                    self._send_response({"error": "Missing ID"}, 400)
                    return
                cursor.execute("SELECT status FROM orders WHERE id=?", (order_id,))
                row = cursor.fetchone()
                if row:
                    self._send_response({"status": row['status']})
                else:
                    self._send_response({"error": "Order not found"}, 404)
            elif path == '/api/sync-gsheet':
                import sync_gsheet
                result = sync_gsheet.sync()
                self._send_response(result)
            else:
                self.send_error(404)
        except Exception as e:
            print(f"Error handling GET {path}: {str(e)}")
            self._send_response({"error": str(e)}, 500)
        finally:
            if 'conn' in locals(): conn.close()

    def do_POST(self):
        try:
            # 1. Đọc dữ liệu từ Body một cách an toàn
            content_length_str = self.headers.get('Content-Length')
            if not content_length_str:
                self._send_response({"error": "Missing Content-Length"}, 400)
                return
            
            content_length = int(content_length_str)
            post_data = self.rfile.read(content_length)
            
            try:
                payload = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError as je:
                print(f"JSON Decode Error: {str(je)}")
                self._send_response({"error": "Invalid JSON format"}, 400)
                return

            parsed_path = urlparse(self.path)
            path = parsed_path.path
            print(f"[{datetime.now()}] Handling POST {path}")

            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 2. Xử lý các endpoint cụ thể
            if path == '/api/products':
                item_id = payload.get('id')
                if item_id:
                    # Update
                    cursor.execute("""
                        UPDATE products SET name=?, price=?, quantity=?, description=? 
                        WHERE id=?
                    """, (payload['name'], payload['price'], payload['quantity'], payload.get('description', ''), item_id))
                else:
                    # Insert
                    cursor.execute("""
                        INSERT INTO products (name, price, quantity, description) 
                        VALUES (?, ?, ?, ?)
                    """, (payload['name'], payload['price'], payload['quantity'], payload.get('description', '')))
                conn.commit()
                self._send_response({"success": True})

            elif path == '/api/customers':
                item_id = payload.get('id')
                if item_id:
                    cursor.execute("""
                        UPDATE customers SET name=?, phone=?, zalo=?, email=?, notes=? 
                        WHERE id=?
                    """, (payload['name'], payload['phone'], payload.get('zalo', ''), payload.get('email', ''), payload.get('notes', ''), item_id))
                else:
                    cursor.execute("""
                        INSERT INTO customers (name, phone, zalo, email, notes) 
                        VALUES (?, ?, ?, ?, ?)
                    """, (payload['name'], payload['phone'], payload.get('zalo', ''), payload.get('email', ''), payload.get('notes', '')))
                conn.commit()
                self._send_response({"success": True})

            elif path.startswith('/api/orders'):
                item_id = payload.get('id')
                if item_id:
                    # Cập nhật trạng thái/ghi chú đơn hàng
                    cursor.execute("""
                        UPDATE orders SET status=?, notes=? 
                        WHERE id=?
                    """, (payload.get('status', 'pending'), payload.get('notes', ''), item_id))
                    conn.commit()
                    self._send_response({"success": True})
                else:
                    # Tạo đơn hàng mới
                    customer_id = payload.get('customer_id')
                    if not customer_id:
                        # Tìm hoặc tạo khách hàng dựa trên SĐT
                        phone = payload.get('phone')
                        cursor.execute("SELECT id FROM customers WHERE phone=?", (phone,))
                        existing = cursor.fetchone()
                        if existing:
                            customer_id = existing['id']
                        else:
                            cursor.execute("INSERT INTO customers (name, phone, email) VALUES (?, ?, ?)", 
                                         (payload.get('name', 'Khách hàng mới'), phone, payload.get('email', '')))
                            customer_id = cursor.lastrowid

                    product_id = payload.get('product_id')
                    cursor.execute("SELECT price FROM products WHERE id=?", (product_id,))
                    prod = cursor.fetchone()
                    if prod:
                        amount = payload.get('amount') or prod['price']
                        cursor.execute("""
                            INSERT INTO orders (customer_id, product_id, amount, status, notes) 
                            VALUES (?, ?, ?, ?, ?)
                        """, (customer_id, product_id, amount, 'pending', payload.get('notes', '')))
                        conn.commit()
                        self._send_response({"success": True, "order_id": cursor.lastrowid})
                    else:
                        self._send_response({"error": "Sản phẩm không tồn tại"}, 404)

            elif path == '/api/public/checkout':
                # Logic checkout từ landing page
                name = payload.get('name')
                phone = payload.get('phone')
                email = payload.get('email')
                product_id = payload.get('product_id')

                # 1. Tìm/Tạo khách hàng
                cursor.execute("SELECT id FROM customers WHERE phone=?", (phone,))
                cust = cursor.fetchone()
                if cust:
                    customer_id = cust['id']
                else:
                    cursor.execute("INSERT INTO customers (name, phone, email) VALUES (?, ?, ?)", (name, phone, email))
                    customer_id = cursor.lastrowid
                
                # 2. Lấy giá sản phẩm
                cursor.execute("SELECT price FROM products WHERE id=?", (product_id,))
                prod = cursor.fetchone()
                if not prod:
                    self._send_response({"success": False, "error": "Sản phẩm không tồn tại"}, 404)
                    return
                
                amount = float(prod['price'])
                
                # 3. Tạo đơn hàng
                cursor.execute("INSERT INTO orders (customer_id, product_id, amount, status, notes) VALUES (?, ?, ?, ?, ?)",
                             (customer_id, product_id, amount, 'pending', payload.get('notes', '')))
                order_id = cursor.lastrowid
                conn.commit()
                
                self._send_response({"success": True, "order_id": order_id, "amount": amount})

            elif path == '/api/delete':
                table = payload['table']
                item_id = payload['id']
                if table in ['products', 'customers', 'orders']:
                    cursor.execute(f"DELETE FROM {table} WHERE id=?", (item_id,))
                    conn.commit()
                    self._send_response({"success": True})
            
            elif path == '/api/sepay-webhook':
                auth_header = self.headers.get('Authorization', '')
                token = auth_header.replace('Bearer ', '').replace('Apikey ', '')
                if SEPAY_WEBHOOK_TOKEN and token != SEPAY_WEBHOOK_TOKEN:
                    self._send_response({"success": False, "message": "Unauthorized"}, 401)
                    return

                content = payload.get('content', '') or payload.get('transactionContent', '')
                import re
                match = re.search(r'NBKM\s*(\d+)', content.upper())
                if match:
                    order_id = match.group(1)
                    cursor.execute("UPDATE orders SET status=? WHERE id=?", ('success', order_id))
                    conn.commit()
                    self._send_response({"success": True, "message": f"Order {order_id} updated"})
                else:
                    self._send_response({"success": False, "message": "No order ID found"})

            else:
                self.send_error(404)

        except Exception as e:
            print(f"!!! Error in do_POST {self.path}: {str(e)}")
            import traceback
            traceback.print_exc()
            self._send_response({"error": str(e)}, 500)
        finally:
            if 'conn' in locals() and conn:
                conn.close()

def run_server():
    # Force UTF-8 for console output on Windows
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, AdminHandler)
    print(f"Admin Server running on http://localhost:{PORT}")
    print(f"Access your admin panel at: http://localhost:{PORT}/admin")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
