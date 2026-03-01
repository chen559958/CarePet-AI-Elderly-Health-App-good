import os
import sqlite3
from pathlib import Path
import threading
from typing import Callable, Any
from dotenv import load_dotenv

try:
    import psycopg2
    from psycopg2 import pool
    from psycopg2.extras import RealDictConnection
except ImportError:
    psycopg2 = None
    pool = None
    RealDictConnection = Any # Dummy type for type hinting

try:
    import asyncpg
except ImportError:
    asyncpg = None

load_dotenv()

SCHEMA_PATH = Path("data/postgres_schema.sql")
SQLITE_SCHEMA_PATH = Path("data/schema.sql")
SQLITE_DB_PATH = Path("data/gamemed.db")

class SQLiteCompatCursor:
    """包裝 SQLite cursor 以支援 Postgres 語法與行為"""
    def __init__(self, cursor):
        self._cursor = cursor

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def execute(self, query: str, params: Any = None):
        # 將 Postgres 的 %s 轉換為 SQLite 的 ?
        if params is not None:
            query = query.replace("%s", "?")
            return self._cursor.execute(query, params)
        return self._cursor.execute(query)

    def fetchone(self):
        row = self._cursor.fetchone()
        return dict(row) if row else None

    def fetchall(self):
        rows = self._cursor.fetchall()
        return [dict(row) for row in rows]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cursor.close()

class SQLiteCompatConnection:
    """包裝 SQLite connection 以模擬 psycopg2"""
    def __init__(self, conn):
        self._conn = conn
        self._conn.row_factory = sqlite3.Row

    def cursor(self, **kwargs):
        return SQLiteCompatCursor(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # We don't close the singleton _sqlite_conn here to match 
        # previous behavior, but the context manager interface 
        # is needed for consistency in repository code.
        pass

    def close(self):
        # SQLite simulation: do not close if handled by pseudo-pool, 
        # but here we just wrap it. 
        # For true pooling we might need more, but for now 
        # we rely on the implementation below.
        self._conn.close()

# --- Connection Pool Logic ---

_pg_pool = None
_async_pg_pool = None
_sqlite_conn = None 
_init_lock = threading.Lock()
_pool_lock = threading.Lock()
_checked = False

async def init_async_pool():
    global _async_pg_pool
    if _async_pg_pool: return _async_pg_pool

    if os.getenv("FORCE_SQLITE", "").lower() == "true":
        print(">>> DEBUG: FORCE_SQLITE 為 True，跳過 Asyncpg 初始化。")
        return None

    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    dbname = os.getenv("DB_NAME", "gamemed")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASS", "postgres")


    if asyncpg:
        try:
            print(f">>> DEBUG: 嘗試建立 Asyncpg 連接池 ({host}:{port}/{dbname})...")
            _async_pg_pool = await asyncpg.create_pool(
                host=host,
                port=port,
                database=dbname,
                user=user,
                password=password,
                min_size=1,
                max_size=20,
                command_timeout=5.0
            )
            print(">>> DEBUG: Asyncpg 連接池建立成功。")
            return _async_pg_pool
        except Exception as e:
             print(f">>> DEBUG: Asyncpg 連接池初始化失敗: {e}")
             return None
    return None

def get_async_pool():
    return _async_pg_pool

def init_pool():
    global _pg_pool, _sqlite_conn
    with _pool_lock:
        if _pg_pool is not None or _sqlite_conn is not None:
            return
        
        if os.getenv("FORCE_SQLITE", "").lower() == "true":
            print(">>> DEBUG: 已由環境變數設定強制使用 SQLite。")
            host = None
        else:
            host = os.getenv("DB_HOST")
        
        if not host or host == "localhost":
            print(">>> DEBUG: 使用本地 SQLite 模式。")
            _pg_pool = None
        else:
            port = os.getenv("DB_PORT", "5432")
            dbname = os.getenv("DB_NAME", "gamemed")
            user = os.getenv("DB_USER", "postgres")
            password = os.getenv("DB_PASS", "postgres")

            if psycopg2:
                try:
                    print(f">>> DEBUG: 正在建立 PostgreSQL 連線 ({host})...")
                    _pg_pool = psycopg2.pool.ThreadedConnectionPool(
                        1, 20,
                        host=host,
                        port=port,
                        dbname=dbname,
                        user=user,
                        password=password,
                        connection_factory=RealDictConnection,
                        connect_timeout=3, # 縮短到 3 秒以便快速失敗
                        options='-c statement_timeout=10000'
                    )
                    print(">>> DEBUG: PostgreSQL 連線成功。")
                    return
                except Exception as e:
                    print(f">>> DEBUG: PostgreSQL 連線失敗 ({e})，正在切換至 SQLite...")
                    _pg_pool = None
    
    # Fallback
    print(">>> DEBUG: 啟動本地資料庫 (data/gamemed.db)...")
    _sqlite_conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)



def get_db_connection() -> Any:
    """
    Get a connection from the pool (Postgres) or the singleton (SQLite).
    WARNING: For Postgres, you MUST close() the connection to return it to the pool.
    """
    global _pg_pool, _sqlite_conn
    
    # Lazy Init
    if _pg_pool is None and _sqlite_conn is None:
        init_pool()

    if _pg_pool:
        try:
            # print("DEBUG: Requesting connection from Postgres pool...")
            conn = _pg_pool.getconn()
            print(f"DEBUG: Connection acquired. Pool status: Used={len(_pg_pool._used)} Total={_pg_pool.minconn}")
            # Monkey-patch close to putconn? 
            # Standard pattern: try/finally putconn.
            # But existing code might call conn.close().
            # Let's wrap it or ensure users use context manager?
            # Existing code uses `conn = get_or_init_connection()` and usually doesn't close it because it was a cached global.
            # ! CRITICAL CHANGE !
            # The previous code returned a GLOBAL cached connection that was rarely closed.
            # Now we want a pool. We need to handle `close()`.
            # To be compatible with existing code which might NOT close keys, 
            # we might need to be careful.
            # BUT: User asked for "Connection Pool (avoid every connect)". 
            # Actually, `SimpleConnectionPool` keeps connections open.
            # `getconn()` gives one.
            # We should wrap it to return to pool on close.
            
            # Simple wrapper to handle pool return
            class PooledConnWrapper:
                def __init__(self, pool, conn):
                    self._pool = pool
                    self._conn = conn
                    self._closed = False
                
                def __getattr__(self, name):
                    return getattr(self._conn, name)
                
                def cursor(self, *args, **kwargs):
                    return self._conn.cursor(*args, **kwargs)
                
                def commit(self):
                    self._conn.commit()
                
                def rollback(self):
                    self._conn.rollback()

                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc_val, exc_tb):
                    self.close()

                def close(self):
                    if not self._closed:
                        try:
                            print(f"DEBUG: Returning connection to Postgres pool. Pool status: Used={len(self._pool._used)}")
                            self._pool.putconn(self._conn)
                        except Exception as e:
                            print(f"DEBUG: Error putting connection back to pool: {e}")
                        finally:
                            self._closed = True

                def __del__(self):
                    if not self._closed:
                        self.close()
            
            return PooledConnWrapper(_pg_pool, conn)
            
        except Exception as e:
            print(f"DEBUG: Error getting connection from pool: {e}")
            raise e
            
    else:
        # SQLite: Return the wrapped singleton
        # We need to ensure we don't assume it's new every time.
        # It's the same object. 
        return SQLiteCompatConnection(_sqlite_conn)


def init_db(conn: Any) -> None:
    """根據連線類型初始化資料庫"""
    # Note: conn might be a wrapper now.
    is_sqlite = isinstance(conn, SQLiteCompatConnection)
    # Check underlying if wrapped
    if hasattr(conn, "_conn") and isinstance(conn._conn, sqlite3.Connection):
        is_sqlite = True
        
    schema_file = SQLITE_SCHEMA_PATH if is_sqlite else SCHEMA_PATH
    
    if not schema_file.exists():
        print(f"DEBUG: Missing schema file at {schema_file}")
        return

    with schema_file.open("r", encoding="utf-8") as f:
        schema_sql = f.read()
        
    with conn.cursor() as cur:
        if is_sqlite:
            # SQLite 的 execute 可能不支持一次執行多條語法，使用 executescript
            # Need to access underlying cursor if it's wrapped?
            # SQLiteCompatCursor wraps it.
            # but executescript is a method of sqlite3.Cursor.
            # SQLiteCompatCursor._cursor is the sqlite3.Cursor.
            cur._cursor.executescript(schema_sql)
        else:
            cur.execute(schema_sql)
    conn.commit()


# Backward compatibility wrapper
def get_or_init_connection(factory: Callable[[], Any] | None = None) -> Any:
    global _checked
    
    # We always need a connection first
    conn = get_db_connection()
    
    # 預防競爭：使用 Lock 確保只有一個執行緒進行初始化檢查與執行
    if not _checked:
        with _init_lock:
            # Double-check inside lock
            if not _checked:
                try:
                    with conn.cursor() as cur:
                        # Check for shop_items table as a marker
                        is_sqlite = isinstance(conn, SQLiteCompatConnection) or \
                                   (hasattr(conn, "_conn") and isinstance(conn._conn, sqlite3.Connection))

                        if is_sqlite:
                            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shop_items'")
                        else:
                            cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'shop_items')")
                        
                        row = cur.fetchone()
                        exists = False
                        if row:
                             if is_sqlite: exists = True
                             else: exists = row.get('exists', False)
                        
                        if not exists:
                            print("DEBUG: DB not initialized, running init_db...")
                            init_db(conn)
                            
                    _checked = True
                except Exception as e:
                    print(f"DEBUG: DB Check failed: {e}")
                    # If it fails, we keep _checked=False so next attempt might try again? 
                    # OR we set it to True to avoid infinite error loops?
                    # Generally, if it fails, the next one will try again.

    return conn
