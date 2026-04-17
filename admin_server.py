# -*- coding: utf-8 -*-
from http.server import HTTPServer, BaseHTTPRequestHandler
import sqlite3
import json
import os
import sys
import mimetypes
from urllib.parse import urlparse, parse_qs

# Configuration
DB_PATH = "brain.db"
PORT = int(os.environ.get("PORT", 8080))  # Tự động nhận PORT từ Render/Hosting
ADMIN_HTML_PATH = "admin.html"
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
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
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
            else:
                self.send_error(404)
        except Exception as e:
            self._send_response({"error": str(e)}, 500)
        finally:
            conn.close()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        payload = json.loads(post_data.decode('utf-8'))
        
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            if path == '/api/products':
                if payload.get('id'): # Edit
                    cursor.execute("UPDATE products SET name=?, price=?, quantity=?, description=? WHERE id=?",
                                 (payload['name'], payload['price'], payload['quantity'], payload.get('description', ''), payload['id']))
                else: # Add
                    cursor.execute("INSERT INTO products (name, price, quantity, description) VALUES (?, ?, ?, ?)",
                                 (payload['name'], payload['price'], payload['quantity'], payload.get('description', '')))
                conn.commit()
                self._send_response({"success": True})

            elif path == '/api/customers':
                if payload.get('id'): # Edit
                    cursor.execute("UPDATE customers SET name=?, phone=?, zalo=?, email=?, notes=? WHERE id=?",
                                 (payload['name'], payload['phone'], payload.get('zalo', ''), payload.get('email', ''), payload.get('notes', ''), payload['id']))
                else: # Add
                    cursor.execute("INSERT INTO customers (name, phone, zalo, email, notes) VALUES (?, ?, ?, ?, ?)",
                                 (payload['name'], payload['phone'], payload.get('zalo', ''), payload.get('email', ''), payload.get('notes', '')))
                conn.commit()
                self._send_response({"success": True})

            elif path == '/api/orders' or path == '/api/public/checkout':
                if payload.get('id'): # Edit Status/Notes
                    cursor.execute("UPDATE orders SET status=?, notes=? WHERE id=?",
                                 (payload.get('status', 'pending'), payload.get('notes', ''), payload['id']))
                    conn.commit()
                    self._send_response({"success": True})
                else: # Add New Order / Public Checkout
                    # 1. Handle Customer (Find or Create)
                    customer_id = payload.get('customer_id')
                    if not customer_id:
                        cursor.execute("SELECT id FROM customers WHERE phone=?", (payload['phone'],))
                        existing = cursor.fetchone()
                        if existing:
                            customer_id = existing[0]
                        else:
                            cursor.execute("INSERT INTO customers (name, phone, email) VALUES (?, ?, ?)",
                                         (payload['name'], payload['phone'], payload.get('email', '')))
                            customer_id = cursor.lastrowid

                    product_id = payload['product_id']
                    
                    # 2. Get Product Price
                    cursor.execute("SELECT price, quantity FROM products WHERE id=?", (product_id,))
                    prod = cursor.fetchone()
                    if not prod:
                        self._send_response({"error": "Sản phẩm không tồn tại"}, 404)
                        return
                    
                    # 3. Create Order
                    amount = payload.get('amount') or prod[0]
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
                # KIỂM TRA BẢO MẬT: Chỉ cho phép SePay gửi dữ liệu
                auth_header = self.headers.get('Authorization', '')
                # Xóa tiền tố Bearer hoặc Apikey nếu có để lấy đúng token gốc
                token = auth_header.replace('Bearer ', '').replace('Apikey ', '')
                
                if SEPAY_WEBHOOK_TOKEN and token != SEPAY_WEBHOOK_TOKEN:
                    self._send_response({"success": False, "message": "Unauthorized - Invalid Webhook Token"}, 401)
                    return

                # SePay webhook gửi data dạng JSON
                content = payload.get('content', '') or payload.get('transactionContent', '') or payload.get('description', '')
                
                import re
                match = re.search(r'NBKM\s*(\d+)', content.upper())
                
                if match:
                    order_id = match.group(1)
                    cursor.execute("UPDATE orders SET status=? WHERE id=?", ('success', order_id))
                    conn.commit()
                    self._send_response({"success": True, "message": f"Updated order {order_id} to success"})
                else:
                    self._send_response({"success": False, "message": "No matching order ID found"})

            else:
                self.send_error(404)
        except Exception as e:
            conn.rollback()
            self._send_response({"error": str(e)}, 500)
        finally:
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
