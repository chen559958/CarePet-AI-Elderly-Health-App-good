from __future__ import annotations

from typing import Callable
try:
    from psycopg2.extras import RealDictConnection
except ImportError:
    from typing import Any
    RealDictConnection = Any


class BaseRepository:
    def __init__(self, conn_factory: Callable[[], RealDictConnection]):
        self._conn_factory = conn_factory

    def _conn(self) -> RealDictConnection:
        return self._conn_factory()

    def safe_execute(self, operation: Callable[[RealDictConnection], any]) -> any:
        """
        安全執行資料庫操作，自動處理 commit 和 rollback 並確保釋放連線
        """
        conn = self._conn()
        try:
            result = operation(conn)
            conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
