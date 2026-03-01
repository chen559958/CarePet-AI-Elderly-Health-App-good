import os
import sqlite3
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SQLITE_DB_PATH = Path("data/gamemed.db")

TABLES_TO_UPDATE = [
    "pets",
    "user_inventory",
    "pet_daily_interactions",
    "point_ledger",
    "user_profile",
    "blood_pressure",
    "drugs",
    "medication_logs",
    "reminder_events",
    "pet_collection",
    "appointments",
    "undo_actions"
]

UNIQUE_CONSTRAINTS = {
    "user_profile": ["user_id"],
    "drugs": ["user_id", "drug_name"],
    "pets": ["user_id"],
    "user_inventory": ["user_id", "item_id"],
    "reminder_events": ["user_id", "drug_id", "date", "planned_time"]
}

def migrate_sqlite():
    if not SQLITE_DB_PATH.exists():
        print(f"SQLite DB {SQLITE_DB_PATH} not found. Skipping.")
        return

    print(f"Migrating SQLite DB at {SQLITE_DB_PATH}...")
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cur = conn.cursor()

    for table in TABLES_TO_UPDATE:
        try:
            cur.execute(f"PRAGMA table_info({table})")
            columns = [info[1] for info in cur.fetchall()]
            
            if "user_id" not in columns:
                print(f"Adding user_id to {table} (SQLite)...")
                cur.execute(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER REFERENCES users(id)")
                cur.execute(f"UPDATE {table} SET user_id = 1 WHERE user_id IS NULL")
            
            # SQLite handles UNIQUE differently in ALTER TABLE (harder to add post-creation)
            # For simplicity in dev, we just skip SQLite unique migration or use a temp table
            # But the primary goal is multi-user isolation which columns provide.
        except Exception as e:
            print(f"Error migrating SQLite table {table}: {e}")

    conn.commit()
    conn.close()

def migrate_postgres():
    host = os.getenv("DB_HOST")
    if not host:
        print("DB_HOST not set. Skipping Postgres migration.")
        return

    print("Migrating Postgres DB...")
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            port=os.getenv("DB_PORT")
        )
        cur = conn.cursor()

        for table in TABLES_TO_UPDATE:
            try:
                cur.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='{table}' AND column_name='user_id'
                """)
                if not cur.fetchone():
                    print(f"Adding user_id to {table} (Postgres)...")
                    cur.execute(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER REFERENCES users(id)")
                    cur.execute(f"UPDATE {table} SET user_id = 1 WHERE user_id IS NULL")
                
                # Add UNIQUE constraints if defined
                if table in UNIQUE_CONSTRAINTS:
                    cols = UNIQUE_CONSTRAINTS[table]
                    constraint_name = f"uq_{table}_{'_'.join(cols)}"
                    
                    # Check if constraint exists
                    cur.execute(f"""
                        SELECT conname FROM pg_constraint 
                        WHERE conname='{constraint_name}'
                    """)
                    if not cur.fetchone():
                        print(f"Adding UNIQUE constraint {constraint_name} to {table}...")
                        cur.execute(f"ALTER TABLE {table} ADD CONSTRAINT {constraint_name} UNIQUE ({', '.join(cols)})")
            except Exception as e:
                print(f"Error migrating Postgres table {table}: {e}")
                conn.rollback() 

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Postgres connection failed: {e}")

if __name__ == "__main__":
    migrate_sqlite()
    migrate_postgres()
