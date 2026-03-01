from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


class NotificationBackend(Protocol):
    def schedule(self, notification_id: int, when: datetime, title: str, body: str) -> None: ...
    def cancel(self, notification_id: int) -> None: ...


@dataclass
class LocalNotificationService:
    backend: NotificationBackend

    def schedule(self, event_id: int, planned_time: datetime, title: str, body: str) -> int:
        notification_id = event_id
        self.backend.schedule(notification_id, planned_time, title, body)
        return notification_id

    def cancel(self, notification_id: int) -> None:
        self.backend.cancel(notification_id)

    def reschedule(self, event_id: int, planned_time: datetime, title: str, body: str) -> int:
        self.cancel(event_id)
        return self.schedule(event_id, planned_time, title, body)
