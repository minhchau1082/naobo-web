# -*- coding: utf-8 -*-
from http.server import HTTPServer, BaseHTTPRequestHandler
import sqlite3
import json
import os
import sys
import mimetypes
import resend
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import threading
import time
import re

# Configuration
DB_PATH = "brain.db"
PORT = int(os.environ.get("PORT", 8080))  # Tự động nhận PORT từ Render/Hosting
ADMIN_HTML_PATH = "admin/index.html"
CHECKOUT_HTML_PATH = "checkout.html"
# MẬT MÃ BẢO MẬT WEBHOOK (Bạn cần điền mã này vào SePay)
SEPAY_WEBHOOK_TOKEN = "naobokhoemanh_secret_2024"

# Cấu hình Resend
RESEND_KEY_FILE = "resend_config.txt"
if os.path.exists(RESEND_KEY_FILE):
    with open(RESEND_KEY_FILE, "r") as f:
        resend.api_key = f.read().strip()
else:
    # Nếu không tìm thấy file, có thể thử lấy từ biến môi trường (cho Render.com)
    resend.api_key = os.environ.get("RESEND_API_KEY")

def send_automated_email(to_email, subject, html_content):
    """Hàm gửi email tự động qua Resend"""
    try:
        if not resend.api_key:
            print("!!! Lỗi: Chưa cấu hình Resend API Key")
            return False
            
        params = {
            "from": "Võ Thu Thủy <thuy@naobokhoemanh.io.vn>", # Đã cập nhật tên miền chuyên nghiệp
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }
        
        email = resend.Emails.send(params)
        print(f"--- Đã gửi email tới {to_email}. ID: {email['id']}")
        return True
    except Exception as e:
        print(f"!!! Lỗi khi gửi email: {str(e)}")
        return False

def parse_email_sequence():
    """Phân tích file email_sequence.md để lấy tiêu đề và nội dung"""
    # Ưu tiên lấy file từ desktop nếu có (để sync với thay đổi của user)
    desktop_path = "c:\\Users\\ADMIN\\Desktop\\my-brain\\email_sequence.md"
    local_path = "email_sequence.md"
    
    path = desktop_path if os.path.exists(desktop_path) else local_path
    
    if not os.path.exists(path):
        print(f"!!! Cảnh báo: Không tìm thấy file {path}")
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        emails = {}
        # Tách các section bằng "## Email X:"
        sections = re.split(r'## Email \d+:', content)
        
        # Email 1 (section 1 vì split tạo ra phần trống ở index 0 nếu file bắt đầu bằng split pattern)
        # Nhưng ở đây file bắt đầu bằng "# Email Sequence", nên section 0 là header
        if len(sections) > 1:
            emails[1] = extract_email_data(sections[1])
        if len(sections) > 2:
            emails[2] = extract_email_data(sections[2])
        if len(sections) > 3:
            emails[3] = extract_email_data(sections[3])
            
        return emails
    except Exception as e:
        print(f"!!! Lỗi khi parse email sequence: {str(e)}")
        return {}

def extract_email_data(section):
    """Trích xuất tiêu đề và nội dung từ một section email"""
    # Tìm tiêu đề trong dấu **Tiêu đề:**
    subject_match = re.search(r'\*\*Tiêu đề:\*\*\s*(.*)', section)
    subject = subject_match.group(1).strip() if subject_match else "Cảm ơn bạn đã quan tâm"
    
    # Lấy nội dung body (bỏ phần tiêu đề và các dấu gạch ngang phân cách)
    body = re.sub(r'\*\*Tiêu đề:\*\*\s*.*', '', section).strip()
    body = body.split('---')[0].strip() # Bỏ phần gạch ngang nếu có
    
    # Chuyển đổi xuống dòng thành <br> để hiển thị tốt trong email HTML
    html_body = body.replace('\n', '<br>')
    # Thêm style cơ bản cho email
    html_content = f"""
    <div style="font-family: 'Be Vietnam Pro', sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
        {html_body}
    </div>
    """
    return {"subject": subject, "body": html_content}

def send_order_confirmation(to_email, customer_name, product_name, amount):
    """Gửi email xác nhận đơn hàng khi có đơn mới"""
    subject = f"Xác nhận đơn hàng: {product_name} - Cảm ơn bạn đã tin tưởng"
    
    html_body = f"""
    Chào {customer_name},<br><br>
    Mình là Thủy đây. Mình vừa nhận được đơn đăng ký của bạn cho sản phẩm "<strong>{product_name}</strong>" với số tiền là <strong>{amount:,}đ</strong>.<br><br>
    Thật sự trân trọng sự tin tưởng bạn dành cho mình và cho chính bản thân bạn trên hành trình tìm lại sự bình yên này.<br><br>
    <strong>Hướng dẫn nhận sản phẩm:</strong><br>
    Vì đây là sản phẩm số, tài liệu hoặc quyền truy cập sẽ được gửi trực tiếp đến bạn trong một email riêng ngay sau đây. Đừng quên kiểm tra hộp thư (cả thư rác) nhé.<br><br>
    Nếu bạn có bất kỳ khó khăn nào trong quá trình nhận tài liệu, đừng ngần ngại trả lời email này, mình luôn ở đây để hỗ trợ.<br>
    Có link cố định để tải file là dưới đây: <a href="https://drive.google.com/file/d/1yrYQBJE-sOHqvOHMGZ3cI-5sa99WydDR/view?usp=sharing">https://drive.google.com/file/d/1yrYQBJE-sOHqvOHMGZ3cI-5sa99WydDR/view?usp=sharing</a><br><br>
    Thân mến,<br><br>
    Võ Thu Thủy<br>
    55 tuổi - Giảng viên & Người bạn đồng hành
    """
    
    html_content = f"""
    <div style="font-family: 'Be Vietnam Pro', sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
        {html_body}
    </div>
    """
    
    # Sử dụng luồng chạy ngầm để không block request tạo đơn
    threading.Thread(target=send_automated_email, args=(to_email, subject, html_content), daemon=True).start()

def email_worker():
    """Luồng chạy ngầm để kiểm tra và gửi email trong hàng đợi"""
    print("--- Email Worker started ---")
    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            # Tìm các email chưa gửi và đã đến hạn
            cursor.execute("SELECT * FROM email_queue WHERE sent_time IS NULL AND scheduled_time <= ?", (now,))
            pending = cursor.fetchall()
            
            if pending:
                print(f"--- Tìm thấy {len(pending)} email cần gửi...")
                emails_content = parse_email_sequence()
                for job in pending:
                    step = job['step']
                    email_addr = job['email']
                    
                    if step in emails_content:
                        data = emails_content[step]
                        print(f"--- Đang gửi Email {step} tới {email_addr}...")
                        success = send_automated_email(email_addr, data['subject'], data['body'])
                        if success:
                            cursor.execute("UPDATE email_queue SET sent_time = ? WHERE id = ?", (datetime.now().isoformat(), job['id']))
                            conn.commit()
                            print(f"--- Đã gửi thành công Email {step} tới {email_addr}")
                    else:
                        print(f"!!! Lỗi: Không tìm thấy nội dung cho Email {step}")
            
            conn.close()
        except Exception as e:
            print(f"!!! Lỗi trong email_worker: {str(e)}")
        
        time.sleep(60) # Kiểm tra mỗi phút

# Khởi động background worker
threading.Thread(target=email_worker, daemon=True).start()

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
                    cursor.execute("SELECT name, price FROM products WHERE id=?", (product_id,))
                    prod = cursor.fetchone()
                    if prod:
                        amount = payload.get('amount') or prod['price']
                        cursor.execute("""
                            INSERT INTO orders (customer_id, product_id, amount, status, notes) 
                            VALUES (?, ?, ?, ?, ?)
                        """, (customer_id, product_id, amount, 'pending', payload.get('notes', '')))
                        conn.commit()
                        
                        # Gửi email xác nhận
                        cursor.execute("SELECT name, email FROM customers WHERE id=?", (customer_id,))
                        cust_info = cursor.fetchone()
                        if cust_info and cust_info['email']:
                            send_order_confirmation(cust_info['email'], cust_info['name'], prod['name'], amount)
                            
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
                cursor.execute("SELECT name, price FROM products WHERE id=?", (product_id,))
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
                
                # Gửi email xác nhận
                if email:
                    send_order_confirmation(email, name, prod['name'], amount)
                
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

            elif path == '/api/public/assessment':
                email = payload.get('email')
                name = payload.get('name')
                phone = payload.get('phone', '')
                
                print(f"--- Nhận đăng ký waitlist: {email} ({name})")
                
                # 1. Tìm/Tạo khách hàng
                cursor.execute("SELECT id FROM customers WHERE email=?", (email,))
                cust = cursor.fetchone()
                if not cust:
                    cursor.execute("INSERT INTO customers (name, email, phone, notes) VALUES (?, ?, ?, ?)", 
                                 (name, email, phone, "Waitlist Assessment"))
                
                # 2. Kích hoạt chuỗi email
                emails_content = parse_email_sequence()
                
                if not emails_content:
                    print("!!! Lỗi: Không thể tải nội dung email sequence")
                    self._send_response({"success": False, "error": "Email content not available"}, 500)
                    return

                if 'test' in email.lower():
                    # CHẾ ĐỘ TEST: Gửi cả 3 ngay lập tức
                    print(f"--- CHẾ ĐỘ TEST: Gửi đồng loạt 3 email tới {email}")
                    for step in [1, 2, 3]:
                        if step in emails_content:
                            data = emails_content[step]
                            send_automated_email(email, data['subject'], data['body'])
                            cursor.execute("INSERT INTO email_queue (email, step, scheduled_time, sent_time) VALUES (?, ?, ?, ?)",
                                         (email, step, datetime.now().isoformat(), datetime.now().isoformat()))
                else:
                    # CHẾ ĐỘ BÌNH THƯỜNG
                    # Gửi Email 1 ngay lập tức
                    if 1 in emails_content:
                        data = emails_content[1]
                        send_automated_email(email, data['subject'], data['body'])
                        cursor.execute("INSERT INTO email_queue (email, step, scheduled_time, sent_time) VALUES (?, ?, ?, ?)",
                                     (email, 1, datetime.now().isoformat(), datetime.now().isoformat()))
                    
                    # Lên lịch Email 2 (sau 2 ngày)
                    if 2 in emails_content:
                        sched2 = (datetime.now() + timedelta(days=2)).isoformat()
                        cursor.execute("INSERT INTO email_queue (email, step, scheduled_time) VALUES (?, ?, ?)",
                                     (email, 2, sched2))
                        print(f"--- Đã lên lịch Email 2 cho {email} vào {sched2}")
                    
                    # Lên lịch Email 3 (sau 3 ngày - tức là 1 ngày sau Email 2)
                    if 3 in emails_content:
                        sched3 = (datetime.now() + timedelta(days=3)).isoformat()
                        cursor.execute("INSERT INTO email_queue (email, step, scheduled_time) VALUES (?, ?, ?)",
                                     (email, 3, sched3))
                        print(f"--- Đã lên lịch Email 3 cho {email} vào {sched3}")
                
                conn.commit()
                self._send_response({"success": True, "message": "Thông tin đã được ghi nhận và chuỗi email đã được kích hoạt."})

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
