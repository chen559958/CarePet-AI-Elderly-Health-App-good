from __future__ import annotations

from app.container import Container
from ui.styles import colors

import flet as ft


async def build_login(page: ft.Page, on_login_success, on_go_register) -> ft.Control:
    """
    建立登入頁面 UI，包含模擬忘記密碼流程。
    """
    print(">>> 進入 login_page.py:build_login()")
    container = Container.get_instance()

    auth_service = container.auth_service
    
    # --- 狀態變數 ---
    flow_view = ft.Ref[ft.Column]()
    current_phone = ""
    
    # --- UI 元件定義 ---
    error_text = ft.Text("", color="red", size=14)
    
    # 登入用欄位
    login_phone = ft.TextField(label="手機號碼", prefix_icon=ft.icons.PHONE, width=300, border_radius=10)
    login_password = ft.TextField(label="密碼", password=True, can_reveal_password=True, prefix_icon=ft.icons.LOCK, width=300, border_radius=10)
    
    # 忘記密碼用欄位
    forgot_phone = ft.TextField(label="註冊手機號碼", prefix_icon=ft.icons.PHONE, width=300, border_radius=10)
    forgot_code = ft.TextField(label="驗證碼 (隨機 5 碼)", prefix_icon=ft.icons.SECURITY, width=300, border_radius=10, keyboard_type=ft.KeyboardType.NUMBER)
    new_password = ft.TextField(label="設定新密碼", password=True, can_reveal_password=True, prefix_icon=ft.icons.LOCK, width=300, border_radius=10)
    confirm_password = ft.TextField(label="再次確認新密碼", password=True, can_reveal_password=True, prefix_icon=ft.icons.LOCK, width=300, border_radius=10)

    # --- 流程切換函式 ---
    def switch_view(view_name):
        error_text.value = ""
        main_col.controls.clear()
        
        if view_name == "login":
            main_col.controls.extend([
                ft.Container(height=40),
                ft.Icon(ft.icons.MEDICATION, size=80, color=colors.PRIMARY),
                ft.Text("藥獸GOOD", size=32, weight="bold", color=colors.TEXT_PRIMARY),
                ft.Text("您的智慧用藥好夥伴", size=16, color=colors.TEXT_SECONDARY),
                ft.Container(height=30),
                login_phone,
                ft.Container(height=10),
                login_password,
                error_text,
                ft.Container(height=10),
                ft.ElevatedButton("登入", bgcolor=colors.SECONDARY, color=colors.WHITE, width=300, height=50, on_click=handle_login),
                ft.TextButton("忘記密碼?", on_click=lambda _: switch_view("forgot_phone")),
                ft.TextButton("還沒有帳號? 立即註冊", on_click=lambda _: on_go_register()),
            ])
        elif view_name == "forgot_phone":
            main_col.controls.extend([
                ft.Text("重設密碼 (階段 1/3)", size=20, weight="bold"),
                ft.Text("請輸入您的手機號碼以獲取驗證碼", size=14, color=colors.TEXT_SECONDARY),
                ft.Container(height=20),
                forgot_phone,
                error_text,
                ft.Container(height=20),
                ft.ElevatedButton("發送驗證碼", bgcolor=colors.PRIMARY, color=colors.WHITE, width=300, on_click=handle_send_code),
                ft.TextButton("返回登入", on_click=lambda _: switch_view("login")),
            ])
        elif view_name == "forgot_code":
            main_col.controls.extend([
                ft.Text("輸入驗證碼 (階段 2/3)", size=20, weight="bold"),
                ft.Text(f"驗證碼已發送至 {current_phone}", size=14, color=colors.TEXT_SECONDARY),
                ft.Container(height=20),
                forgot_code,
                error_text,
                ft.Container(height=20),
                ft.ElevatedButton("驗證", bgcolor=colors.PRIMARY, color=colors.WHITE, width=300, on_click=handle_verify_code),
            ])
        elif view_name == "forgot_password":
            main_col.controls.extend([
                ft.Text("設定新密碼 (階段 3/3)", size=20, weight="bold"),
                ft.Text("請為您的帳號設置一個新的強力密碼", size=14, color=colors.TEXT_SECONDARY),
                ft.Container(height=20),
                new_password,
                ft.Container(height=10),
                confirm_password,
                error_text,
                ft.Container(height=20),
                ft.ElevatedButton("確認變更並登入", bgcolor=colors.SECONDARY, color=colors.WHITE, width=300, on_click=handle_reset_password),
            ])
        page.update()

    # --- 事件處理 ---
    async def handle_login(e):
        if not login_phone.value or not login_password.value:
            error_text.value = "請輸入完整登入資訊"; page.update(); return
        success, message = await on_login_success(login_phone.value, login_password.value)
        if not success: error_text.value = message; page.update()

    def handle_send_code(e):
        nonlocal current_phone
        if not forgot_phone.value:
            error_text.value = "請輸入手機號碼"; page.update(); return
        current_phone = forgot_phone.value
        switch_view("forgot_code")

    def handle_verify_code(e):
        if len(forgot_code.value) != 5:
            error_text.value = "請輸入 5 位數字驗證碼"; page.update(); return
        switch_view("forgot_password")

    async def handle_reset_password(e):
        if not new_password.value or len(new_password.value) < 6:
            error_text.value = "密碼至少需 6 個字元"; page.update(); return
        
        if new_password.value != confirm_password.value:
            error_text.value = "兩次輸入的密碼不一致"; page.update(); return
        
        success, message = auth_service.reset_password(current_phone, new_password.value)
        if success:
            # 觸發與 handle_login 相同的成功流程 (通常是跳轉首頁)
            await on_login_success(current_phone, new_password.value)
        else:
            error_text.value = message
            page.update()

    # --- 初始佈局 ---
    main_col = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    switch_view("login")
    
    return ft.Container(
        content=main_col,
        alignment=ft.Alignment(0, 0),
        expand=True,
        bgcolor="#F4F0EE",
    )
