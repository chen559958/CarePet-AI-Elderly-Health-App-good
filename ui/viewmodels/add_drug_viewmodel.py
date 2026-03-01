from __future__ import annotations
from typing import Sequence
from app.container import Container
from domain.models import IntakePeriod
from domain.watcher import reminder_watcher
from domain.vision_engine import VisionEngine, ScannedMedication

class AddDrugViewModel:
    def __init__(self, container: Container):
        self.container = container
        self.drug_repo = container.drug_repo

    async def scan_medication(self, image_path: str) -> list[ScannedMedication]:
        import asyncio
        # 使用 to_thread 避免阻塞 Flet 事件循環
        return await asyncio.to_thread(VisionEngine.analyze_drug_bag, image_path)

    def add_medication(
        self,
        name: str,
        periods: Sequence[str],
        timing: str = "after_meal",
        pills: float = 1.0,
        usage_method: str = "口服",
        hospital: str | None = None,
        doctor: str | None = None,
        department: str | None = None
    ) -> bool:
        if not name:
            return False

        try:
            user = self.container.auth_service.get_current_user()
            if not user:
                return False

            self.drug_repo.add_drug(
                user_id=user.id,
                drug_name=name,
                intake_periods=periods,
                intake_timing=timing,
                pills_per_intake=pills,
                usage_method=usage_method,
                hospital=hospital,
                doctor=doctor,
                department=department
            )
            # Notify watchers so home page generates new reminders if needed
            reminder_watcher.notify()
            return True
        except Exception as e:
            print(f"Error adding medication: {e}")
            return False

    def get_drug(self, drug_id: int):
        """獲取特定藥品資訊"""
        user = self.container.auth_service.get_current_user()
        if not user:
            return None
        return self.drug_repo.get_by_id(user.id, drug_id)

    def update_medication(
        self,
        drug_id: int,
        name: str,
        periods: Sequence[str],
        timing: str = "after_meal",
        pills: float = 1.0,
        usage_method: str = "口服",
        hospital: str | None = None,
        doctor: str | None = None,
        department: str | None = None
    ) -> bool:
        """更新現有藥品資訊"""
        if not name:
            return False

        try:
            user = self.container.auth_service.get_current_user()
            if not user:
                return False

            self.drug_repo.update_drug(
                user_id=user.id,
                drug_id=drug_id,
                drug_name=name,
                intake_periods=periods,
                intake_timing=timing,
                pills_per_intake=pills,
                usage_method=usage_method,
                hospital=hospital,
                doctor=doctor,
                department=department
            )
            # Notify watchers to refresh reminders
            reminder_watcher.notify()
            return True
        except Exception as e:
            print(f"Error updating medication: {e}")
            return False


