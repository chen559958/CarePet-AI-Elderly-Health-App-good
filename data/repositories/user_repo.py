from __future__ import annotations

from datetime import datetime
from domain.utils import get_now_taiwan

from domain.models import UserProfile

from .base import BaseRepository


class UserRepository(BaseRepository):
    def get_profile(self, user_id: int) -> UserProfile | None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM user_profile WHERE user_id = %s LIMIT 1", (user_id,))
                row = cur.fetchone()
        if not row:
            return None
        return self._to_profile(row)

    def init_default_profile_if_empty(self, user_id: int) -> UserProfile:
        profile = self.get_profile(user_id)
        if profile:
            return profile
        now = get_now_taiwan()
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO user_profile (user_id, name, breakfast_time, lunch_time, dinner_time, sleep_time,
                                       haptics_enabled, snooze_minutes, gentle_mode, line_id, birthday, notifications_enabled, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        "阿姨",
                        "07:30",
                        "12:00",
                        "18:00",
                        "22:30",
                        1,
                        10,
                        1,
                        None,
                        None,
                        1,
                        now,
                        now,
                    ),
                )
            conn.commit()
        return self.get_profile(user_id)  # type: ignore

    def update_profile(self, user_id: int, profile: UserProfile) -> None:
        with self._conn() as conn:
            now = get_now_taiwan()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE user_profile
                    SET name = %s, breakfast_time = %s, lunch_time = %s, dinner_time = %s, sleep_time = %s,
                        haptics_enabled = %s, snooze_minutes = %s, gentle_mode = %s, line_id = %s, birthday = %s,
                        notifications_enabled = %s, updated_at = %s
                    WHERE user_id = %s
                    """,
                    (
                        profile.name,
                        profile.breakfast_time,
                        profile.lunch_time,
                        profile.dinner_time,
                        profile.sleep_time,
                        1 if profile.haptics_enabled else 0,
                        profile.snooze_minutes,
                        1 if profile.gentle_mode else 0,
                        profile.line_id,
                        profile.birthday,
                        1 if profile.notifications_enabled else 0,
                        now,
                        user_id,
                    ),
                )
            conn.commit()

    @staticmethod
    def _to_profile(row: dict) -> UserProfile:
        return UserProfile(
            id=row["id"],
            name=row["name"],
            phone=row["phone"],
            email=row["email"],
            breakfast_time=row["breakfast_time"],
            lunch_time=row["lunch_time"],
            dinner_time=row["dinner_time"],
            sleep_time=row["sleep_time"],
            haptics_enabled=bool(row["haptics_enabled"]),
            snooze_minutes=row["snooze_minutes"],
            gentle_mode=bool(row["gentle_mode"]),
            notifications_enabled=bool(row.get("notifications_enabled", 1)),
            line_id=row["line_id"] if "line_id" in row.keys() else None,
            birthday=row["birthday"] if "birthday" in row.keys() else None,
        )
