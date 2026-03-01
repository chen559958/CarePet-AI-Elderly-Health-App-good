from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, Sequence

from .models import DrugItem, IntakePeriod, ReminderEvent, UserProfile

PERIOD_TO_FIELD: dict[IntakePeriod, str] = {
    "breakfast": "breakfast_time",
    "lunch": "lunch_time",
    "dinner": "dinner_time",
    "sleep": "sleep_time",
}


def compute_planned_time(date_str: str, base_hhmm: str, intake_timing: str) -> datetime:
    from domain.utils import to_taiwan_time
    dt = datetime.strptime(f"{date_str} {base_hhmm}", "%Y-%m-%d %H:%M")
    # Convert to aware (assuming naive is local/UTC, to_taiwan_time handles both)
    dt = to_taiwan_time(dt)
    
    if intake_timing == "after_meal":
        # 飯後 30 分鐘
        dt += timedelta(minutes=30)
    elif intake_timing == "before_meal":
        # 飯前 15 分鐘
        dt -= timedelta(minutes=15)
    elif intake_timing == "anytime":
        dt += timedelta(minutes=0)
    return dt


def generate_today_events(
    date_str: str,
    user: UserProfile,
    drugs: Iterable[DrugItem],
) -> Sequence[tuple[int, datetime]]:
    events: list[tuple[int, datetime]] = []
    for drug in drugs:
        if not drug.active:
            continue
        for period in drug.intake_periods:
            base_time = getattr(user, PERIOD_TO_FIELD[period])
            planned = compute_planned_time(date_str, base_time, drug.intake_timing)
            events.append((drug.id, planned))
    return events


def judge_missed(event: ReminderEvent, now: datetime, window_minutes: int = 60) -> bool:
    if event.status not in {"notified", "snoozed"}:
        return False
    diff = now - event.planned_time
    return diff.total_seconds() >= window_minutes * 60
