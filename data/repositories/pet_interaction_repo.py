from __future__ import annotations
from datetime import datetime, date, timedelta
from typing import Optional
from .base import BaseRepository
from domain.utils import get_now_taiwan

class PetInteractionRepository(BaseRepository):
    """
    寵物每日互動追蹤 Repository
    負責管理零食、玩具、寵物互動的每日上限
    """
    
    def get_today_interactions(self, user_id: int) -> dict:
        """
        取得今日互動記錄,如果不存在則建立
        """
        with self._conn() as conn:
            today = date.today().isoformat()
            
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM pet_daily_interactions WHERE user_id = %s AND date = %s", (user_id, today))
                row = cur.fetchone()
                
                if not row:
                    # 建立今日記錄
                    cur.execute(
                        """
                        INSERT INTO pet_daily_interactions 
                        (user_id, date, snack_mood_total, pet_interact_used, all_meds_taken, bp_completed, bp_bonus_awarded, last_decay_time, med_points_today)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (user_id, today, 0, False, False, False, False, get_now_taiwan(), 0)
                    )
                    cur.execute("SELECT * FROM pet_daily_interactions WHERE user_id = %s AND date = %s", (user_id, today))
                    row = cur.fetchone()
                    conn.commit()
            
            return row

    def add_med_point(self, user_id: int) -> bool:
        """
        增加服藥點數,檢查是否超過每日上限 (20點)
        """
        with self._conn() as conn:
            today = date.today().isoformat()
            
            # 重新取得最新的互動記錄 (避免並發問題)
            interactions = self.get_today_interactions(user_id)
            current_points = interactions.get("med_points_today", 0)
            max_points = 20
            
            if current_points >= max_points:
                return False
                
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE pet_daily_interactions SET med_points_today = med_points_today + 1 WHERE user_id = %s AND date = %s",
                    (user_id, today)
                )
            conn.commit()
            return True

    def add_snack_mood(self, user_id: int, mood_gain: int) -> tuple[bool, int]:
        """
        增加零食心情值,檢查是否超過每日上限
        """
        with self._conn() as conn:
            today = date.today().isoformat()
            from domain.pet_engine import PetEngine
            
            interactions = self.get_today_interactions(user_id)
            current_total = interactions["snack_mood_total"]
            max_mood = PetEngine.MAX_SNACK_MOOD_PER_DAY
            
            # 檢查是否已達上限
            if current_total >= max_mood:
                return False, 0
            
            # 計算實際可增加的心情值 (不超過上限)
            actual_gain = min(mood_gain, max_mood - current_total)
            
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE pet_daily_interactions SET snack_mood_total = snack_mood_total + %s WHERE user_id = %s AND date = %s",
                    (actual_gain, user_id, today)
                )
            conn.commit()
            return True, actual_gain

    def set_toy_used(self, user_id: int, toy_name: str) -> bool:
        """
        設定今日使用的玩具,檢查是否已使用過玩具
        """
        with self._conn() as conn:
            today = date.today().isoformat()
            
            interactions = self.get_today_interactions(user_id)
            
            # 檢查是否已使用過玩具
            if interactions["toy_used"]:
                return False
            
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE pet_daily_interactions SET toy_used = %s WHERE user_id = %s AND date = %s",
                    (toy_name, user_id, today)
                )
            conn.commit()
            return True

    def use_pet_interact(self, user_id: int) -> bool:
        """
        使用寵物互動,檢查是否已使用過
        """
        with self._conn() as conn:
            today = date.today().isoformat()
            
            interactions = self.get_today_interactions(user_id)
            
            # 檢查是否已使用過
            if interactions["pet_interact_used"]:
                return False
            
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE pet_daily_interactions SET pet_interact_used = %s WHERE user_id = %s AND date = %s",
                    (True, user_id, today)
                )
            conn.commit()
            return True

    def mark_all_meds_taken(self, user_id: int) -> None:
        """標記完成所有用藥"""
        with self._conn() as conn:
            today = date.today().isoformat()
            
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE pet_daily_interactions SET all_meds_taken = %s WHERE user_id = %s AND date = %s",
                    (True, user_id, today)
                )
            conn.commit()

    def mark_bp_completed(self, user_id: int) -> bool:
        """
        標記完成血壓測量 (如果尚未完成)
        """
        with self._conn() as conn:
            today = date.today().isoformat()
            
            interactions = self.get_today_interactions(user_id)
            if interactions["bp_completed"]:
                return False
                
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE pet_daily_interactions SET bp_completed = %s WHERE user_id = %s AND date = %s",
                    (True, user_id, today)
                )
            conn.commit()
            return True

    def update_last_decay_time(self, user_id: int, decay_time: Optional[datetime] = None) -> None:
        """
        更新上次心情衰減時間
        """
        with self._conn() as conn:
            today = date.today().isoformat()
            
            if decay_time is None:
                decay_time = get_now_taiwan()
            
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE pet_daily_interactions SET last_decay_time = %s WHERE user_id = %s AND date = %s",
                    (decay_time, user_id, today)
                )
            conn.commit()

    def get_last_decay_time(self, user_id: int) -> Optional[datetime]:
        """
        取得上次心情衰減時間
        """
        interactions = self.get_today_interactions(user_id)
        last_decay = interactions.get("last_decay_time")
        
        if last_decay:
            from domain.utils import to_taiwan_time
            return to_taiwan_time(last_decay)
        return None

    def reset_daily_stats(self, user_id: int) -> None:
        """
        重置每日統計
        """
        with self._conn() as conn:
            today = date.today()
            seven_days_ago = (today - timedelta(days=7)).isoformat()
            
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM pet_daily_interactions WHERE user_id = %s AND date < %s",
                    (user_id, seven_days_ago)
                )
            conn.commit()
