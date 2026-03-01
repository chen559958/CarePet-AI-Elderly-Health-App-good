"""
簡化版資料遷移：只遷移使用者帳號
"""
import sqlite3
import psycopg2

# PostgreSQL 連線資訊
PG_CONFIG = {
    'host': 'tpe1.clusters.zeabur.com',
    'port': 24709,
    'database': 'zeabur',
    'user': 'root',
    'password': '5Q926U3VDO7ijrKszlLRx08e1ZNgH4ym'
}

SQLITE_DB = 'data/gamemed.db'

print("開始遷移使用者帳號...")

# 連接資料庫
pg_conn = psycopg2.connect(**PG_CONFIG)
pg_cur = pg_conn.cursor()
sqlite_conn = sqlite3.connect(SQLITE_DB)
sqlite_cur = sqlite_conn.cursor()

# 只遷移 users 資料表
pg_cur.execute("SELECT id, phone, password_hash, created_at FROM users")
users = pg_cur.fetchall()

print(f"找到 {len(users)} 個使用者帳號")

# 清空並插入
sqlite_cur.execute("DELETE FROM users")
for user in users:
    sqlite_cur.execute(
        "INSERT INTO users (id, phone, password_hash, created_at) VALUES (?, ?, ?, ?)",
        user
    )
    print(f"  ✓ 遷移帳號: {user[1]}")

sqlite_conn.commit()
print("\n遷移完成！")

pg_conn.close()
sqlite_conn.close()
