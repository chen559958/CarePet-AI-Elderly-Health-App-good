from app.container import Container
from domain.utils import get_now_taiwan
from datetime import timedelta

def empty_bowl():
    container = Container.get_instance()
    pet_repo = container.pet_repo
    
    # 假設預設 user_id 為 1 (與 dashboard 邏輯一致)
    user_id = 1 
    
    pet = pet_repo.get_pet(user_id)
    if not pet:
        print("找不到寵物資料")
        return

    # 設定體力為 50 (低於 60 會顯示空碗)
    # 並將過期時間設為 1 小時前
    expired_time = get_now_taiwan() - timedelta(hours=1)
    
    pet_repo.update_pet(
        user_id,
        mood=pet.mood,
        stamina=50,
        bowl_expires_at=expired_time
    )
    print(f"寵物 {pet.pet_name} 的飼料盆已清空！(Stamina: 50, 已過期)")

if __name__ == "__main__":
    empty_bowl()
