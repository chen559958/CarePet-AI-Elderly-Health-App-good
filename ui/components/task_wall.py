from __future__ import annotations

import flet as ft

from ui.components.task_card import task_card
from ui.styles import colors


class TaskWall(ft.Column):
    def __init__(self, *, on_refresh, tasks: list[dict]):
        print(f"DEBUG: TaskWall tasks count={len(tasks)}")
        cards = [
            task_card(
                drug_name=item["drug_name"],
                period_label=item["period"],
                pills=item["pills"],
                status=item["status"],
                on_taken=item["on_taken"],
                on_snooze=item["on_snooze"],
            )
            for item in tasks
        ]
        if not cards:
            cards = [ft.Text("今日沒有任務，請新增藥品。", style=ft.TextThemeStyle.BODY_LARGE, color=colors.TEXT_SECONDARY)]
        
        super().__init__(
            controls=[
                ft.Row(
                    [
                        ft.Text("今日任務", size=24, color=colors.TEXT_PRIMARY, weight="bold"),
                        ft.Container(
                            content=ft.Icon(ft.icons.REFRESH, color=colors.TEXT_PRIMARY),
                            on_click=on_refresh,
                            padding=5,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                *cards,
            ],
            spacing=16,
        )
