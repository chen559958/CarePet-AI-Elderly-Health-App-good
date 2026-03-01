import sqlite3
import os
from datetime import datetime

# 展示用資料庫路徑
db_path = "data/gamemed.db"

def seed_gallery():
    if not os.path.exists(db_path):
        print("Database not found.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # 獲取第一個使用者 ID (通常是 1)
        cur.execute("SELECT id FROM users LIMIT 1")
        res = cur.fetchone()
        if not res:
            print("No users found to seed.")
            return
        user_id = res[0]
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 準備資料
        # 注意：image_path 需對應 assets/gallery/ 下的檔案
        demo_pets = [
            (user_id, "旺財", "cat", "assets/gallery/pet_cat.png", 12, now, now),
            (user_id, "薑母鴨", "duck", "assets/gallery/pet_duck.png", 12, now, now),
        ]

        for p in demo_pets:
            # 檢查是否已存在，避免重複
            cur.execute("SELECT id FROM pet_collection WHERE user_id=? AND pet_type=?", (p[0], p[2]))
            if not cur.fetchone():
                cur.execute(
                    "INSERT INTO pet_collection (user_id, pet_name, pet_type, image_path, final_level, graduated_at, unlocked_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    p
                )
                print(f"Seeded: {p[1]} ({p[2]})")
            else:
                print(f"Skipped: {p[1]} (already exists)")

        conn.commit()
        conn.close()
        print("Gallery seeding completed.")
    except Exception as e:
        print(f"Error seeding gallery: {e}")

if __name__ == "__main__":
    seed_gallery()
