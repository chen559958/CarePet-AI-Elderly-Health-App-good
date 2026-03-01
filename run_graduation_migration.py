import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            port=os.getenv("DB_PORT")
        )
        cursor = conn.cursor()
        
        with open("data/migrations/migration_pet_graduation.sql", "r", encoding="utf-8") as f:
            sql = f.read()
            cursor.execute(sql)
            
        conn.commit()
        print("✅ Graduation system migration applied successfully.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    run_migration()
