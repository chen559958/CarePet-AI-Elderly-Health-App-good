from __future__ import annotations

import hashlib
import json
from pathlib import Path
from domain.models import User
from data.repositories.auth_repo import AuthRepository


AUTH_STATE_FILE = Path("data/auth_state.json")


class AuthService:
    """Service for handling authentication logic."""
    
    def __init__(self, auth_repo: AuthRepository):
        self.auth_repo = auth_repo
        self._current_user: User | None = None

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def register(self, phone: str, password: str) -> tuple[bool, str]:
        """
        Register a new user.
        Returns (success, message).
        """
        # Validate phone format (simple validation)
        if not phone or len(phone) < 10:
            return False, "手機號碼格式不正確"
        
        # Check if user already exists
        existing_user = self.auth_repo.get_user_by_phone(phone)
        if existing_user:
            return False, "此手機號碼已註冊"
        
        # Validate password
        if not password or len(password) < 6:
            return False, "密碼至少需要 6 個字元"
        
        # Create user
        password_hash = self.hash_password(password)
        user_id = self.auth_repo.create_user(phone, password_hash)
        
        if user_id:
            # Auto-login after registration
            user = self.auth_repo.get_user_by_id(user_id)
            if user:
                self._save_auth_state(user)
                self._current_user = user
                return True, "註冊成功"
        
        return False, "註冊失敗，請稍後再試"

    def login(self, phone: str, password: str) -> tuple[bool, str]:
        """
        Login user.
        Returns (success, message).
        """
        user = self.auth_repo.get_user_by_phone(phone)
        
        if not user:
            return False, "手機號碼或密碼錯誤"
        
        # Verify password
        password_hash = self.hash_password(password)
        if user.password_hash != password_hash:
            return False, "手機號碼或密碼錯誤"
        
        # Update last login
        self.auth_repo.update_last_login(user.id)
        
        # Save auth state
        self._save_auth_state(user)
        self._current_user = user
        
        return True, "登入成功"

    def reset_password(self, phone: str, new_password: str) -> tuple[bool, str]:
        """Reset user's password (simulated flow)."""
        if not new_password or len(new_password) < 6:
            return False, "新密碼至少需要 6 個字元"
        
        # Check if user exists
        user = self.auth_repo.get_user_by_phone(phone)
        if not user:
            return False, "找不到此手機號碼相關的帳號"
            
        password_hash = self.hash_password(new_password)
        success = self.auth_repo.update_password(phone, password_hash)
        
        if success:
            # Auto-login after reset
            updated_user = self.auth_repo.get_user_by_phone(phone)
            if updated_user:
                self._save_auth_state(updated_user)
                self._current_user = updated_user
                return True, "密碼重設成功並已自動登入"
        
        return False, "密碼重設失敗，請稍後再試"

    def logout(self) -> None:
        """Logout current user."""
        self._clear_auth_state()
        self._current_user = None

    def get_current_user(self) -> User | None:
        """Get current logged-in user."""
        return self._current_user

    def is_logged_in(self) -> bool:
        """Check if user is logged in."""
        return self._current_user is not None

    def restore_session(self) -> bool:
        """
        Restore login session from saved state.
        Returns True if session was restored successfully.
        """
        if not AUTH_STATE_FILE.exists():
            return False
        
        try:
            with AUTH_STATE_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            
            user_id = data.get("user_id")
            if not user_id:
                return False
            
            user = self.auth_repo.get_user_by_id(user_id)
            if user:
                self._current_user = user
                return True
            
        except (json.JSONDecodeError, KeyError, IOError):
            pass
        
        return False

    def _save_auth_state(self, user: User) -> None:
        """Save authentication state to file."""
        AUTH_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "user_id": user.id,
            "phone": user.phone
        }
        
        with AUTH_STATE_FILE.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _clear_auth_state(self) -> None:
        """Clear authentication state file."""
        if AUTH_STATE_FILE.exists():
            AUTH_STATE_FILE.unlink()
