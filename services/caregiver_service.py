from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from domain.utils import get_now_taiwan
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.container import Container

@dataclass
class CaregiverMessage:
    title: str
    body: str
    timestamp: datetime

class CaregiverService:
    def __init__(self, container: Container | None):
        self.container = container

    @property
    def reminder_repo(self):
        return self.container.reminder_repo if self.container else None

    @property
    def drug_repo(self):
        return self.container.drug_repo if self.container else None

    async def check_daily_missed_dose(self, user_id: int) -> bool:
        """
        Checks if the user has missed doses for the entire day.
        Sends a specific LINE alert if so.
        """
        today_str = get_now_taiwan().strftime("%Y-%m-%d")
        import asyncio
        all_today_events = await asyncio.to_thread(self.reminder_repo.list_today_events, user_id, today_str)
        
        if not all_today_events:
            return False
            
        missed_today = [e for e in all_today_events if e.status == "missed"]
        
        # If there are missed events today, and all events so far are missed or snoozed (not taken)
        # Or more simply, if there's any missed dose and we want to alert "today missed"
        if missed_today:
            # We only send this specific "daily missed" alert once per day
            # (Self-check: we could use a session variable or a flag in DB, 
            # but for MVP simulation we'll just print it)
            
            print(f">>> [LINE NOTIFY SIMULATION] (User: {user_id}) <<<")
            print(f"To: Linked LINE ID")
            print(f"Message: 今日使用者未按時服藥喔！")
            print(f">>> ------------------------ <<<")
            return True
            
        return False

    async def check_and_notify_caregivers(self, user_id: int) -> int:
        """
        Scans for missed events that haven't been notified yet.
        Returns the number of notifications sent.
        """
        import asyncio
        missed_events = await asyncio.to_thread(self.reminder_repo.list_unnotified_missed_events, user_id)
        count = 0
        
        for event in missed_events:
            drug = await asyncio.to_thread(self.container.drug_repo.get_by_id, user_id, event.drug_id)
            drug_name = drug.drug_name if drug else "未知藥物"
            
            # Simulate sending LINE message
            title = "⚠️ 藥物漏領通知"
            body = f"您的親友漏領了藥物: {drug_name}。\n預計服用時間: {event.planned_time.strftime('%H:%M')}"
            
            print(f">>> [LINE NOTIFY SIMULATION] (User: {user_id}) <<<")
            print(f"To: Family Members")
            print(f"Title: {title}")
            print(f"Body: {body}")
            print(f">>> ------------------------ <<<")
            
            # Mark as notified to avoid duplicate alerts
            await asyncio.to_thread(self.reminder_repo.mark_caregiver_notified, user_id, event.id)
            count += 1
            
        return count
