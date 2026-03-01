from __future__ import annotations

from datetime import datetime

from .base import BaseRepository


class LogRepository(BaseRepository):
    def add_med_log(self, user_id: int, *, date: str, time: str, drug_id: int, status: str, reminder_event_id: int | None) -> int:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO medication_logs (user_id, date, time, drug_id, status, reminder_event_id, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (user_id, date, time, drug_id, status, reminder_event_id, datetime.utcnow()),
                )
                log_id = cur._cursor.lastrowid if hasattr(cur, "_cursor") else cur.lastrowid
            conn.commit()
        return log_id

    def add_bp_log(self, user_id: int, *, date: str, time: str, systolic: int, diastolic: int, pulse: int | None) -> int:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO blood_pressure (user_id, date, time, systolic, diastolic, pulse, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (user_id, date, time, systolic, diastolic, pulse, datetime.utcnow()),
                )
                log_id = cur._cursor.lastrowid if hasattr(cur, "_cursor") else cur.lastrowid
            conn.commit()
        return log_id
