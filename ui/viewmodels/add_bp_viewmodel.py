from __future__ import annotations
from datetime import datetime
from app.container import Container
from domain.pet_engine import PetEngine
from domain.watcher import reminder_watcher, pet_watcher
from dataclasses import dataclass

@dataclass
class BPScanResult:
    systolic: int
    diastolic: int

class AddBPViewModel:
    def __init__(self, container: Container):
        self.container = container
        self.bp_repo = container.bp_repo

    def scan_bp_report(self, image_path: str) -> BPScanResult:
        """模擬 AI 辨識血壓計畫面或報告"""
        # 實際應用中會在此呼叫 OCR/AI 服務
        return BPScanResult(systolic=120, diastolic=80)

    async def save_bp(self, systolic: int, diastolic: int, pulse: int | None = None) -> bool:
        """儲存血壓紀錄並發放獎勵"""
        import asyncio
        user = self.container.auth_service.get_current_user()
        if not user:
            print("Error saving BP: User not authenticated")
            return False

        try:
            # 1. 儲存紀錄
            await asyncio.to_thread(self.bp_repo.add_record, user.id, systolic, diastolic, pulse)
            
            # 2. 發放積分 (參考 HomeViewModel 邏輯)
            # 新規則: +15 點 (每日上限 1 次)
            from domain.point_engine import PointEngine
            # pet_interaction_repo is still sync
            if await asyncio.to_thread(self.container.pet_interaction_repo.mark_bp_completed, user.id):
                await asyncio.to_thread(
                    self.container.points_repo.add_ledger,
                    user_id=user.id,
                    delta=PointEngine.POINTS_BP_MEASURE,
                    reason="Blood Pressure Measured",
                    ref_type="blood_pressure",
                    ref_id=0
                )
                print(f"DEBUG: Blood Pressure Points Awarded (+{PointEngine.POINTS_BP_MEASURE})")
            else:
                print("DEBUG: Blood Pressure Points already awarded today.")
            
            # 3. 更新寵物狀態 (給點正面影響)
            current_pet = await self.container.pet_repo.get_pet(user.id)
            if current_pet:
                new_pet = PetEngine.apply_taken(current_pet) 
                await self.container.pet_repo.update_pet(
                    user_id=user.id,
                    mood=new_pet.mood,
                    stamina=new_pet.stamina,
                    state=new_pet.state
                )
            
            # 4. 每日首刷獎勵 XP (10點)
            stats = await self.container.pet_repo.get_daily_stats(user.id)
            if stats and not stats["bp_bonus_awarded"]:
                await self.container.pet_repo.update_daily_stats(user.id, bp_bonus_awarded=True)
                await self.container.pet_repo.add_exp(user.id, 10)
            
            reminder_watcher.notify()
            pet_watcher.notify()
            return True
        except Exception as e:
            print(f"Error saving BP: {e}")
            return False
