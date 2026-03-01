import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def migrate():
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    dbname = os.getenv("DB_NAME", "gamemed")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASS", "postgres")
    
    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )
    try:
        with conn.cursor() as cur:
            print("Adding notifications_enabled to user_profile...")
            cur.execute("ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS notifications_enabled INTEGER DEFAULT 1;")
            conn.commit()
            print("Migration successful.")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
