from __future__ import annotations

from datetime import datetime

from .base import BaseRepository


class UndoRepository(BaseRepository):
    def insert(self, user_id: int, action_key: str, expires_at: datetime, payload_json: str) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO undo_actions (user_id, action_key, expires_at, payload_json, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (user_id, action_key, expires_at, payload_json, datetime.utcnow()),
                )
            conn.commit()

    def get(self, user_id: int, action_key: str) -> dict | None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM undo_actions WHERE action_key = %s AND user_id = %s",
                    (action_key, user_id),
                )
                row = cur.fetchone()
        return dict(row) if row else None

    def delete(self, user_id: int, action_key: str) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM undo_actions WHERE action_key = %s AND user_id = %s", (action_key, user_id))
            conn.commit()
