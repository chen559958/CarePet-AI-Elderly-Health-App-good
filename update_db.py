import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT")
    )
    print("✅ 資料庫已連線")
    
    cur = conn.cursor()
    
    # Add exp column to pets table
    try:
        cur.execute("ALTER TABLE pets ADD COLUMN exp INTEGER NOT NULL DEFAULT 0")
        print("✅ 新增 exp 欄位成功")
    except Exception as e:
        print(f"⚠️  exp 欄位可能已存在: {e}")
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ 資料庫更新完成")
except Exception as e:
    print(f"❌ 錯誤: {e}")
