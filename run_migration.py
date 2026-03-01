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
    CREATE TABLE IF NOT EXISTS pet_daily_interactions (
      id SERIAL PRIMARY KEY,
      date TEXT NOT NULL UNIQUE,
      snack_mood_total INTEGER NOT NULL DEFAULT 0,
      toy_used TEXT,
      pet_interact_used BOOLEAN NOT NULL DEFAULT FALSE,
      all_meds_taken BOOLEAN NOT NULL DEFAULT FALSE,
      bp_completed BOOLEAN NOT NULL DEFAULT FALSE,
      last_decay_time TIMESTAMP,
      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_pet_daily_interactions_date ON pet_daily_interactions(date);
    """
    
    cur.execute(migration_sql)
    conn.commit()
    print("✅ pet_daily_interactions 表建立成功")
    
    cur.close()
    conn.close()
    print("✅ Migration 完成")
except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()
