import flet as ft
from ui.styles import colors

def mood_heart(mood: int, text_size: int = 24) -> ft.Control:
    """顯示單顆愛心，填滿比例對應 mood 0~100，文字疊加在愛心上"""
    icon_size = int(text_size * 2.5)
    mood = max(0, min(100, mood))

    # 之前給的填色邏輯：映射 0~100 到心形的實際視覺區間 (約 8% 到 88% 的高度)
    # 這樣 90% 就不會看起來完全滿掉，0% 也不會完全沒顏色
    visual_ratio = (mood / 100) * 0.8 + 0.08
    visual_height = icon_size * visual_ratio

    return ft.Stack(
        [
            # 背景：空心
            ft.Image(src="/heart_0%.png", width=icon_size, height=icon_size, fit=ft.ImageFit.CONTAIN),
            # 前景：實心 (由下往上填滿)
            ft.Container(
                width=icon_size,
                height=visual_height,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                animate=ft.animation.Animation(600, ft.AnimationCurve.EASE_OUT_QUART),
                content=ft.Stack(
                    [
                        ft.Image(
                            src="/heart_100%.png",
                            width=icon_size,
                            height=icon_size,
                            fit=ft.ImageFit.CONTAIN,
                            bottom=0,
                        ),
                    ],
                ),
            ),
            # 文字疊加層
            ft.Container(
                content=ft.Text(
                    f"{mood}",
                    size=int(icon_size * 0.35),
                    weight="bold",
                    color=colors.TEXT_PRIMARY,
                ),
                alignment=ft.alignment.center,
                width=icon_size,
                height=icon_size,
            ),
            # 水平切線
            ft.Container(
                width=icon_size * 0.83, 
                left=icon_size * 0.085, 
                bottom=0,
                height=icon_size,
                visible=0 < mood < 100,
                content=ft.ShaderMask(
                    content=ft.Image(
                        src="/heart_100%.png",
                        width=icon_size,
                        height=icon_size,
                        fit=ft.ImageFit.NONE,
                    ),
                    blend_mode=ft.BlendMode.SRC_IN,
                    shader=ft.LinearGradient(
                        begin=ft.alignment.bottom_center,
                        end=ft.alignment.top_center,
                        colors=[ft.colors.TRANSPARENT, ft.colors.with_opacity(0.4, colors.TEXT_PRIMARY), ft.colors.TRANSPARENT],
                        stops=[
                            visual_ratio - 0.015,
                            visual_ratio,
                            visual_ratio + 0.015
                        ],
                    ),
                ),
            ),
        ],
        width=icon_size,
        height=icon_size,
        alignment=ft.alignment.bottom_center,
    )


def pet_panel(*, pet_name, level, exp, mood, stamina, image_path=None, page: ft.Page, on_bowl_click=None, on_pet_click=None, item_animation_widget=None, reward_trigger=None):
    # 判斷是否最大化 (用於控制外框寬度)
    is_maximized = page.window.maximized or page.window.full_screen
    

    curr_width = page.window.width if page.window.width else 450
    
    # 外框寬度 (維持二元切換，避免拉動時外框一直抖動)
    PET_WIDTH = 700 if is_maximized else 500
    TEXT_WIDTH = 1150 if is_maximized else 800

    # NAME_SIZE = min(36, max(24, curr_width * 0.024)) #curr_width螢幕寬度 * 0.024
    # LV_SIZE = min(32, max(20, curr_width * 0.021))
    # bowl_size = min(150, max(80, curr_width * 0.15))
    # MOOD_TEXT_SIZE = min(40, max(22, curr_width * 0.05))

    # 新的線性偏移公式：基礎值 + (寬度 * 係數)
    # 這樣小視窗會更早開始增長，大視窗增加速度較穩定
    NAME_SIZE = min(36, max(24, 18 + curr_width * 0.015)) 
    LV_SIZE = min(30, max(18, 15 + curr_width * 0.012))
    bowl_size = min(150, max(80, 30 + curr_width * 0.05))
    MOOD_TEXT_SIZE = min(40, max(22, 16 + curr_width * 0.02))
    
    pet_size = min(300, max(200, 190 + curr_width * 0.07))

    from domain.level_engine import LevelEngine
    req_exp = LevelEngine.get_required_exp(level)
    xp_progress = min(1.0, exp / req_exp) if req_exp > 0 else 1.0

    # 使用動態圖片路徑，若無則使用預設
    # 注意: assets 路徑在 Flet 中通常對應 src="/" (如果在 assets 目錄下)
    # 這裡我們假設 image_path 存的是 "assets/gallery/pet_cat.png"
    # Flet main.py 設定了 assets_dir="assets"，所以 "assets/" 開頭的路徑要調整
    # 如果路徑已經包含 "assets/"，Flet 預設會從 assets_dir 相對路徑找
    # 例如 src="gallery/pet_cat.png" 對應 "assets/gallery/pet_cat.png"
    
    # 修改邏輯: 去除 "assets/" 前綴以符合 Flet 資源路徑規則
    if image_path:
        src_path = image_path.replace("assets/", "/")
        if not src_path.startswith("/"):
            src_path = "/" + src_path
    else:
        src_path = "/pet.png"

    pet_img = ft.Image(
        src=src_path, 
        width=pet_size,
        fit=ft.ImageFit.CONTAIN,
    )
    
    bowl_img = ft.Container(
        content=ft.Image(
            src="/food_full.png" if stamina >= 60 else "/food_empty.png",
            fit=ft.ImageFit.CONTAIN,
        ),
        width=bowl_size,
        # animate_width 必須在 Image 括號外面，Container 括號裡面
        # animate=ft.animation.Animation(300, ft.AnimationCurve.DECELERATE),
        animate=ft.animation.Animation(100, ft.AnimationCurve.EASE_OUT), #看會不會比較順
    )   

    # # 封裝寵物互動區 Container，以便後續動態修改
    # is_max = page.window.maximized or page.window.full_screen
    # card_container = ft.Container(
    #     width=MAX_CARD_WIDTH,
    #     expand=True,
    #     border=ft.border.all(2, ft.colors.RED_ACCENT),
    #     bgcolor=ft.colors.with_opacity(0.05, ft.colors.BLUE),
    #     padding=10,
    #     content=ft.Stack([
    #         ft.Container(content=pet_img, alignment=ft.alignment.bottom_right, expand=True),
    #         ft.Container(content=bowl_img, left=10, bottom=-10),
    #     ]),
    # )

    # # --- 2. 定義響應式監聽函式 ---
    # def on_page_resize(e):
    #     # 重新計算數值
    #     curr_width = page.window.width
    #     new_bowl_size = min(150, max(80, curr_width * 0.1))
    #     # is_max_now = page.window.maximized or page.window.full_screen
        
    #     # 更新元件屬性
    #     bowl_img.width = new_bowl_size
    #     # card_container.width = MAX_CARD_WIDTH
        
    #     # 執行更新
    #     page.update()

    # # 綁定監聽
    # page.on_resize = on_page_resize


    async def on_pet_interaction(e):
        """Combo: Jump animation + Callback"""
        await jump_pet(e.control)
        if on_pet_click:
            await on_pet_click(e)

    # --- 以下為動畫邏輯 (放在變數定義與元件建立之後) ---

    # 硬幣 (Token) 容器
    token_widget = ft.Container(
        content=ft.Image(
            src="/token.png", 
            width=bowl_size * 1.2, 
            fit=ft.ImageFit.CONTAIN
        ),
        opacity=0,
        offset=ft.transform.Offset(0, 0),
        animate_opacity=ft.animation.Animation(400, ft.AnimationCurve.EASE_OUT),
        animate_offset=ft.animation.Animation(800, ft.AnimationCurve.EASE_OUT_EXPO),
    )

    async def jump_pet(control: ft.Container):
        """讓寵物跳一下的動畫"""
        if not control.page:
            return
        control.offset = ft.transform.Offset(0, -0.15) # 往上跳
        control.update()
        import asyncio
        await asyncio.sleep(0.3)
        if not control.page:
            return
        control.offset = ft.transform.Offset(0, 0) # 回到原位
        control.update()

    async def show_reward_animation():
        """執行任務完成後的驚喜動畫：硬幣上升"""
        if not pet_container.page:
            return
            
        import asyncio
        # 1. 寵物跳一下
        pet_container.offset = ft.transform.Offset(0, -0.15)
        pet_container.update()
        
        # 2. Token 出現並大力升起
        token_widget.opacity = 1
        token_widget.offset = ft.transform.Offset(0, -1.5) # 往上飛，確保飛出頭頂
        if token_widget.page:
            token_widget.update()
        
        await asyncio.sleep(0.3)
        if not pet_container.page:
            return
            
        pet_container.offset = ft.transform.Offset(0, 0)
        pet_container.update()
        
        # 3. 停留一秒 (如需求)
        await asyncio.sleep(1.1)
        
        # 4. 消失
        # 4. 消失
        token_widget.opacity = 0
        if token_widget.page:
            token_widget.update()
        await asyncio.sleep(0.4)
        # 重設位置
        # 重設位置
        token_widget.offset = ft.transform.Offset(0, 0)
        if token_widget.page:
            token_widget.update()

    # 偵測是否由首頁鍵觸發的獎勵
    if reward_trigger:
        async def delayed_reward():
            import asyncio
            # 增加初始延遲，等待頁面切換過渡效果完成
            await asyncio.sleep(0.8) 
            while not pet_container.page: # 確保元件已掛載
                await asyncio.sleep(0.1)
            await show_reward_animation()
        page.run_task(delayed_reward)

    return ft.Column(
        [
            # --- 第一個紅框：文字資訊區 ---
            ft.Container(
                alignment=ft.alignment.center,
                content=ft.Container(
                    width=TEXT_WIDTH,
                    padding=ft.padding.symmetric(horizontal=20, vertical=15),
                    # border=ft.border.all(2, ft.colors.TRANSPARENT), 
                    border_radius=0, 
                    bgcolor=ft.colors.TRANSPARENT,
                    content=ft.Row(
                        [
                            ft.Container(
                                content=ft.Column([
                                    ft.Text(pet_name, size=NAME_SIZE, weight="bold", color=colors.TEXT_PRIMARY),
                                    ft.Row([
                                        ft.Text(f"Lv.{level}", size=LV_SIZE, weight="bold", color=colors.TEXT_PRIMARY),
                                        ft.Container(
                                            content=ft.Stack([
                                                ft.ProgressBar(
                                                    value=xp_progress,
                                                    width=150,
                                                    height=17,
                                                    color=colors.BABY_BLUE,
                                                    bgcolor=ft.colors.with_opacity(0.3, colors.TEXT_SECONDARY),
                                                    border_radius=9,
                                                ),
                                                ft.Container(
                                                    content=ft.Text(f"{exp}", size=11, color=colors.WHITE, weight="bold"),
                                                    alignment=ft.alignment.center,
                                                    width=150 * xp_progress,
                                                    height=17,
                                                )
                                            ]),
                                            border=ft.border.all(1, colors.TEXT_SECONDARY),
                                            border_radius=10,
                                            padding=0,
                                        ),
                                        ft.Text(f"{req_exp}", size=12, color=colors.TEXT_SECONDARY, weight="bold")
                                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                                    
                                ], spacing=2),
                                bgcolor=ft.colors.TRANSPARENT,
                                padding=0,
                            ),
                            mood_heart(mood, text_size=MOOD_TEXT_SIZE),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ),
            ),    
            # --- 第二個紅框：寵物互動區 ---
            ft.Container(
                alignment=ft.alignment.center,
                expand=True,
                content=ft.Container(                       
                    width=PET_WIDTH, 
                    expand=True,
                    # border=ft.border.all(2, ft.colors.RED_ACCENT),  紅色輔助框
                    # bgcolor=ft.colors.with_opacity(0.05, ft.colors.BLUE),                     
                    border=ft.border.all(2, ft.colors.TRANSPARENT), 
                    bgcolor=ft.colors.TRANSPARENT, 
                    border_radius=0, 
                    padding=10, 
                    alignment=ft.alignment.top_center, 
                    content=ft.Stack(
                        [
                            # 硬幣層 (放在寵物後面)
                            ft.Container(
                                content=token_widget,
                                right=pet_size * 0.29, # 往左一點，對準熊熊背後
                                bottom=pet_size * 0.29, # 調整初始垂直位置
                            ),
                            # 寵物層
                            pet_container := ft.Container(
                                content=pet_img,
                                alignment=ft.alignment.bottom_right,                               
                                padding=ft.padding.only(right=-5),
                                expand=True,
                                animate_offset=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT_BACK),
                                offset=ft.transform.Offset(0, 0),
                                on_click=on_pet_interaction,
                            ),
                            # 飼料盆層
                            ft.Container(
                                content=bowl_img,
                                left=10,    
                                bottom=-10,
                                on_click=on_bowl_click,
                            ),
                            # 物品動畫層（如果有）
                            *([item_animation_widget] if item_animation_widget else []),
                        ],
                    ),
                ),
            ),
        ],
        spacing=10, 
        expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )