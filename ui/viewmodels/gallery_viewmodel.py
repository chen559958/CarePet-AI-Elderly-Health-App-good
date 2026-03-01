from __future__ import annotations
from app.container import Container

class GalleryViewModel:
    def __init__(self, container: Container):
        self.container = container
        self.pet_repo = container.pet_repo

    ALL_PET_TYPES = [
        {"type": "pet", "default_name": "波樂", "image": "assets/pet.png"},
        {"type": "cat", "default_name": "貓咪", "image": "assets/gallery/pet_cat.png"},
        {"type": "dog", "default_name": "狗狗", "image": "assets/gallery/pet_dog.png"},
        {"type": "duck", "default_name": "小鴨", "image": "assets/gallery/pet_duck.png"},
        {"type": "squirrel", "default_name": "松鼠", "image": "assets/gallery/pet_squirrel.png"},
    ]

    async def load_gallery_items(self) -> list[dict]:
        """
        Load graduated pets history and merge with all possible types.
        """
        user = self.container.auth_service.get_current_user()
        if not user:
             return []

        rows = await self.pet_repo.list_pet_collection(user.id)
        
        
        # 建立已收集對照表
        collection_map = {row["pet_type"]: row for row in rows}
        
        gallery = []
        for pet_def in self.ALL_PET_TYPES:
            ptype = pet_def["type"]
            if ptype in collection_map:
                row = collection_map[ptype]
                grad_date = row["graduated_at"]
                if hasattr(grad_date, "strftime"):
                    grad_date = grad_date.strftime("%Y-%m-%d")
                
                gallery.append({
                    "id": row["id"],
                    "name": row["pet_name"],
                    "type": ptype,
                    "image_path": row["image_path"],
                    "final_level": row["final_level"],
                    "graduated_at": grad_date,
                    "is_unlocked": True
                })
            else:
                gallery.append({
                    "id": None,
                    "name": pet_def["default_name"],
                    "type": ptype,
                    "image_path": pet_def["image"],
                    "final_level": 0,
                    "graduated_at": "未收集",
                    "is_unlocked": False
                })
            
        # 排序：解鎖項目在前
        gallery.sort(key=lambda x: x["is_unlocked"], reverse=True)
            
        return gallery
