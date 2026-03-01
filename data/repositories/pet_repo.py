from __future__ import annotations
from datetime import datetime, timedelta
from typing import Any
from domain.utils import get_now_taiwan, to_taiwan_time

from domain.models import PetState

# Remove BaseRepository inheritance or keep it but override everything
# User's example showed only __init__ and get_pet.
# We will drop BaseRepository inheritance to avoid confusion, as strictly requested.

import asyncio
from typing import Callable
from data.database import RealDictConnection

class PetRepository:
    def __init__(self, conn_factory: Callable[[], RealDictConnection]):
        self._conn = conn_factory

    def _strip_tz(self, dt: Any) -> Any:
        """Strip timezone from datetime for naive TIMESTAMP columns if it has one."""
        if isinstance(dt, datetime) and dt.tzinfo is not None:
            return dt.replace(tzinfo=None)
        return dt

    def _get_pet_sync(self, user_id: int) -> PetState | None:
        print(f"DEBUG: PetRepository: _get_pet_sync ENTER for user {user_id}")
        with self._conn() as conn:
            print(f"DEBUG: PetRepository: _get_pet_sync obtained connection for user {user_id}")
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM pets WHERE user_id=%s LIMIT 1", (user_id,))
                row = cur.fetchone()
                print(f"DEBUG: PetRepository: _get_pet_sync query finished for user {user_id}")
                if not row:
                    return None
                return self._to_state(row)

    async def get_pet(self, user_id: int) -> PetState | None:
        print(f"DEBUG: PetRepository: Getting pet for user {user_id} (Sync Fallback)...")
        return await asyncio.to_thread(self._get_pet_sync, user_id)

    def _create_pet_sync(self, user_id: int, name: str, image_path: str) -> PetState | None:
        now = self._strip_tz(get_now_taiwan())
        bowl_expires_at = self._strip_tz(get_now_taiwan() + timedelta(minutes=5))
        
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO pets (user_id, pet_name, level, exp, mood, stamina, state, bowl_expires_at, image_path, created_at, updated_at)
                    VALUES (%s, %s, 1, 0, 60, 60, 'normal', %s, %s, %s, %s)
                    """,
                    (user_id, name, bowl_expires_at, image_path, now, now)
                )
            conn.commit()
        return self._get_pet_sync(user_id)

    async def create_pet(self, user_id: int, name: str, image_path: str = "assets/pet.png") -> PetState | None:
        return await asyncio.to_thread(self._create_pet_sync, user_id, name, image_path)

    async def init_default_pet_if_empty(self, user_id: int) -> PetState | None:
        pet = await self.get_pet(user_id)
        if pet:
            return pet
        return await self.create_pet(user_id, "波樂")

    def _update_pet_sync(self, user_id: int, updates_dict: dict) -> None:
        if not updates_dict:
            return
            
        updates = []
        params = []
        
        for key, value in updates_dict.items():
            updates.append(f"{key} = %s")
            if key == "bowl_expires_at" and value is not None:
                params.append(self._strip_tz(value))
            elif isinstance(value, datetime):
                params.append(self._strip_tz(value))
            else:
                params.append(value)
            
        # Add updated_at automatically if not provided
        if "updated_at" not in updates_dict:
            updates.append("updated_at = %s")
            params.append(self._strip_tz(get_now_taiwan()))
        
        params.append(user_id)
        
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE pets SET {', '.join(updates)} WHERE user_id = %s",
                    tuple(params)
                )
            conn.commit()

    async def update_pet(self, user_id: int, **kwargs) -> None:
        await asyncio.to_thread(self._update_pet_sync, user_id, kwargs)

    def _graduate_pet_sync(self, user_id: int, pet: PetState, new_name: str, new_image_path: str) -> PetState | None:
        now = self._strip_tz(get_now_taiwan())
        import os
        filename = os.path.basename(pet.image_path or "assets/pet.png")
        pet_type = filename.split('.')[0].replace("pet_", "")
        if pet_type == "pet": pet_type = "default"

        with self._conn() as conn:
            with conn.cursor() as cur:
                # 1. Archive
                cur.execute(
                    """
                    INSERT INTO pet_collection (user_id, pet_name, pet_type, image_path, final_level, graduated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (user_id, pet.pet_name, pet_type, pet.image_path or "assets/pet.png", pet.level, now)
                )
                # 2. Reincarnate
                cur.execute(
                    """
                    UPDATE pets
                    SET pet_name = %s, level = 1, exp = 0, mood = 60, stamina = 60, state = 'Normal', 
                        image_path = %s, updated_at = %s
                    WHERE user_id = %s
                    """,
                    (new_name, new_image_path, now, user_id)
                )
            conn.commit()
        return self._get_pet_sync(user_id)

    async def graduate_pet(self, user_id: int, pet: PetState, new_name: str, new_image_path: str) -> PetState | None:
        return await asyncio.to_thread(self._graduate_pet_sync, user_id, pet, new_name, new_image_path)

    async def add_exp(self, user_id: int, amount: int) -> None:
        pet = await self.get_pet(user_id)
        if not pet:
            return
        from domain.level_engine import LevelEngine
        total_exp = pet.exp + amount
        new_level, remaining_exp = LevelEngine.calculate_level(pet.level, total_exp)
        await self.update_pet(user_id, mood=pet.mood, stamina=pet.stamina, level=new_level, exp=remaining_exp)

    def _list_pet_collection_sync(self, user_id: int) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM pet_collection WHERE user_id = %s", (user_id,))
                return cur.fetchall()

    async def list_pet_collection(self, user_id: int) -> list[dict]:
        return await asyncio.to_thread(self._list_pet_collection_sync, user_id)

    def _get_daily_stats_sync(self, user_id: int) -> dict | None:
        today = datetime.now().date()
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM pet_daily_interactions WHERE user_id = %s AND date = %s", (user_id, str(today)))
                row = cur.fetchone()
                if not row:
                    cur.execute("INSERT INTO pet_daily_interactions (user_id, date) VALUES (%s, %s)", (user_id, str(today)))
                    conn.commit()
                    cur.execute("SELECT * FROM pet_daily_interactions WHERE user_id = %s AND date = %s", (user_id, str(today)))
                    row = cur.fetchone()
                return dict(row) if row else None

    async def get_daily_stats(self, user_id: int) -> dict | None:
        return await asyncio.to_thread(self._get_daily_stats_sync, user_id)

    def _update_daily_stats_sync(self, user_id: int, **kwargs) -> None:
        today = datetime.now().date()
        updates = [f"{k} = %s" for k in kwargs.keys()]
        params = list(kwargs.values())
        params = [self._strip_tz(p) if isinstance(p, datetime) else p for p in params]
        params.append(user_id)
        params.append(str(today))
        
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE pet_daily_interactions SET {', '.join(updates)} WHERE user_id = %s AND date = %s", 
                    tuple(params)
                )
            conn.commit()

    async def update_daily_stats(self, user_id: int, **kwargs) -> None:
        await asyncio.to_thread(self._update_daily_stats_sync, user_id, **kwargs)

    @staticmethod
    def _to_state(row: Any) -> PetState:
        return PetState(
            id=row["id"],
            pet_name=row["pet_name"],
            level=row["level"],
            mood=row["mood"],
            stamina=row["stamina"],
            state=row["state"],
            exp=row["exp"],
            bowl_expires_at=to_taiwan_time(row["bowl_expires_at"]) if row.get("bowl_expires_at") else None,
            image_path=row.get("image_path") or "assets/pet.png"
        )

