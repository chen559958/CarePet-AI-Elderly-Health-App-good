from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Sequence

ReminderStatus = Literal["scheduled", "notified", "snoozed", "taken", "missed", "revoked"]
IntakeTiming = Literal["after_meal", "before_meal", "anytime"]
IntakePeriod = Literal["breakfast", "lunch", "dinner", "sleep"]


@dataclass(slots=True)
class User:
    id: int
    phone: str
    password_hash: str
    created_at: datetime
    last_login: datetime | None = None



@dataclass(slots=True)
class UserProfile:
    id: int
    name: str
    phone: str | None
    email: str | None
    breakfast_time: str
    lunch_time: str
    dinner_time: str
    sleep_time: str
    haptics_enabled: bool
    snooze_minutes: int
    gentle_mode: bool
    notifications_enabled: bool = True
    line_id: str | None = None
    birthday: str | None = None




@dataclass(slots=True)
class DrugItem:
    id: int
    drug_name: str
    usage_method: str  # 吸入/口服/外敷
    intake_timing: str # 餐前/餐後
    intake_periods: Sequence[str]
    pills_per_intake: float

    hospital: str | None = None
    doctor: str | None = None
    department: str | None = None
    active: bool = True


@dataclass(slots=True)
class ReminderEvent:
    id: int
    drug_id: int
    date: str
    planned_time: datetime
    action_time: datetime | None
    status: ReminderStatus
    snooze_count: int
    caregiver_notified: bool = False
    notification_id: int | None = None


@dataclass(slots=True)
class PetState:
    id: int
    pet_name: str
    level: int
    mood: int
    stamina: int
    state: str
    exp: int
    bowl_expires_at: datetime
    image_path: str | None = None


@dataclass(slots=True)
class LedgerEntry:
    id: int
    datetime: datetime
    delta: int
    reason: str
    ref_type: str | None
    ref_id: int | None

@dataclass(slots=True)
class BloodPressureRecord:
    id: int
    date: str
    time: str
    systolic: int
    diastolic: int
    pulse: int | None
    photo_path: str | None
    created_at: datetime
