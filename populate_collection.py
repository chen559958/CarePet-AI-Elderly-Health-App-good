import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    port=os.getenv("DB_PORT")
)
cursor = conn.cursor()

# Check if data exists
cursor.execute("SELECT count(*) FROM pet_collection")
count = cursor.fetchone()[0]

if count == 0:
    print("Initializing pet collection data...")
    pets = [
        ("幼年期", "Normal", 1, "assets/pets/baby.png"),
        ("成長期", "Normal", 5, "assets/pets/child.png"),
        ("成熟期", "Normal", 10, "assets/pets/adult.png"),
        ("完全體", "Normal", 20, "assets/pets/perfect.png"),
        ("究極體", "Normal", 50, "assets/pets/ultimate.png"),
        ("生病狀態", "Sick", 1, "assets/pets/sick.png"),
        ("旅遊狀態", "Traveling", 1, "assets/pets/traveling.png"),
    ]
    
    for name, type_, unlock_lv, img in pets:
        try:
            cursor.execute(
                """
                INSERT INTO pet_collection (pet_name, pet_type, unlock_level, image_path, unlocked_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                """,
                (name, type_, unlock_lv, img)
            )
        except Exception as e:
            print(f"Error inserting {name}: {e}")
            conn.rollback()
    conn.commit()
    print("Inserted default pet collection data.")
else:
    print("Data already exists.")

conn.close()
