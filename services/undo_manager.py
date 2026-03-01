from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Protocol


class UndoRepository(Protocol):
    def insert(self, user_id: int, action_key: str, expires_at: datetime, payload_json: str) -> None: ...
    def get(self, user_id: int, action_key: str) -> dict | None: ...
    def delete(self, user_id: int, action_key: str) -> None: ...


RollbackFn = Callable[[dict], None]


@dataclass
class UndoManager:
    repo: UndoRepository

    def create_action(self, user_id: int, payload: dict, ttl_seconds: int = 5) -> str:
        action_key = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        self.repo.insert(user_id, action_key, expires_at, json.dumps(payload))
        return action_key

    def rollback(self, user_id: int, action_key: str, rollback_fn: RollbackFn) -> bool:
        record = self.repo.get(user_id, action_key)
        if not record:
            return False
        expires_at = datetime.fromisoformat(record["expires_at"])
        if datetime.utcnow() > expires_at:
            self.repo.delete(user_id, action_key)
            return False
        payload = json.loads(record["payload_json"])
        rollback_fn(payload)
        self.repo.delete(user_id, action_key)
        return True
