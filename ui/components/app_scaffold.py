from __future__ import annotations

import flet as ft
from ui.styles import colors


# 核心應用程式架構組件
def app_scaffold(content: ft.Control, *, selected_tab: str, page: ft.Page, padding: int = 20, hide_top_bar: bool = False, top_bar_title: str | None = None, title_ref: ft.Ref[ft.Text] | None = None) -> ft.Control:
    """
    建立應用程式的通用框架，包含頂部返回列與底部導覽列。
    
    參數:
        content: 頁面的主要內容控制項
        selected_tab: 當前選中的分頁名稱
        page: Flet 頁面實例
        padding: 內容區域的內距，預設為 20
        hide_top_bar: 是否隱藏頂部返回列 (預設 False)
        top_bar_title: 頂部標題文字 (預設為 "HOME")
        title_ref: 獲取標題 Text 控制項的引用，用於動態更新。
    """
    
    # --- 響應式縮放邏輯 (比照碗的邏輯) ---
    curr_width = page.window.width if page.window.width else 450

    icon_base = min(56, max(36, curr_width * 0.2))
    text_base = min(26, max(15, 12 + curr_width * 0.01))


    
    def nav_item(label: str, route: str, icon_data: str, is_selected: bool) -> ft.Control:
        curr_icon_size = icon_base
        curr_text_size = text_base

        # 建立圖示 - 支援圖片和系統圖示
        if isinstance(icon_data, str) and (".png" in icon_data or "/" in icon_data):
            # 圖片路徑
            icon_widget = ft.Image(
                src=icon_data,
                width=curr_icon_size,
                height=curr_icon_size,
                fit=ft.ImageFit.CONTAIN,
            )
        else:
            # 系統圖示
            icon_widget = ft.Icon(
                icon_data,
                color=colors.NAVI_GLOW if is_selected else colors.TEXT_SECONDARY,
                size=curr_icon_size,
            )
        
        # --- 智慧換行邏輯 ---
        # 如果標籤中有空格，將其拆分為多個 Text 組件，並放入水平包裝 Row 中
        text_parts = []
        for part in label.split(" "):
            text_parts.append(
                ft.Text(
                    part,
                    size=curr_text_size,
                    text_align=ft.TextAlign.CENTER,
                    weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL,
                    color=colors.NAVI_GLOW if is_selected else colors.TEXT_PRIMARY,
                )
            )
        
        text_container = ft.Row(
            controls=text_parts,
            wrap=True, # 空間不足時自動換行
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=0, # 兩個字組件之間不要間距，看起來像一個詞
            run_spacing=0,
        )
        
        # 返回按鈕容器
        return ft.Container(
            content=ft.Column(
                controls=[
                    # 使用固定高度容器包裝圖示，確保所有圖示在同一水平線上
                    ft.Container(
                        content=icon_widget,
                        height=icon_base * 1.1, 
                        alignment=ft.alignment.top_center, # 改為靠頂，減少上方空白
                    ),
                    text_container # 使用智慧換行容器
                ],
                alignment=ft.MainAxisAlignment.START, # 從頂部開始排列
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=3, # 稍微增加間距，避免圖示跟字太擠
                tight=True,
            ),
            on_click=lambda _: page.go(route),
            padding=ft.padding.only(top=2, bottom=2, left=2, right=2), # 頂部 padding 縮小至 2
            bgcolor=colors.PRIMARY if is_selected else ft.colors.TRANSPARENT,
            border_radius=12,
            expand=True,
            ink=True,
        )

    # 底部導覽列容器 (Custom Row)
    nav_bar = ft.Container(
        content=ft.Row(
            [
                nav_item("圖鑑", "/gallery", "/nav_icons/magnifier.png", selected_tab == "Gallery"),
                nav_item("紀錄", "/records", "/nav_icons/record.png", selected_tab == "Records"),
                nav_item("開始 任務", "/tasks", "/nav_icons/pill.png", selected_tab == "Tasks"),
                nav_item("商城", "/shop", "/nav_icons/bag.png", selected_tab == "Shop"),
                nav_item("設定", "/member", "/nav_icons/set.png", selected_tab == "Member"),
            ],
            spacing=2,
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        bgcolor=colors.BACKGROUND,
        padding=ft.padding.only(top=5, bottom=3, left=5, right=5),
        # height=100, 
        border=ft.border.only(top=ft.border.BorderSide(1, colors.PRIMARY)),
    )
    
    # 頂部工具列（非首頁時顯示返回按鈕）
    top_bar = None
    if selected_tab != "Home" and not hide_top_bar:
        # 計算頂部標題響應式字體大小 (放大)
        top_title_size = min(32, max(20, 14 + curr_width * 0.02))
        
        # 如果沒傳標題，預設用 "HOME"
        display_title = top_bar_title if top_bar_title else "HOME"
        
        # 返回首頁的動作
        async def go_home(e):
            # 優先檢查是否有傳入自定義的首頁跳轉邏輯 (例如需要帶參數)
            target_route = "/"
            if hasattr(page, "extra_data") and page.extra_data.get("task_recently_completed"):
                target_route = "/?show_reward=1"
                # 消耗掉這個狀態，避免重複觸發
                page.extra_data["task_recently_completed"] = False
            
            page.go(target_route)

        top_bar = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Image(
                        src="/nav_icons/home.png", 
                        width=38, 
                        height=38,
                        disabled=True, # 讓點擊穿透
                    ), 
                    padding=ft.padding.only(left=10),
                    on_click=go_home, # 雙重保障：內層也綁定
                ),
                ft.Text(display_title, color=colors.TEXT_PRIMARY, size=top_title_size, weight="bold", ref=title_ref)
            ], alignment=ft.MainAxisAlignment.START),
            padding=ft.padding.only(left=10, top=10, bottom=5),
            bgcolor=colors.BACKGROUND,
            on_click=go_home, # 外層綁定
            ink=True, # 加入水波紋點擊效果
        )

    # 主要佈局結構
    controls = []
    if top_bar:
        controls.append(top_bar)
        
    # 返回內容：將頁面內容與導航列垂直排列
    # 使用 expand=True 確保內容區域能撐滿除了導航列以外的所有空間
    return ft.Column(
        controls=[
            # 只有當 top_bar 存在時才放入 controls，避免重複或多餘空間
            *( [top_bar] if top_bar else [] ),
            
            # 主內容層
            ft.Container(
                content=content,
                expand=True,
                padding=padding,
            ),
            
            # 底部工具列 (Custom)
            nav_bar, 
        ],
        spacing=0,
        expand=True,
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )


def _tab_index(tab_name: str) -> int:
    """根據分頁名稱獲取索引（保留作擴充用）"""
    match tab_name:
        case "Home":
            return 0
        case "Records":
            return 1
        case "Shop":
            return 2
        case "Member":
            return 3
    return 0
