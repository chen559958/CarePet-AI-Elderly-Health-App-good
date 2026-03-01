from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
from data.database import get_or_init_connection, RealDictConnection

from data.database import get_or_init_connection, RealDictConnection, get_async_pool
from data.repositories.drug_repo import DrugRepository
from data.repositories.log_repo import LogRepository
from data.repositories.pet_repo import PetRepository
from data.repositories.points_repo import PointsRepository
from data.repositories.reminder_repo import ReminderRepository
from data.repositories.undo_repo import UndoRepository
from data.repositories.user_repo import UserRepository
from data.repositories.shop_repo import ShopRepository
from data.repositories.blood_pressure_repo import BloodPressureRepository
from data.repositories.auth_repo import AuthRepository
from data.repositories.pet_interaction_repo import PetInteractionRepository
from services.haptics_service import HapticsService
from services.notification_service import LocalNotificationService
from services.caregiver_service import CaregiverService
from services.undo_manager import UndoManager
from domain.services.auth_service import AuthService
from domain.shop_engine import ShopEngine


def _conn_factory() -> RealDictConnection:
    return get_or_init_connection()


@dataclass
class Container:
    user_repo: UserRepository
    drug_repo: DrugRepository
    reminder_repo: ReminderRepository
    log_repo: LogRepository
    points_repo: PointsRepository
    pet_repo: PetRepository
    undo_repo: UndoRepository
    shop_repo: ShopRepository
    bp_repo: BloodPressureRepository
    auth_repo: AuthRepository
    pet_interaction_repo: PetInteractionRepository
    notification_service: LocalNotificationService
    haptics_service: HapticsService
    caregiver_service: CaregiverService
    undo_manager: UndoManager
    auth_service: AuthService
    shop_engine: ShopEngine


    _instance: "Container" | None = None

    @classmethod
    def get_instance(cls) -> "Container":
        if cls._instance is None:
            cls._instance = cls.build()
        return cls._instance

    @classmethod
    def build(cls) -> "Container":
        conn_factory: Callable[[], RealDictConnection] = _conn_factory
        user_repo = UserRepository(conn_factory)
        
        pet_repo = PetRepository(conn_factory)
        container = cls(
            user_repo=user_repo,
            drug_repo=DrugRepository(conn_factory),
            reminder_repo=ReminderRepository(conn_factory),
            log_repo=LogRepository(conn_factory),
            points_repo=PointsRepository(conn_factory),
            pet_repo=pet_repo,
            undo_repo=UndoRepository(conn_factory),
            shop_repo=ShopRepository(conn_factory),
            bp_repo=BloodPressureRepository(conn_factory),
            auth_repo=AuthRepository(conn_factory),
            pet_interaction_repo=PetInteractionRepository(conn_factory),
            notification_service=LocalNotificationService(backend=_NoopNotificationBackend()),
            haptics_service=HapticsService(),
            caregiver_service=CaregiverService(None), # Placeholder, will set below
            undo_manager=UndoManager(UndoRepository(conn_factory)),
            auth_service=None,  # Placeholder, will set below
            shop_engine=None,   # Placeholder, will set below
        )

        container.auth_service = AuthService(container.auth_repo)
        container.shop_engine = ShopEngine(container)
        container.caregiver_service.container = container # Fix circular
        # init_demo_shop removed from here to prevent blocking build()
        return container



class _NoopNotificationBackend:
    def __init__(self):
        self.on_notify = None

    def schedule(self, notification_id, when, title, body):
        print(f"[notification noop] schedule {notification_id} at {when} {title}")
        if self.on_notify:
            self.on_notify(title, body)

    def cancel(self, notification_id):
        print(f"[notification noop] cancel {notification_id}")
