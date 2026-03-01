import os
import sys
import sqlite3
from pathlib import Path

# 定位資料庫路徑
SQLITE_DB_PATH = Path("data/gamemed.db")

def force_update_name():
    phone = "0981123456"
    new_name = "李"
    
    if not SQLITE_DB_PATH.exists():
        print(f"錯誤: 找不到資料庫檔案 {SQLITE_DB_PATH}")
        return

    print(f"正在連接資料庫: {SQLITE_DB_PATH}...")
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    
    try:
        cur = conn.cursor()
        
        # 1. 查找用戶 ID
        print(f"正在尋找電話為 {phone} 的用戶...")
        cur.execute("SELECT id FROM users WHERE phone = ?", (phone,))
        user_row = cur.fetchone()
        
        if not user_row:
            print(f"錯誤: 找不到用戶 {phone}")
            return
            
        user_id = user_row['id']
        print(f"找到用戶 ID: {user_id}")
        
        # 2. 更新名稱
        print(f"正規劃將 user_profile 表中的名稱更新為 '{new_name}'...")
        cur.execute("UPDATE user_profile SET name = ? WHERE user_id = ?", (new_name, user_id))
        
        affected = cur.rowcount
        conn.commit()
        
        if affected > 0:
            print(f"成功! 已更新 {affected} 筆資料。用戶 {phone} 的名稱現在是 '{new_name}'。")
        else:
            print("警告: SQL 已執行但沒有資料被更新 (可能該用戶本來就叫這個名字，或者 user_profile 中沒有該 user_id)。")
            
    except Exception as e:
        print(f"執行 SQL 時出錯: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    force_update_name()
