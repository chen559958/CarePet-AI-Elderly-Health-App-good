from __future__ import annotations

from datetime import datetime

from .base import BaseRepository


class PointsRepository(BaseRepository):
    def add_ledger(self, user_id: int, delta: int, reason: str, ref_type: str | None, ref_id: int | None) -> int:
        with self._conn() as conn:
            now = datetime.utcnow()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO point_ledger (user_id, datetime, delta, reason, ref_type, ref_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (user_id, now, delta, reason, ref_type, ref_id),
                )
                ledger_id = cur._cursor.lastrowid if hasattr(cur, "_cursor") else cur.lastrowid
            conn.commit()
        return ledger_id

    def get_balance(self, user_id: int) -> int:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COALESCE(SUM(delta), 0) AS balance FROM point_ledger WHERE user_id = %s", (user_id,))
                row = cur.fetchone()
        return row["balance"]
