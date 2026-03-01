import os
import sys

# 將當前目錄加入 path
sys.path.append(os.getcwd())

from app.container import Container

def update_user_name():
    container = Container.get_instance()
    auth_repo = container.auth_repo
    user_repo = container.user_repo
    
    phone = "0981123456"
    new_name = "李"
    
    print(f"正在搜尋用戶: {phone}...")
    user = auth_repo.get_user_by_phone(phone)
    
    if not user:
        print(f"錯誤: 找不到電話為 {phone} 的用戶")
        return
    
    print(f"找到用戶 ID: {user.id}。正在獲取個人資料...")
    profile = user_repo.get_profile(user.id)
    
    if not profile:
        print(f"錯誤: 找不到用戶 ID {user.id} 的個人資料")
        return
    
    old_name = profile.name
    print(f"當前名稱為: {old_name}。正在更新為: {new_name}...")
    
    profile.name = new_name
    user_repo.update_profile(user.id, profile)
    
    print(f"成功! 用戶 {phone} 的名稱已從 「{old_name}」 更新為 「{new_name}」。")

if __name__ == "__main__":
    update_user_name()
