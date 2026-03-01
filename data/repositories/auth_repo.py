from __future__ import annotations

from datetime import datetime
from domain.models import User
from .base import BaseRepository


class AuthRepository(BaseRepository):
    """Repository for authentication-related database operations."""
    
    def create_user(self, phone: str, password_hash: str) -> int:
        """Create a new user and return the user ID."""
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (phone, password_hash) VALUES (%s, %s)",
                    (phone, password_hash)
                )
                user_id = cur._cursor.lastrowid if hasattr(cur, "_cursor") else cur.lastrowid
            conn.commit()
        return user_id

    def get_user_by_phone(self, phone: str) -> User | None:
        """Get user by phone number."""
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, phone, password_hash, created_at, last_login FROM users WHERE phone = %s",
                    (phone,)
                )
                row = cur.fetchone()
        
        if not row:
            return None
        
        return User(
            id=row["id"],
            phone=row["phone"],
            password_hash=row["password_hash"],
            created_at=row["created_at"],
            last_login=row["last_login"]
        )

    def get_user_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, phone, password_hash, created_at, last_login FROM users WHERE id = %s",
                    (user_id,)
                )
                row = cur.fetchone()
        
        if not row:
            return None
        
        return User(
            id=row["id"],
            phone=row["phone"],
            password_hash=row["password_hash"],
            created_at=row["created_at"],
            last_login=row["last_login"]
        )

    def update_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp."""
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
                    (user_id,)
                )
            conn.commit()

    def update_password(self, phone: str, password_hash: str) -> bool:
        """Update user's password hash."""
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET password_hash = %s WHERE phone = %s",
                    (password_hash, phone)
                )
                affected = cur.rowcount
            conn.commit()
        return affected > 0
