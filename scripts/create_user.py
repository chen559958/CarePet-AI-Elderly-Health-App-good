import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from data.database import connect
from data.repositories.auth_repo import AuthRepository
from domain.services.auth_service import AuthService

def main():
    print("=== Create User ===")
    try:
        phone = input("請輸入手機號碼: ").strip()
        if not phone:
            print("❌ 手機號碼不能為空")
            return

        password = input("請輸入密碼: ").strip()
        if not password:
            print("❌ 密碼不能為空")
            return

        print(f"正在建立使用者 {phone}...")
        
        # Initialize service
        repo = AuthRepository(connect)
        service = AuthService(repo)

        # Register
        success, message = service.register(phone, password)
        
        if success:
            print(f"✅ 使用者建立成功！")
            print(f"手機: {phone}")
            
            # Verify user exists in DB
            user = service.auth_repo.get_user_by_phone(phone)
            if user:
                print(f"ID: {user.id}")
                print(f"Password Hash: {user.password_hash[:10]}...")
        else:
            print(f"❌ 建立失敗: {message}")
            
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
