"""
資料遷移腳本：從 PostgreSQL 匯出到 SQLite
"""
import os
import sys
import sqlite3
import psycopg2
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# PostgreSQL 連線資訊
PG_CONFIG = {
    'host': 'tpe1.clusters.zeabur.com',
    'port': 24709,
    'database': 'zeabur',
    'user': 'root',
    'password': '5Q926U3VDO7ijrKszlLRx08e1ZNgH4ym'
}

# SQLite 資料庫路徑
SQLITE_DB = 'data/gamemed.db'

# 需要遷移的資料表（按照外鍵依賴順序）
TABLES = [
    'users',
    'user_profile',
    'pets',
    'pet_collection',
    'drugs',
    'reminder_events',
    'blood_pressure',
    'shop_items',
    'user_inventory',
    'point_ledger',
    'pet_interaction_stats'
]

def migrate_data():
    print("開始資料遷移...")
    
    # 連接到 PostgreSQL
    print("連接到 PostgreSQL...")
    try:
        pg_conn = psycopg2.connect(**PG_CONFIG)
        pg_cur = pg_conn.cursor()
        print("✓ PostgreSQL 連接成功")
    except Exception as e:
        print(f"✗ PostgreSQL 連接失敗: {e}")
        return False
    
    # 連接到 SQLite
    print("連接到 SQLite...")
    try:
        sqlite_conn = sqlite3.connect(SQLITE_DB)
        sqlite_cur = sqlite_conn.cursor()
        print("✓ SQLite 連接成功")
    except Exception as e:
        print(f"✗ SQLite 連接失敗: {e}")
        pg_conn.close()
        return False
    
    try:
        # 遷移每個資料表
        for table in TABLES:
            print(f"\n處理資料表: {table}")
            
            # 從 PostgreSQL 讀取資料
            try:
                pg_cur.execute(f"SELECT * FROM {table}")
                rows = pg_cur.fetchall()
                
                if not rows:
                    print(f"  - {table} 沒有資料，跳過")
                    continue
                
                # 取得欄位名稱
                columns = [desc[0] for desc in pg_cur.description]
                print(f"  - 找到 {len(rows)} 筆資料")
                
                # 清空 SQLite 中的資料表
                sqlite_cur.execute(f"DELETE FROM {table}")
                
                # 插入資料到 SQLite
                placeholders = ','.join(['?' for _ in columns])
                insert_sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
                
                for row in rows:
                    try:
                        sqlite_cur.execute(insert_sql, row)
                    except Exception as e:
                        print(f"  ✗ 插入失敗: {e}")
                        print(f"    資料: {row}")
                
                sqlite_conn.commit()
                print(f"  ✓ {table} 遷移完成")
                
            except Exception as e:
                print(f"  ✗ {table} 遷移失敗: {e}")
                continue
        
        print("\n資料遷移完成！")
        return True
        
    except Exception as e:
        print(f"\n遷移過程發生錯誤: {e}")
        return False
    finally:
        pg_conn.close()
        sqlite_conn.close()

if __name__ == "__main__":
    success = migrate_data()
    sys.exit(0 if success else 1)
