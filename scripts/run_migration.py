from data.database import get_or_init_connection
import os

def run_migration():
    print("Starting migration...")
    
    # Read the SQL file
    migration_file = os.path.join("data", "migrations", "fix_drug_constraint.sql")
    with open(migration_file, "r", encoding="utf-8") as f:
        sql = f.read()
        
    conn = get_or_init_connection()
    try:
        with conn.cursor() as cur:
            print(f"Executing SQL from {migration_file}...")
            cur.execute(sql)
        conn.commit()
        print("Migration completed successfully!")
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()
