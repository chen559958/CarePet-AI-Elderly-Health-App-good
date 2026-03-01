from __future__ import annotations
from domain.models import PetState

class PetEngine:
    """
    寵物引擎:根據用藥行為和互動計算寵物狀態變化
    負責處理寵物的心情值和狀態更新
    """
    
    # === 心情系統常數 ===
    INITIAL_MOOD = 60            # 心情初始值
    
    # 心情特效閾值
    MOOD_HAPPY_THRESHOLD = 90    # 愛心特效
    MOOD_SAD_THRESHOLD = 30      # 哭泣表情
    MOOD_TRAVEL_THRESHOLD = 0    # 出去旅遊
    
    # 餵食獎勵
    MOOD_REGULAR_FOOD = 10       # 普通飼料
    MOOD_PREMIUM_FOOD = 20       # 高級飼料
    MOOD_CANDY = 2               # 糖果
    MOOD_DRINK = 5               # 飲料
    MOOD_COOKIE = 8              # 餅乾
    
    # 玩具獎勵
    MOOD_TOY_BALL = 5            # 小球
    MOOD_TOY_PINWHEEL = 5        # 風車
    MOOD_TOY_GAME = 10           # 遊戲機
    
    # 互動與任務獎勵
    MOOD_PET_INTERACT = 5        # 點擊寵物互動
    MOOD_ALL_MEDS = 10           # 完成所有用藥
    MOOD_BP_TASK = 5             # 完成血壓測量
    
    # 每日上限
    MAX_SNACK_MOOD_PER_DAY = 10  # 零食每日心情上限 (總共只能增加 10 點)
    MAX_PET_INTERACT_COUNT = 1   # 寵物互動每日上限 (只能互動 1 次)
    
    # 時間衰減
    DECAY_INTERVAL_HOURS = 4     # 每 4 小時衰減一次
    DECAY_HIGH_MOOD = 5          # 心情 > 30 時的衰減值
    DECAY_LOW_MOOD = 2           # 心情 <= 30 時的衰減值
    MAX_DECAY_PER_DAY = 25       # 24 小時內最多扣 25 心情
    
    # 隨機轉生池 (不包含初始寵物)
    PET_IMAGES = [
        "assets/gallery/pet_cat.png",
        "assets/gallery/pet_dog.png",
        "assets/gallery/pet_duck.png",
        "assets/gallery/pet_squirrel.png"
    ]
    # 初始寵物圖片
    DEFAULT_PET_IMAGE = "assets/pet.png"  

    # === 經驗值系統常數 ===
    EXP_TAKE_MED = 2             # 每次服藥 (以時段計)
    EXP_BLOOD_PRESSURE = 10      # 量血壓
    EXP_TOY = 1                  # 使用玩具
    EXP_INTERACT = 1             # 寵物互動 (每日上限 1 EXP)
    EXP_FEED = 1                 # 餵食
    
    MAX_VAL = 100  # 心情最大值
    MIN_VAL = 0    # 心情最小值

    @staticmethod
    def get_random_pet_image() -> str:
        """Return a random pet image path from the available gallery images."""
        import random
        return random.choice(PetEngine.PET_IMAGES)

    @staticmethod
    def check_graduation(pet: PetState) -> bool:
        """Check if the pet meets graduation requirements (Level >= 12)."""
        return pet.level >= 12

    @classmethod
    def determine_state(cls, mood: int) -> str:
        """
        根據心情值決定寵物狀態
        
        Args:
            mood: 當前心情值
            
        Returns:
            寵物狀態字串
        """
        if mood == cls.MOOD_TRAVEL_THRESHOLD:
            return "Traveling"  # 旅遊中
        elif mood >= cls.MOOD_HAPPY_THRESHOLD:
            return "Happy"      # 開心 (愛心特效)
        elif mood <= cls.MOOD_SAD_THRESHOLD:
            return "Sad"        # 難過 (哭泣表情)
        else:
            return "Normal"     # 正常

    @classmethod
    def apply_food_effect(cls, pet: PetState, food_type: str) -> tuple[PetState, int]:
        """
        套用餵食效果到寵物狀態
        
        Args:
            pet: 當前的寵物狀態
            food_type: 食物類型 (regular_food, premium_food, candy, drink, cookie)
            
        Returns:
            (更新後的寵物狀態, 增加的心情值)
        """
        # 根據食物類型決定心情增加值
        mood_gain_map = {
            "regular_food": cls.MOOD_REGULAR_FOOD,
            "premium_food": cls.MOOD_PREMIUM_FOOD,
            "candy": cls.MOOD_CANDY,
            "drink": cls.MOOD_DRINK,
            "cookie": cls.MOOD_COOKIE,
        }
        
        mood_gain = mood_gain_map.get(food_type, 0)
        new_mood = min(cls.MAX_VAL, pet.mood + mood_gain)
        new_state = cls.determine_state(new_mood)
        
        return PetState(
            id=pet.id,
            pet_name=pet.pet_name,
            level=pet.level,
            exp=pet.exp,
            mood=new_mood,
            stamina=pet.stamina,
            state=new_state,
            bowl_expires_at=pet.bowl_expires_at,
            image_path=pet.image_path
        ), mood_gain

    @classmethod
    def apply_toy_effect(cls, pet: PetState, toy_type: str) -> PetState:
        """
        套用玩具效果到寵物狀態
        
        Args:
            pet: 當前的寵物狀態
            toy_type: 玩具類型 (ball, pinwheel, game)
            
        Returns:
            更新後的寵物狀態
        """
        mood_gain_map = {
            "ball": cls.MOOD_TOY_BALL,
            "pinwheel": cls.MOOD_TOY_PINWHEEL,
            "game": cls.MOOD_TOY_GAME,
        }
        
        mood_gain = mood_gain_map.get(toy_type, 0)
        new_mood = min(cls.MAX_VAL, pet.mood + mood_gain)
        new_state = cls.determine_state(new_mood)
        
        return PetState(
            id=pet.id,
            pet_name=pet.pet_name,
            level=pet.level,
            exp=pet.exp,
            mood=new_mood,
            stamina=pet.stamina,
            state=new_state,
            bowl_expires_at=pet.bowl_expires_at,
            image_path=pet.image_path
        )

    @classmethod
    def apply_interact_effect(cls, pet: PetState) -> PetState:
        """
        套用寵物互動效果 (點擊寵物)
        
        Args:
            pet: 當前的寵物狀態
            
        Returns:
            更新後的寵物狀態
        """
        new_mood = min(cls.MAX_VAL, pet.mood + cls.MOOD_PET_INTERACT)
        new_state = cls.determine_state(new_mood)
        
        return PetState(
            id=pet.id,
            pet_name=pet.pet_name,
            level=pet.level,
            exp=pet.exp,
            mood=new_mood,
            stamina=pet.stamina,
            state=new_state,
            bowl_expires_at=pet.bowl_expires_at,
            image_path=pet.image_path
        )

    @classmethod
    def apply_task_reward(cls, pet: PetState, task_type: str) -> PetState:
        """
        套用任務獎勵到寵物狀態
        
        Args:
            pet: 當前的寵物狀態
            task_type: 任務類型 (all_meds, bp_task)
            
        Returns:
            更新後的寵物狀態
        """
        mood_gain_map = {
            "all_meds": cls.MOOD_ALL_MEDS,
            "bp_task": cls.MOOD_BP_TASK,
        }
        
        mood_gain = mood_gain_map.get(task_type, 0)
        new_mood = min(cls.MAX_VAL, pet.mood + mood_gain)
        new_state = cls.determine_state(new_mood)
        
        return PetState(
            id=pet.id,
            pet_name=pet.pet_name,
            level=pet.level,
            exp=pet.exp,
            mood=new_mood,
            stamina=pet.stamina,
            state=new_state,
            bowl_expires_at=pet.bowl_expires_at,
            image_path=pet.image_path
        )

    @classmethod
    def apply_time_decay(cls, pet: PetState, decay_count: int = 1) -> PetState:
        """
        套用時間衰減到寵物狀態
        
        每 4 小時衰減一次:
        - 心情 > 30: 每次 -5
        - 心情 <= 30: 每次 -2
        
        Args:
            pet: 當前的寵物狀態
            decay_count: 衰減次數 (預設 1 次)
            
        Returns:
            更新後的寵物狀態
        """
        new_mood = pet.mood
        
        for _ in range(decay_count):
            if new_mood > cls.MOOD_SAD_THRESHOLD:
                new_mood -= cls.DECAY_HIGH_MOOD
            else:
                new_mood -= cls.DECAY_LOW_MOOD
        
        # 確保不低於最小值
        new_mood = max(cls.MIN_VAL, new_mood)
        new_state = cls.determine_state(new_mood)
        
        return PetState(
            id=pet.id,
            pet_name=pet.pet_name,
            level=pet.level,
            exp=pet.exp,
            mood=new_mood,
            stamina=pet.stamina,
            state=new_state,
            bowl_expires_at=pet.bowl_expires_at,
            image_path=pet.image_path
        )

    @classmethod
    def handle_travel_return(cls, pet: PetState) -> PetState:
        """
        處理寵物從旅遊回家 (使用門票)
        
        回家後:
        - 保留原始等級
        - 心情重置為初始值 60
        - 狀態改為 Normal
        
        Args:
            pet: 當前的寵物狀態
            
        Returns:
            更新後的寵物狀態
        """
        return PetState(
            id=pet.id,
            pet_name=pet.pet_name,
            level=pet.level,  # 保留等級
            exp=pet.exp,
            mood=cls.INITIAL_MOOD,  # 重置心情為 60
            stamina=pet.stamina,
            state="Normal",
            bowl_expires_at=pet.bowl_expires_at,
            image_path=pet.image_path
        )

    # === 保留舊方法以維持向後相容 ===
    
    @classmethod
    def apply_taken(cls, pet: PetState) -> PetState:
        """
        套用「按時服藥」效果到寵物狀態 (舊方法,保留向後相容)
        
        注意: 此方法已被 apply_task_reward(pet, "all_meds") 取代
        
        Args:
            pet: 當前的寵物狀態
            
        Returns:
            更新後的寵物狀態
        """
        # 使用新的任務獎勵方法
        return cls.apply_task_reward(pet, "all_meds")

    @classmethod
    def apply_missed(cls, pet: PetState) -> PetState:
        """
        套用「漏服藥物」效果到寵物狀態 (舊方法,保留向後相容)
        
        注意: 漏服藥物不再直接影響心情,改由時間衰減機制處理
        
        Args:
            pet: 當前的寵物狀態
            
        Returns:
            更新後的寵物狀態 (不變)
        """
        # 漏服藥物不再直接扣心情,只是不給獎勵
        return pet
