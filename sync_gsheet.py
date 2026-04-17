# -*- coding: utf-8 -*-
import sqlite3
import urllib.request
import csv
import io
import os
from datetime import datetime

import sys
import io

# Đảm bảo in được tiếng Việt trên Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Cấu hình
GSHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1S3REQQIGS12sO294QaQT8DXJqmDBEO9qUZlqBA-9MCY/export?format=csv"
DB_PATH = "brain.db"

def sync():
    print(f"[{datetime.now()}] Đang bắt đầu đồng bộ từ Google Sheets...")
    
    try:
        # 1. Tải dữ liệu
        response = urllib.request.urlopen(GSHEET_CSV_URL)
        content = response.read().decode('utf-8')
        
        # 2. Parse CSV
        # Bỏ qua dòng đầu tiên (Tiêu đề lớn)
        lines = content.splitlines()[1:]
        reader = csv.reader(lines)
        headers = next(reader) # Dòng tiêu đề cột: THỜI GIAN, TÊN, SỐ ĐIỆN THOẠI...
        
        # 3. Kết nối Database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        new_count = 0
        update_count = 0
        
        for row in reader:
            if not row or len(row) < 3:
                continue
                
            time_str = row[0]
            name = row[1].strip()
            phone = row[2].strip()
            
            # Làm sạch số điện thoại (bỏ khoảng trắng, v.v.)
            phone = "".join(filter(str.isdigit, phone))
            if not phone: continue
            
            # Chuẩn hóa số điện thoại: thêm số 0 ở đầu nếu thiếu
            if not phone.startswith('0') and len(phone) >= 9:
                phone = '0' + phone
                
            vande = row[3] if len(row) > 3 else ""
            giaiphap = row[4] if len(row) > 4 else ""
            muctieu = row[5] if len(row) > 5 else ""
            
            notes = f"Vấn đề: {vande}\nGiải pháp: {giaiphap}\nMục tiêu: {muctieu}"
            
            # Chuyển đổi format thời gian nếu có thể (dd/mm/yyyy hh:mm:ss -> yyyy-mm-dd hh:mm:ss)
            try:
                dt = datetime.strptime(time_str, "%d/%m/%Y %H:%M:%S")
                created_at = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 4. Kiểm tra và Insert vào DB
            cursor.execute("SELECT id FROM customers WHERE phone = ?", (phone,))
            existing = cursor.fetchone()
            
            if existing:
                # Cập nhật nếu đã tồn tại
                cursor.execute("""
                    UPDATE customers SET name=?, notes=? WHERE id=?
                """, (name, notes, existing[0]))
                update_count += 1
            else:
                # Thêm mới
                cursor.execute("""
                    INSERT INTO customers (name, phone, notes, created_at)
                    VALUES (?, ?, ?, ?)
                """, (name, phone, notes, created_at))
                new_count += 1
                
        conn.commit()
        conn.close()
        
        msg = f"Đồng bộ thành công! Thêm mới: {new_count}, Cập nhật: {update_count}"
        print(msg)
        return {"success": True, "message": msg}
        
    except Exception as e:
        error_msg = f"Lỗi đồng bộ: {str(e)}"
        print(error_msg)
        return {"success": False, "error": error_msg}

if __name__ == "__main__":
    sync()
