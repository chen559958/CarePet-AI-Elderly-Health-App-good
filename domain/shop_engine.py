from __future__ import annotations
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.container import Container
from domain.pet_engine import PetEngine


class ShopEngine:
    def __init__(self, container: Container):
        self.container = container
        self.points_repo = container.points_repo
        self.shop_repo = container.shop_repo
        self.pet_repo = container.pet_repo
        self.pet_interaction_repo = container.pet_interaction_repo

    async def purchase_item(self, user_id: int, item_id: int, quantity: int = 1) -> tuple[bool, str]:
        """
        處理商店商品購買邏輯
        
        Returns:
            (是否成功, 訊息)
        """
        item = self.shop_repo.get_item(item_id)
        if not item:
            return False, "商品不存在"

        total_cost = item.cost * quantity
        current_balance = self.points_repo.get_balance(user_id)
        if current_balance < total_cost:
            return False, f"點數不足 (尚需 {total_cost - current_balance} 點)"

        try:
            # 1. 扣除點數
            self.points_repo.add_ledger(
                user_id=user_id,
                delta=-total_cost,
                reason=f"購買商品: {item.name} x{quantity}",
                ref_type="shop_purchase",
                ref_id=item.id
            )
            
            # 2. 加入庫存
            self.shop_repo.add_to_inventory(user_id, item_id, quantity=quantity)
            
            # 3. 自動使用商品 (套用效果)
            success_count = 0
            messages = []
            
            for i in range(quantity):
                success, msg = await self._apply_item_effect(user_id, item)
                if success:
                    success_count += 1
                if msg and i == 0:  # 只顯示第一次的訊息
                    messages.append(msg)
            
            if success_count == 0:
                return False, messages[0] if messages else "無法使用商品"
            elif success_count < quantity:
                return True, f"成功使用了 {success_count}/{quantity} 個{item.name}。{messages[0] if messages else ''}"
            else:
                return True, f"成功購買並使用了 {quantity} 個{item.name}!"
                
        except Exception as e:
            print(f"ShopEngine Error: {e}")
            import traceback
            traceback.print_exc()
            return False, "交易處理失敗"

    async def _apply_item_effect(self, user_id: int, item) -> tuple[bool, str]:
        """
        套用商品效果到寵物
        
        Returns:
            (是否成功, 訊息)
        """
        try:
            effects = json.loads(item.effect_json)
            pet = await self.pet_repo.get_pet(user_id)
            if not pet:
                return False, "找不到寵物"

            item_type = effects.get("type", "")
            category = item.category.lower()
            
            # 處理門票特殊邏輯 (從旅遊回家)
            if item.name == "門票" or effects.get("state") == "Normal":
                if pet.state == "Traveling":
                    # 使用 PetEngine 處理旅遊回家
                    new_pet = PetEngine.handle_travel_return(pet)
                    await self.pet_repo.update_pet(
                        user_id=user_id,
                        mood=new_pet.mood,
                        stamina=new_pet.stamina,
                        state=new_pet.state
                    )
                    return True, f"{pet.pet_name}回家了!心情恢復到 {new_pet.mood}"
                else:
                    return False, f"{pet.pet_name}沒有在旅遊,不需要門票"
            
            # 處理零食類
            if category == "snacks":
                # 先用 PetEngine 計算心情增加值
                new_pet, mood_gain = PetEngine.apply_food_effect(pet, item_type)
                
                # 直接更新寵物狀態
                await self.pet_repo.update_pet(
                    user_id=user_id,
                    mood=new_pet.mood,
                    stamina=new_pet.stamina,
                    state=new_pet.state
                )
                # 零食也給經驗值
                await self.pet_repo.add_exp(user_id, PetEngine.EXP_FEED)
                return True, ""
            
            # 處理玩具類
            elif category == "toys":
                # 使用 PetEngine 計算心情變化
                new_pet = PetEngine.apply_toy_effect(pet, item_type)
                await self.pet_repo.update_pet(
                    user_id=user_id,
                    mood=new_pet.mood,
                    stamina=new_pet.stamina,
                    state=new_pet.state
                )
                # 玩具給經驗值
                await self.pet_repo.add_exp(user_id, PetEngine.EXP_TOY)
                return True, ""
            
            # 處理食物類
            elif category == "foods":
                # 使用 PetEngine 計算心情變化
                new_pet, _ = PetEngine.apply_food_effect(pet, item_type)
                from datetime import timedelta
                from domain.utils import get_now_taiwan
                await self.pet_repo.update_pet(
                    user_id=user_id,
                    mood=new_pet.mood,
                    stamina=60, # 填滿飼料盆
                    state=new_pet.state,
                    bowl_expires_at=get_now_taiwan() + timedelta(minutes=5)
                )
                # 餵食獎勵經驗值
                await self.pet_repo.add_exp(user_id, PetEngine.EXP_FEED)
                return True, ""
            
            else:
                # 其他類型 - 不應該出現,但保留容錯
                print(f"WARNING: Unknown item category: {category}")
                return False, "未知的商品類型"
                
        except Exception as e:
            print(f"Error applying effect: {e}")
            import traceback
            traceback.print_exc()
            return False, f"套用效果失敗: {e}"
