import os
import sys
from dotenv import load_dotenv

# 將當前目錄加入 path
sys.path.append(os.getcwd())

from data.database import get_or_init_connection

def fix_postgres():
    load_dotenv()
    conn = get_or_init_connection()
    
    # 檢查是否為 PostgreSQL
    if "psycopg2" not in str(type(conn)).lower():
        print("DEBUG: 目前使用的是 SQLite，略過 PostgreSQL 遷移。")
        return

    print("DEBUG: 正在修復 PostgreSQL 綱要...")
    with conn.cursor() as cur:
        # 1. 檢查並建立 pet_daily_interactions 表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pet_daily_interactions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                date TEXT NOT NULL,
                snack_mood_total INTEGER NOT NULL DEFAULT 0,
                toy_used TEXT,
                pet_interact_used INTEGER NOT NULL DEFAULT 0,
                all_meds_taken INTEGER NOT NULL DEFAULT 0,
                bp_completed INTEGER NOT NULL DEFAULT 0,
                bp_bonus_awarded INTEGER NOT NULL DEFAULT 0,
                med_points_today INTEGER NOT NULL DEFAULT 0,
                last_decay_time TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, date)
            )
        """)
        print("DEBUG: 確保 pet_daily_interactions 表存在。")

        # 2. 檢查並補齊 bp_bonus_awarded 欄位 (預防萬一表已存在但缺欄位)
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'pet_daily_interactions' AND column_name = 'bp_bonus_awarded'
        """)
        if not cur.fetchone():
            print("DEBUG: 補齊 bp_bonus_awarded 欄位...")
            cur.execute("ALTER TABLE pet_daily_interactions ADD COLUMN bp_bonus_awarded INTEGER NOT NULL DEFAULT 0")
        
        # 3. 檢查並補齊 user_profile 缺失欄位
        profile_cols = {
            "birthday": "TEXT",
            "line_id": "TEXT",
            "notifications_enabled": "INTEGER NOT NULL DEFAULT 1"
        }
        for col_name, col_type in profile_cols.items():
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'user_profile' AND column_name = %s
            """, (col_name,))
            if not cur.fetchone():
                print(f"DEBUG: 補齊 user_profile.{col_name} 欄位...")
                cur.execute(f"ALTER TABLE user_profile ADD COLUMN {col_name} {col_type}")

        # 4. 確保索引存在
        cur.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relname = 'idx_pet_daily_interactions_date' AND n.nspname = 'public') THEN
                    CREATE INDEX idx_pet_daily_interactions_date ON pet_daily_interactions(date);
                END IF;
            END $$;
        """)

    conn.commit()
    print("DEBUG: PostgreSQL 綱要修復完成。")

if __name__ == "__main__":
    fix_postgres()
