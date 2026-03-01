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
    
    # 執行 migration
    migration_sql = """
    ALTER TABLE pet_collection ADD COLUMN IF NOT EXISTS unlock_level INTEGER NOT NULL DEFAULT 1;
    """
    
    cur.execute(migration_sql)
    conn.commit()
    print("✅ unlock_level 欄位新增成功")
    
    cur.close()
    conn.close()
    print("✅ Migration 完成")
except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()
