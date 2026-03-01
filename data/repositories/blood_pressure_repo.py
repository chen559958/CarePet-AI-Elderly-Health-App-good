from __future__ import annotations
from datetime import datetime
from domain.utils import get_now_taiwan, to_taiwan_time
from typing import List, Optional
from domain.models import BloodPressureRecord
from .base import BaseRepository

class BloodPressureRepository(BaseRepository):

    def add_record(self, user_id: int, systolic: int, diastolic: int, pulse: Optional[int] = None):
        with self._conn() as conn:
            now = get_now_taiwan()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")
            
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO blood_pressure (user_id, date, time, systolic, diastolic, pulse, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (user_id, date_str, time_str, systolic, diastolic, pulse, now)
                )
            conn.commit()

    def get_today_record(self, user_id: int) -> Optional[dict]:
        with self._conn() as conn:
            today = datetime.now().strftime("%Y-%m-%d")
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM blood_pressure WHERE user_id = %s AND date = %s ORDER BY created_at DESC LIMIT 1",
                    (user_id, today)
                )
                row = cur.fetchone()
        
        if row:
            d = dict(row)
            d["created_at"] = to_taiwan_time(d["created_at"])
            return d
        return None

    def list_recent_records(self, user_id: int, limit: int = 7) -> List[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM blood_pressure WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
                    (user_id, limit)
                )
                rows = cur.fetchall()
        res = []
        for row in rows:
            d = dict(row)
            d["created_at"] = to_taiwan_time(d["created_at"])
            res.append(d)
        return res
