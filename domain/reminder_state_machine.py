from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from domain.models import ReminderEvent, ReminderStatus

# Events that trigger transitions
ReminderCommand = Literal["mark_taken", "snooze", "mark_missed", "revoke"]

@dataclass
class StateTransition:
    new_status: ReminderStatus
    action_time: datetime | None = None
    new_planned_time: datetime | None = None
    should_notify: bool = False
    
class ReminderStateMachine:
    """
    Implements state transitions for ReminderEvent.
    
    Transitions:
    - scheduled -> notified (by system)
    - notified -> taken (by user)
    - notified -> snoozed (by user) -> scheduled (new time)
    - notified -> missed (by system timeout)
    - snoozed -> missed (by system timeout)
    """
    
    @staticmethod
    def apply(
        event: ReminderEvent, 
        command: ReminderCommand, 
        now: datetime, 
        snooze_minutes: int = 10
    ) -> StateTransition:
        if command == "mark_taken":
            if event.status in ("scheduled", "notified", "snoozed", "missed"):
                # Allow taking even if missed or scheduled (early take)
                return StateTransition(
                    new_status="taken",
                    action_time=now
                )
            raise ValueError(f"Cannot take medication when status is {event.status}")
            
        elif command == "snooze":
            if event.status in ("notified", "missed"): # Allow snooze if just missed? Spec says missed after 60.
                # If truly missed (cutoff passed), maybe shouldn't allow snooze?
                # Blueprint: "snooze +10".
                new_time = now + timedelta(minutes=snooze_minutes)
                return StateTransition(
                    new_status="snoozed",
                    new_planned_time=new_time,
                    should_notify=True
                )
            raise ValueError(f"Cannot snooze when status is {event.status}")
            
        elif command == "mark_missed":
            if event.status in ("scheduled", "notified", "snoozed"):
                return StateTransition(
                    new_status="missed"
                )
            # If already taken or revoked, ignore
            return StateTransition(new_status=event.status)
            
        elif command == "revoke":
            return StateTransition(new_status="revoked")
            
        raise ValueError(f"Unknown command {command}")
