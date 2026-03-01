from __future__ import annotations
from app.container import Container
from domain.shop_engine import ShopEngine
from domain.watcher import pet_watcher

class ShopViewModel:
    def __init__(self, container: Container):
        self.container = container
        self.shop_repo = container.shop_repo
        self.points_repo = container.points_repo
        self.shop_engine = ShopEngine(container)

    def load_shop_data(self) -> dict:
        user = self.container.auth_service.get_current_user()
        if not user:
             # Return default empty/zero data if not logged in (though should be handled by nav guard)
             return {"items": [], "balance": 0}

        items = self.shop_repo.list_active_items()
        balance = self.points_repo.get_balance(user.id)
        
        return {
            "items": [
                {
                    "id": i.id,
                    "name": i.name,
                    "cost": i.cost,
                    "category": i.category,
                    "image_path": i.image_path
                } for i in items
            ],
            "balance": balance
        }

    async def buy_item(self, item_id: int, quantity: int = 1) -> tuple[bool, str]:
        user = self.container.auth_service.get_current_user()
        if not user:
            return False, "請先登入"
        success, message = await self.shop_engine.purchase_item(user.id, item_id, quantity=quantity)
        if success:
            # Notify watchers to refresh home page pet status if needed
            pet_watcher.notify()
        return success, message

    def load_inventory(self) -> list[dict]:
        """Fetch current user's inventory."""
        user = self.container.auth_service.get_current_user()
        if not user:
            return []
        return list(self.shop_repo.get_inventory(user.id))

    async def use_item(self, item_id: int) -> tuple[bool, str, str]:
        """
        使用背包中的物品
        
        Returns:
            (是否成功, 訊息, 物品類別)
        """
        # 取得物品資訊
        item = self.shop_repo.get_item(item_id)
        if not item:
            return False, "物品不存在", ""
        
        # 檢查背包中是否有此物品
        user = self.container.auth_service.get_current_user()
        if not user:
            return False, "請先登入", ""
        inventory = self.shop_repo.get_inventory(user.id)
        has_item = any(inv["item_id"] == item_id and inv["quantity"] > 0 for inv in inventory)
        if not has_item:
            return False, "背包中沒有此物品", ""
        
        # 套用物品效果
        success, message = await self.shop_engine._apply_item_effect(user.id, item)
        
        if success:
            # 扣除背包物品數量
            self.shop_repo.use_from_inventory(user.id, item_id, quantity=1)
            # 通知寵物狀態更新
            pet_watcher.notify()
            return True, message or f"成功使用 {item.name}！", item.category
        else:
            return False, message, ""
