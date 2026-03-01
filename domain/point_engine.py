from __future__ import annotations
from datetime import datetime
from domain.models import ReminderEvent

class PointEngine:
    """
    積分引擎：計算用藥遵從度的積分獎勵
    根據服藥時間的準時程度和延遲次數來計算積分
    """
    
    # === 積分常數定義 ===
    POINTS_MED_INTAKE = 1   # 每次服藥積分 (每日上限 20)
    POINTS_BP_MEASURE = 15  # 量血壓積分 (每日上限 1 次)
    POINTS_ALL_MEDS = 10    # 全勤積分 (完成當日所有用藥)

    @classmethod
    def calculate_taken_points(cls, event: ReminderEvent, now: datetime) -> int:
        """
        計算服藥獲得的積分
        
        注意: 現在積分規則改為固定 +1 分 (每日上限 20),
        此方法保留是為了相容性,或如果有額外加成邏輯
        """
        return cls.POINTS_MED_INTAKE

    @classmethod
    def calculate_missed_penalty(cls) -> int:
        """
        計算漏服藥物的懲罰積分
        """
        return 0  # 暫時移除懲罰,或根據需求調整
