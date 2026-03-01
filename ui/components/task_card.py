from __future__ import annotations

import flet as ft
from ui.styles import colors

def task_card(
    *,
    drug_name: str,
    period_label: str,
    pills: int,
    status: str,
    on_taken,
    on_snooze,
) -> ft.Card:
    """
    用藥任務卡片組件。
    """
    # 根據狀態決定任務樣式
    status_color = colors.SUCCESS if status == "taken" else colors.SECONDARY if status == "snoozed" else colors.ERROR if status == "missed" else colors.TEXT_PRIMARY
    
    # --- 已用藥按鈕 (SUCCESS) ---
    taken_btn = ft.Container(
        content=ft.Text("我已服藥", color=colors.WHITE, weight="bold"),
        bgcolor=colors.SUCCESS,
        on_click=lambda _: on_taken(),
        padding=ft.padding.symmetric(horizontal=20, vertical=10),
        border_radius=8,
        ink=True,
    )
    
    # --- 延後提醒按鈕 (SECONDARY) ---
    snooze_btn = ft.Container(
        content=ft.Text("延後", color=colors.WHITE, weight="bold"),
        bgcolor=colors.SECONDARY,
        on_click=lambda _: on_snooze(),
        padding=ft.padding.symmetric(horizontal=20, vertical=10),
        border_radius=8,
        ink=True,
    )

    return ft.Card(
        content=ft.Container(
            padding=20,
            bgcolor=colors.WHITE,
            border=ft.border.all(1, colors.PRIMARY),
            border_radius=15,
            content=ft.Column(
                [
                    ft.Row([
                        ft.Text(drug_name, size=22, color=colors.TEXT_PRIMARY, weight="bold", expand=True),
                        ft.Container(
                            content=ft.Text(f" {status.upper()} ", color=colors.WHITE, weight="bold", size=12),
                            bgcolor=status_color,
                            border_radius=4,
                        )
                    ]),
                    ft.Text(f"時間: {period_label} | 份量: {pills} 錠", size=16, color=colors.TEXT_SECONDARY),
                    ft.Divider(height=1, color=colors.PRIMARY),
                    ft.Row(
                        [
                            taken_btn,
                            snooze_btn,
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        spacing=15,
                    ),
                ],
                spacing=16,
            ),
        )
    )
