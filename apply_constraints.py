import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

UNIQUE_CONSTRAINTS = {
    "user_profile": ["user_id"],
    "drugs": ["user_id", "drug_name"],
    "pets": ["user_id"],
    "user_inventory": ["user_id", "item_id"],
    "reminder_events": ["user_id", "drug_id", "date", "planned_time"]
}

def apply_constraints():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            port=os.getenv("DB_PORT")
        )
        cur = conn.cursor()
        
        for table, cols in UNIQUE_CONSTRAINTS.items():
            constraint_name = f"uq_{table}_{'_'.join(cols)}"
            # Check if constraint exists
            cur.execute(f"SELECT conname FROM pg_constraint WHERE conname='{constraint_name}'")
            if not cur.fetchone():
                print(f"Adding UNIQUE constraint {constraint_name} to {table}...")
                try:
                    # In case of duplicates, we might need to clean up first, 
                    # but for now let's hope it's clean (or it will fail and we'll see)
                    cur.execute(f"ALTER TABLE {table} ADD CONSTRAINT {constraint_name} UNIQUE ({', '.join(cols)})")
                    print(f"Successfully added {constraint_name}")
                except Exception as e:
                    print(f"Failed to add constraint to {table}: {e}")
                    conn.rollback()
                    continue
        
        conn.commit()
        conn.close()
        print("Done.")
    except Exception as e:
        print(f"Error connecting: {e}")

if __name__ == "__main__":
    apply_constraints()
