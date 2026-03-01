from __future__ import annotations

import json
from datetime import datetime
from typing import Sequence

from domain.models import DrugItem, IntakePeriod

from .base import BaseRepository


class DrugRepository(BaseRepository):
    def list_active_drugs(self, user_id: int) -> Sequence[DrugItem]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM drugs WHERE user_id = %s AND active = 1", (user_id,))
                rows = cur.fetchall()
        return [self._to_drug(row) for row in rows]

    def list_all_drugs(self, user_id: int) -> Sequence[DrugItem]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM drugs WHERE user_id = %s", (user_id,))
                rows = cur.fetchall()
        return [self._to_drug(row) for row in rows]

    def get_by_id(self, user_id: int, drug_id: int) -> DrugItem | None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM drugs WHERE id = %s AND user_id = %s", (drug_id, user_id))
                row = cur.fetchone()
        return self._to_drug(row) if row else None

    def add_drug(
        self,
        user_id: int,
        *,
        drug_name: str,
        intake_periods: Sequence[str],
        intake_timing: str,
        pills_per_intake: int,
        usage_method: str = "口服",
        hospital: str | None = None,
        doctor: str | None = None,
        department: str | None = None
    ) -> int:
        with self._conn() as conn:
            timestamp = datetime.utcnow()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO drugs (
                        user_id, drug_name, intake_periods, intake_timing, pills_per_intake,
                        usage_method, hospital, doctor, department,
                        active, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s, %s)
                    """,
                    (
                        user_id,
                        drug_name,
                        json.dumps(list(intake_periods)),
                        intake_timing,
                        pills_per_intake,
                        usage_method,
                        hospital,
                        doctor,
                        department,
                        timestamp,
                        timestamp
                    ),
                )
                drug_id = cur._cursor.lastrowid if hasattr(cur, "_cursor") else cur.lastrowid
            conn.commit()
        return drug_id

    def set_active(self, user_id: int, drug_id: int, active: bool) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE drugs SET active = %s, updated_at = %s WHERE id = %s AND user_id = %s",
                    (
                        1 if active else 0,
                        datetime.utcnow(),
                        drug_id,
                        user_id,
                    ),
                )
            conn.commit()

    def update_drug(
        self,
        user_id: int,
        drug_id: int,
        *,
        drug_name: str,
        intake_periods: Sequence[str],
        intake_timing: str,
        pills_per_intake: int,
        usage_method: str = "口服",
        hospital: str | None = None,
        doctor: str | None = None,
        department: str | None = None
    ) -> None:
        with self._conn() as conn:
            timestamp = datetime.utcnow()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE drugs
                    SET drug_name = %s, intake_periods = %s, intake_timing = %s, pills_per_intake = %s,
                        usage_method = %s, hospital = %s, doctor = %s, department = %s,
                        updated_at = %s
                    WHERE id = %s AND user_id = %s
                    """,
                    (
                        drug_name,
                        json.dumps(list(intake_periods)),
                        intake_timing,
                        pills_per_intake,
                        usage_method,
                        hospital,
                        doctor,
                        department,
                        timestamp,
                        drug_id,
                        user_id
                    ),
                )
            conn.commit()


    def init_demo_data(self, user_id: int) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM drugs WHERE user_id = %s", (user_id,))
                count = cur.fetchone()["count"]
        if count == 0:
            print("[DrugRepo] Seeding demo drugs...")
            self.add_drug(
                user_id,
                drug_name="維生素 C",
                intake_periods=["breakfast"],
                intake_timing="after_meal",
                pills_per_intake=1,
                usage_method="口服"
            )
            self.add_drug(
                user_id,
                drug_name="降血壓藥 (Amlodipine)",
                intake_periods=["breakfast", "dinner"],
                intake_timing="after_meal",
                pills_per_intake=1,
                usage_method="口服"
            )
            
    @staticmethod
    def _to_drug(row: dict) -> DrugItem:
        periods = json.loads(row["intake_periods"])
        # Handle potential missing columns if DB isn't migrated yet (fallback)
        try:
            usage = row["usage_method"]
        except IndexError:
            usage = "口服"
            
        try:
            hosp = row["hospital"]
        except IndexError:
            hosp = None
            
        try:
            doc = row["doctor"]
        except IndexError:
            doc = None
            
        try:
            dept = row["department"]
        except IndexError:
            dept = None

        return DrugItem(
            id=row["id"],
            drug_name=row["drug_name"],
            usage_method=usage if usage else "口服",
            intake_timing=row["intake_timing"],
            intake_periods=periods,
            pills_per_intake=row["pills_per_intake"],
            hospital=hosp,
            doctor=doc,
            department=dept,
            active=bool(row["active"]),
        )
