import sqlite3
from datetime import datetime

# SQLite 資料庫路徑
DB_PATH = "data/gamemed.db"

try:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    print("✅ SQLite 資料庫已連線")
    
    cur = conn.cursor()
    
    # 查詢使用者
    phone = "0981123456"
    cur.execute("SELECT id, phone FROM users WHERE phone = ?", (phone,))
    user = cur.fetchone()
    
    if user:
        user_id = user["id"]
        print(f"✅ 找到使用者: ID={user_id}, Phone={user['phone']}")
        
        # 新增 10000 點
        amount = 10000
        cur.execute(
            """
            INSERT INTO point_ledger (user_id, datetime, delta, reason, ref_type, note)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, datetime.now().isoformat(), amount, "管理員贈送", "admin_gift", "測試用點數")
        )
        conn.commit()
        
        # 查詢該使用者的當前總點數
        cur.execute("SELECT COALESCE(SUM(delta), 0) as balance FROM point_ledger WHERE user_id = ?", (user_id,))
        balance = cur.fetchone()[0]
        
        print(f"✅ 成功新增 {amount} 點!")
        print(f"✅ 使用者 {user_id} 當前總點數: {balance}")
    else:
        print(f"❌ 找不到手機號碼為 {phone} 的使用者")
        print("提示: 請先在應用程式中註冊此帳號")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()
