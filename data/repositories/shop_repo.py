import json
from datetime import datetime
from typing import Sequence, Optional
from dataclasses import dataclass
from .base import BaseRepository

@dataclass
class ShopItem:
    id: int
    category: str
    name: str
    cost: int
    stock: int
    effect_json: str
    active: bool
    image_path: Optional[str] = None

class ShopRepository(BaseRepository):
    def list_active_items(self) -> Sequence[ShopItem]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM shop_items WHERE active = 1")
                rows = cur.fetchall()
            
            # Fallback Init for SQLite or fresh DB if empty
            if not rows:
                self.init_demo_shop()
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM shop_items WHERE active = 1")
                    rows = cur.fetchall()

        return [self._to_item(row) for row in rows]

    def get_item(self, item_id: int) -> Optional[ShopItem]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM shop_items WHERE id = %s", (item_id,))
                row = cur.fetchone()
        return self._to_item(row) if row else None

    def add_to_inventory(self, user_id: int, item_id: int, quantity: int = 1) -> None:
        with self._conn() as conn:
            now = datetime.utcnow()
            with conn.cursor() as cur:
                # Check if already exists
                cur.execute("SELECT id, quantity FROM user_inventory WHERE user_id = %s AND item_id = %s", (user_id, item_id))
                exists = cur.fetchone()
                if exists:
                    cur.execute(
                        "UPDATE user_inventory SET quantity = quantity + %s, updated_at = %s WHERE user_id = %s AND item_id = %s",
                        (quantity, now, user_id, item_id)
                    )
                else:
                    cur.execute(
                        "INSERT INTO user_inventory (user_id, item_id, quantity, updated_at) VALUES (%s, %s, %s, %s)",
                        (user_id, item_id, quantity, now)
                    )
            conn.commit()

    def get_inventory(self, user_id: int) -> Sequence[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT i.item_id, i.quantity, s.name, s.category, s.effect_json, s.image_path
                    FROM user_inventory i
                    JOIN shop_items s ON i.item_id = s.id
                    WHERE i.user_id = %s AND i.quantity > 0
                """, (user_id,))
                return cur.fetchall()

    def consume_item(self, user_id: int, item_id: int, quantity: int = 1) -> bool:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT quantity FROM user_inventory WHERE user_id = %s AND item_id = %s", (user_id, item_id))
                row = cur.fetchone()
                if not row or row["quantity"] < quantity:
                    return False
                cur.execute(
                    "UPDATE user_inventory SET quantity = quantity - %s, updated_at = %s WHERE user_id = %s AND item_id = %s",
                    (quantity, datetime.utcnow(), user_id, item_id)
                )
            conn.commit()
            return True

    def use_from_inventory(self, user_id: int, item_id: int, quantity: int = 1) -> bool:
        """使用背包中的物品（consume_item 的別名）"""
        return self.consume_item(user_id, item_id, quantity)

    def init_demo_shop(self) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                # 預設商品列表
                items = [
                    ("foods", "普通飼料", 20, json.dumps({"mood": 10}), "assets/shop/Regular_feed.png"),
                    ("foods", "高級飼料", 60, json.dumps({"mood": 20}), "assets/shop/Advanced_feed.png"),                    
                    ("snacks", "糖果", 8, json.dumps({"mood": 2}), "assets/shop/candy.png"),
                    ("snacks", "飲料", 13, json.dumps({"mood": 5}), "assets/shop/drink.png"),
                    ("snacks", "餅乾", 20, json.dumps({"mood": 8}), "assets/shop/cookie.png"),
                    ("Props", "門票", 100, json.dumps({"state": "Normal"}), "assets/shop/ticket.png"),
                    ("toys", "小球", 10, json.dumps({"mood": 5}), "assets/shop/ball.png"),
                    ("toys", "風車", 10, json.dumps({"mood": 5}), "assets/shop/pinwheel.png"),
                    ("toys", "遊戲機", 20, json.dumps({"mood": 10}), "assets/shop/game_console.png"),
                ]

                for cat, name, cost, effect, img in items:
                    # 檢查商品是否存在 (避免重複新增)
                    cur.execute("SELECT id FROM shop_items WHERE name = %s", (name,))
                    if not cur.fetchone():
                        cur.execute(
                            "INSERT INTO shop_items (category, name, cost, effect_json, image_path, active) VALUES (%s, %s, %s, %s, %s, true)",
                            (cat, name, cost, effect, img)
                        )
            conn.commit()

    @staticmethod
    def _to_item(row: dict) -> ShopItem:
        return ShopItem(
            id=row["id"],
            category=row["category"],
            name=row["name"],
            cost=row["cost"],
            stock=row["stock"],
            effect_json=row["effect_json"],
            active=bool(row["active"]),
            image_path=row["image_path"] if "image_path" in row.keys() else None
        )
