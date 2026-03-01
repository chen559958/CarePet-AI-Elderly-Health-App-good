from app.container import Container
from ui.styles import colors

import flet as ft


async def build_register(page: ft.Page, on_register_success, on_go_login) -> ft.Control:
    """
    建立註冊頁面 UI。
    顯示手機號碼、密碼及確認密碼輸入欄位。
    """
    
    # 手機號碼輸入欄位
    phone_field = ft.TextField(
        label="手機號碼",
        hint_text="請輸入手機號碼",
        keyboard_type=ft.KeyboardType.PHONE,
        autofocus=True, # 自動取得焦點
        width=300,
        text_size=18,
        prefix_icon=ft.icons.PHONE,
        border_radius=10,
        color=colors.TEXT_PRIMARY
    )
    
    # 密碼設定欄位
    password_field = ft.TextField(
        label="設置密碼",
        password=True,
        can_reveal_password=True,
        hint_text="至少 6 個字元",
        width=300,
        text_size=18,
        prefix_icon=ft.icons.LOCK,
        border_radius=10,
        color=colors.TEXT_PRIMARY
    )
    
    # 密碼確認欄位
    confirm_password_field = ft.TextField(
        label="確認密碼",
        password=True,
        can_reveal_password=True,
        hint_text="再次輸入密碼",
        width=300,
        text_size=18,
    )
    
    # 錯誤訊息提示文字
    error_text = ft.Text("", color="red", size=14)
    
    # 處理註冊按鈕點擊
    async def handle_register(_):
        phone = phone_field.value
        password = password_field.value
        confirm_password = confirm_password_field.value
        
        # 簡易欄位檢查
        if not phone or not password or not confirm_password:
            error_text.value = "請填寫所有欄位"
            page.update()
            return
        
        # 確認密碼一致性
        if password != confirm_password:
            error_text.value = "兩次輸入的密碼不一致"
            page.update()
            return
        
        # 呼叫傳入的註冊驗證回調
        success, message = await on_register_success(phone, password)
        
        # 若失敗則顯示錯誤訊息
        if not success:
            error_text.value = message
            page.update()
    
    # 返回登入處理
    def handle_login(_):
        on_go_login()
    
    # 註冊提交按鈕
    register_button = ft.ElevatedButton(
        content=ft.Text("完成註冊", size=18, weight="bold"),
        bgcolor=colors.SECONDARY,
        color=colors.WHITE,
        width=300,
        height=50,
        on_click=handle_register, # Changed from on_register_click to handle_register to match existing logic
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    )
    
    # 登入頁面導引連結 (renamed and modified)
    login_back_button = ft.TextButton(
        "已有帳號? 回到登入",
        icon=ft.icons.ARROW_BACK_IOS_NEW,
        on_click=lambda _: on_go_login(), # Changed from on_go_to_login to on_go_login to match existing logic
        style=ft.ButtonStyle(color=colors.TEXT_PRIMARY)
    )
    
    # 頂部返回按鈕組件
    back_button = ft.Container(
        content=ft.Row([
            ft.Icon(ft.icons.ARROW_BACK_IOS_NEW, size=16, color=colors.TEXT_PRIMARY), # Replaced hardcoded color
            ft.Text("登入", size=16, color=colors.TEXT_PRIMARY, weight="bold"), # Replaced hardcoded color
        ], spacing=5),
        on_click=handle_login,
        padding=ft.padding.only(left=20, top=10),
    )
    
    # --- UI Elements ---
    title = ft.Text("建立新帳號", size=24, weight="bold", color=colors.TEXT_PRIMARY)
    
    # 頁面內容結構 (Stack 允許重疊佈局)
    content = ft.Stack([
        # 主要表單內容容器
        ft.Container(
            content=ft.Column([
                ft.Container(height=50), # 頂部間距
                ft.Icon(ft.icons.MEDICATION, size=80, color="#F7A89A"), # Logo 圖示 (kept as is, not in instruction to change)
                title, # Used the new title element
                ft.Container(height=30), # 間距
                phone_field,
                ft.Container(height=10),
                password_field,
                ft.Container(height=10),
                confirm_password_field,
                ft.Container(height=10),
                error_text,
                ft.Container(height=20),
                register_button,

            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.Alignment(0, 0), # 置中對齊
            expand=True,
            bgcolor="#F4F0EE", # 全域背景色
        ),
        # 將返回按鈕放置於左上角
        ft.Container(
            content=back_button,
            top=10,
            left=0,
        ),
    ], expand=True)
    
    return content
    
