from __future__ import annotations

import flet as ft
from ui.styles import colors


def quick_action_card(label: str, icon: str, on_click) -> ft.Container:
    return ft.Container(
        content=ft.Column(
            [
                ft.Icon(icon, size=28, color=colors.SECONDARY),
                ft.Text(label, size=13, weight="bold", color=colors.TEXT_PRIMARY),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        ),
        on_click=on_click,
        bgcolor=colors.BACKGROUND, 
        width=100,
        height=100,
        padding=10,
        border_radius=16,
        ink=True,
    )
