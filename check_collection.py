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
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM pet_collection")
    count = cursor.fetchone()[0]
    print(f"DEBUG: pet_collection count = {count}")
    
    if count > 0:
        cursor.execute("SELECT * FROM pet_collection LIMIT 5")
        print("DEBUG: First 5 rows:", cursor.fetchall())
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
