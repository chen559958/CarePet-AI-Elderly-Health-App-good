import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def check_columns():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            port=os.getenv("DB_PORT")
        )
        cur = conn.cursor()
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='reminder_events'")
        columns = [row[0] for row in cur.fetchall()]
        print(f"Columns in reminder_events: {columns}")
        
        cur.execute("""
            SELECT conname FROM pg_constraint 
            WHERE conname LIKE 'uq_reminder_events%'
        """)
        constraints = [row[0] for row in cur.fetchall()]
        print(f"Constraints on reminder_events: {constraints}")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_columns()
