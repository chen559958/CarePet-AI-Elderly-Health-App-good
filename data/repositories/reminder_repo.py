from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Sequence
from domain.utils import get_now_taiwan

from domain.models import ReminderEvent

from .base import BaseRepository


@dataclass
class ReminderRow:
    id: int
    drug_id: int
    date: str
    planned_time: datetime
    action_time: datetime | None
    status: str
    snooze_count: int
    notification_id: int | None


class ReminderRepository(BaseRepository):
    def create_events_for_today(self, user_id: int, date_str: str, planned_events: Sequence[tuple[int, datetime]]) -> None:
        with self._conn() as conn:
            now = get_now_taiwan()
            with conn.cursor() as cur:
                for drug_id, planned_time in planned_events:
                    cur.execute(
                        """
                        INSERT INTO reminder_events
                            (user_id, drug_id, date, planned_time, status, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, 'scheduled', %s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (user_id, drug_id, date_str, planned_time, now, now),
                    )
            conn.commit()

    def list_today_events(self, user_id: int, date_str: str) -> Sequence[ReminderEvent]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM reminder_events
                    WHERE user_id = %s AND date = %s
                    ORDER BY planned_time ASC
                    """,
                    (user_id, date_str),
                )
                rows = cur.fetchall()
        return [self._to_event(row) for row in rows]

    def list_all_events(self, user_id: int, limit: int = 50) -> Sequence[ReminderEvent]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT * FROM reminder_events
                    WHERE user_id = %s
                    ORDER BY planned_time DESC
                    LIMIT {limit}
                    """,
                    (user_id,)
                )
                rows = cur.fetchall()
        return [self._to_event(row) for row in rows]

    def update_status(self, user_id: int, event_id: int, status: str, action_time: datetime | None = None) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE reminder_events
                    SET status = %s, action_time = %s, updated_at = %s
                    WHERE id = %s AND user_id = %s
                    """,
                    (
                        status,
                        action_time,
                        get_now_taiwan(),
                        event_id,
                        user_id,
                    ),
                )
            conn.commit()

    def update_planned_time(self, user_id: int, event_id: int, new_time: datetime, status: str) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE reminder_events
                    SET planned_time = %s, status = %s, snooze_count = snooze_count + 1, updated_at = %s
                    WHERE id = %s AND user_id = %s
                    """,
                    (
                        new_time,
                        status,
                        get_now_taiwan(),
                        event_id,
                        user_id,
                    ),
                )
            conn.commit()

    def mark_missed_overdue(self, user_id: int, now: datetime, window_minutes: int = 60) -> int:
        with self._conn() as conn:
            cutoff = now - timedelta(minutes=window_minutes)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE reminder_events
                    SET status = 'missed', updated_at = %s
                    WHERE user_id = %s
                      AND status IN ('notified','snoozed','scheduled')
                      AND planned_time <= %s
                    """,
                    (now, user_id, cutoff),
                )
                rowcount = cur.rowcount
            conn.commit()
        return rowcount

    def list_unnotified_missed_events(self, user_id: int) -> Sequence[ReminderEvent]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM reminder_events
                    WHERE user_id = %s AND status = 'missed' AND caregiver_notified = 0
                    """,
                    (user_id,)
                )
                rows = cur.fetchall()
        return [self._to_event(row) for row in rows]

    def mark_caregiver_notified(self, user_id: int, event_id: int) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE reminder_events SET caregiver_notified = 1 WHERE id = %s AND user_id = %s",
                    (event_id, user_id)
                )
            conn.commit()

    @staticmethod
    def _to_event(row: dict) -> ReminderEvent:
        from domain.utils import to_taiwan_time
        planned = to_taiwan_time(row["planned_time"])
        action_time = to_taiwan_time(row["action_time"]) if row.get("action_time") else None
        return ReminderEvent(
            id=row["id"],
            drug_id=row["drug_id"],
            date=row["date"],
            planned_time=planned,
            action_time=action_time,
            status=row["status"],
            snooze_count=row["snooze_count"],
            caregiver_notified=bool(row["caregiver_notified"]),
            notification_id=row["notification_id"],
        )
