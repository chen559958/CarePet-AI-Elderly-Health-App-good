from __future__ import annotations
import asyncio
import flet as ft
from app.container import Container
from ui.styles import colors
from ui.components.app_scaffold import app_scaffold
from ui.viewmodels.home_viewmodel import HomeViewModel
from domain.watcher import reminder_watcher
from datetime import datetime, timedelta
from domain.utils import get_now_taiwan
from collections import defaultdict

class TaskView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.page = page
        self.container = Container.get_instance()
        self.vm = HomeViewModel(self.container) # Keep HomeViewModel as per original code, not TaskViewModel from snippet
        self.title_ref = ft.Ref[ft.Text]()
        
        self.data = {"tasks": [], "bp_completed": False} # Keep self.data as per original code
        self.events = [] # Added from snippet
        self.is_loading = True
        self._subscription = None # Changed from self.subscription
        self.main_container = self # TaskView is the container
        
        # Initial UI sync
        self._sync_ui()

    def did_mount(self):
        self.vm._create_task(self._init_data())
        self._subscription = reminder_watcher.subscribe(self._handle_watcher_notify)

    def _handle_watcher_notify(self):
        if self.page:
            self.vm._create_task(self._on_refresh())

    def will_unmount(self):
        if self._subscription:
            reminder_watcher.unsubscribe(self._subscription)
        self.vm.dispose()
        print("DEBUG: TaskView unmounted.")

    async def _init_data(self):
        await self._load_data()

    async def _on_refresh(self):
        await self._load_data()

    async def _load_data(self):
        self.is_loading = True
        self.update()
        try:
            self.data = await self.vm.load_dashboard()
        except Exception as e:
            print(f"ERROR: TaskView _load_data failed: {e}")
        finally:
            self.is_loading = False
            self._sync_ui()
            if self.page:
                self.update()

    async def on_task_action(self, action_func, tid):
        print(f"DEBUG: on_task_action triggered for event {tid}")
        try:
            await action_func(tid)
            
            # 標記任務剛完成，供 app_scaffold 判斷首頁動畫
            if not hasattr(self.page, "extra_data"):
                self.page.extra_data = {}
            self.page.extra_data["task_recently_completed"] = True
            
            self.page.snack_bar = ft.SnackBar(ft.Text("狀態已更新！完成任務後可以點擊 Home 回去找寵物領賞喔！"), open=True)
            self.page.update()
            
            # Local update is handled by separate watcher notification inside VM usually.
            # But wait, VM.mark_taken calls reminder_watcher.notify().
            # So _on_refresh will be called.
            
        except Exception as e:
            print(f"Error in on_task_action: {e}")

    def go_add_drug(self, mode=None):
        self.page.data = {"add_drug_mode": mode}
        self.page.go("/add_drug")

    def _sync_ui(self):

        if self.is_loading:
            self.main_container.content = ft.Container(expand=True, alignment=ft.alignment.center, content=ft.ProgressRing())
            return
            
        # Data Extraction
        tasks = self.data.get("tasks", [])
        if not tasks and not self.data.get("pet"): # If both are missing, something probably failed
             self.main_container.content = ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                content=ft.Column([
                    ft.Icon(ft.icons.ERROR_OUTLINE, size=50, color=colors.ERROR),
                    ft.Text("無法載入任務資料", size=16, color=colors.TEXT_SECONDARY),
                    ft.ElevatedButton("重試", on_click=lambda _: self.page.run_task(self._load_data))
                ], horizontal_alignment="center", spacing=20)
            )
             return
        
        bp_completed = self.data.get("bp_completed", False)
        
        # 每日任務按鈕
        daily_tasks_btn = ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.ASSIGNMENT_TURNED_IN, size=40, color=colors.TEXT_PRIMARY),
                ft.Text("每日任務", size=18, weight="bold", color=colors.TEXT_PRIMARY),
                ft.Text("量測血壓與脈搏" if not bp_completed else "✓ 已完成", size=14, color=colors.TEXT_PRIMARY),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=colors.PRIMARY if not bp_completed else colors.WHITE,
            border_radius=15, padding=20, expand=1,
            border=ft.border.all(2, colors.SECONDARY if not bp_completed else colors.PRIMARY),
            on_click=lambda _: self.page.go("/add_bp"),
            ink=True,
        )

        # 新增藥品按鈕
        add_task_btn = ft.Container(
            content=ft.Column([
                ft.Image(src="/nav_icons/plus.png", width=40, height=40, fit="contain"),
                ft.Text("新增藥品", size=18, weight="bold", color=colors.TEXT_PRIMARY),
                ft.Text("", size=14),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=colors.PRIMARY if not bp_completed else colors.WHITE, # Logic copied from old code, intentional?
            border_radius=15, padding=20, expand=1,
            border=ft.border.all(2, colors.SECONDARY if not bp_completed else colors.PRIMARY),
            on_click=lambda _: self.go_add_drug(None),
            ink=True,
        )

        # 藥物列表邏輯
        groups = defaultdict(list)
        for t in tasks:
            groups[t["drug_name"]].append(t)
        
        now = get_now_taiwan()
        today_str = now.strftime("%Y-%m-%d")
        
        med_list = ft.Column(spacing=15)
        
        if not groups:
            med_list.controls.append(
                ft.Container(
                    content=ft.Text("今天沒有用藥項目囉!", color=colors.TEXT_SECONDARY),
                    padding=20, alignment=ft.Alignment(0, 0)
                )
            )
        else:
            for drug_name, group_tasks in groups.items():
                group_tasks.sort(key=lambda x: x["period"])
                
                task_status_controls = []
                for i, task in enumerate(group_tasks):
                    planned_dt = datetime.strptime(f"{today_str} {task['period']}", "%Y-%m-%d %H:%M").replace(tzinfo=now.tzinfo)
                    unlock_dt = planned_dt - timedelta(minutes=30)
                    
                    if i < len(group_tasks) - 1:
                        next_task = group_tasks[i+1]
                        next_planned_dt = datetime.strptime(f"{today_str} {next_task['period']}", "%Y-%m-%d %H:%M").replace(tzinfo=now.tzinfo)
                        expire_dt = next_planned_dt - timedelta(minutes=30)
                    else:
                        expire_dt = planned_dt.replace(hour=23, minute=59, second=59)

                    is_active = unlock_dt <= now < expire_dt
                    is_future = now < unlock_dt
                    status = task["status"]

                    # Status Badge Construction
                    if status == "taken":
                        task_status_controls.append(
                            ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.icons.CHECK_CIRCLE, color=colors.SUCCESS, size=18),
                                    ft.Text(f"{task['period']} {task['period_label']} {task['timing_label']}".strip() + " 已服", color=colors.SUCCESS, size=14, weight="bold")
                                ], spacing=3),
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                bgcolor=ft.colors.with_opacity(0.1, colors.SUCCESS),
                                border_radius=6,
                            )
                        )
                    elif is_active:
                         task_status_controls.append(
                            ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.icons.PLAY_ARROW, color=colors.WHITE, size=16),
                                    ft.Text(f"{task['period']} {task['period_label']} {task['timing_label']}".strip() + " 該吃藥囉~", color=colors.WHITE, size=14, weight="bold")
                                ], spacing=3),
                                bgcolor=colors.SUCCESS,
                                padding=ft.padding.symmetric(horizontal=10, vertical=6),
                                border_radius=8,
                                on_click=lambda e, t=task: self.page_ref.run_task(self.on_task_action, t['on_taken'], t['event_id']),
                                ink=True,
                            )
                        )
                    elif is_future:
                        task_status_controls.append(
                            ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.icons.SCHEDULE, color="grey", size=16),
                                    ft.Text(f"{task['period']} {task['period_label']} {task['timing_label']}".strip() + " 鎖定", color="grey", size=13)
                                ], spacing=3),
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                border=ft.border.all(1, "grey"), border_radius=6, opacity=0.6,
                            )
                        )
                    else:
                         task_status_controls.append(
                            ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.icons.ALARM_OFF, color=colors.ERROR, size=16),
                                    ft.Text(f"{task['period']} {task['period_label']} {task['timing_label']}".strip() + " 逾期", color=colors.ERROR, size=13, weight="bold")
                                ], spacing=3),
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                bgcolor=ft.colors.with_opacity(0.1, colors.ERROR),
                                border_radius=6,
                                on_click=lambda e, t=task: self.page_ref.run_task(self.on_task_action, t['on_taken'], t['event_id']),
                                ink=True,
                            )
                        )

                med_list.controls.append(
                    ft.Container(
                        padding=15, bgcolor=colors.WHITE, border_radius=12,
                        border=ft.border.all(1, colors.PRIMARY),
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.icons.MEDICAL_SERVICES, color=colors.PRIMARY, size=20),
                                ft.Text(drug_name, size=18, weight="bold", color=colors.TEXT_PRIMARY, expand=True),
                                ft.Text(f"{group_tasks[0]['pills']} 錠/次", size=13, color=colors.TEXT_SECONDARY),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Divider(height=1, color=ft.colors.with_opacity(0.1, colors.PRIMARY)),
                            ft.Row(task_status_controls, wrap=True, spacing=10, run_spacing=10),
                        ], spacing=10)
                    )
                )

        self.main_container.content = ft.Column(
            [
                ft.Text("任務調度站", size=24, color=colors.TEXT_PRIMARY, weight="bold"),
                ft.Divider(height=1, color=colors.PRIMARY),
                ft.Row([daily_tasks_btn, add_task_btn], spacing=15),
                ft.Text("今日用藥清單", size=18, color=colors.TEXT_PRIMARY, weight="bold"),
                med_list,
            ],
            spacing=20, scroll=ft.ScrollMode.AUTO,
        )

async def build_tasks(page: ft.Page) -> ft.Control:
    # Notice: Top Bar Title needs to be passed to scaffold, but TaskView calculates it dynamically based on data?
    # Actually TaskView calculates it in build().
    # AppScaffold constructs the AppBar.
    # If we pass TaskView to AppScaffold, AppScaffold builds its layout.
    # The title in AppScaffold is usually static per page type unless passed.
    # The original code calculated title in build_tasks.
    # We can do the same here lightly.
    
    container = Container.get_instance()
    user = container.auth_service.get_current_user()
    pet = await container.pet_repo.get_pet(user.id) if user else None
    pet_name = pet.pet_name if pet else "寵物"
    custom_title = f"做完任務去找{pet_name}領賞吧!"
        
    return app_scaffold(TaskView(page), selected_tab="Tasks", page=page, top_bar_title=custom_title)
