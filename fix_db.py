import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def fix_db():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            port=os.getenv("DB_PORT")
        )
        cur = conn.cursor()
        
        # 1. Fix user_profile (one per user)
        print("Fixing user_profile...")
        cur.execute("""
            DELETE FROM user_profile a USING user_profile b
            WHERE a.id < b.id AND a.user_id = b.user_id;
        """)
        cur.execute("ALTER TABLE user_profile ADD CONSTRAINT uq_user_profile_user_id UNIQUE (user_id);")
        
        # 2. Fix drugs (unique name per user)
        print("Fixing drugs...")
        cur.execute("""
            DELETE FROM drugs a USING drugs b
            WHERE a.id < b.id AND a.user_id = b.user_id AND a.drug_name = b.drug_name;
        """)
        cur.execute("ALTER TABLE drugs ADD CONSTRAINT uq_drugs_user_id_drug_name UNIQUE (user_id, drug_name);")
        
        # 3. Fix reminder_events
        print("Fixing reminder_events...")
        cur.execute("""
            DELETE FROM reminder_events a USING reminder_events b
            WHERE a.id < b.id AND a.user_id = b.user_id AND a.drug_id = b.drug_id 
              AND a.date = b.date AND a.planned_time = b.planned_time;
        """)
        cur.execute("ALTER TABLE reminder_events ADD CONSTRAINT uq_reminder_events_uid_did_date_time UNIQUE (user_id, drug_id, date, planned_time);")
        
        # 4. Fix pets
        print("Fixing pets...")
        cur.execute("""
            DELETE FROM pets a USING pets b
            WHERE a.id < b.id AND a.user_id = b.user_id;
        """)
        cur.execute("ALTER TABLE pets ADD CONSTRAINT uq_pets_user_id UNIQUE (user_id);")

        conn.commit()
        print("Database schema fixed successfully!")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
        if conn: conn.rollback()

if __name__ == "__main__":
    fix_db()
