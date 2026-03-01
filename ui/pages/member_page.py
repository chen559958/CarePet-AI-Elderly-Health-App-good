from __future__ import annotations
import flet as ft
from datetime import datetime
from ui.components.app_scaffold import app_scaffold
from ui.viewmodels.member_viewmodel import MemberViewModel
from app.container import Container
from ui.styles import colors
import asyncio

class MemberView(ft.Container):
    def __init__(self, page: ft.Page, on_logout):
        super().__init__(expand=True)
        self.page = page
        self.on_logout_click = on_logout
        self.container = Container.get_instance()
        self.vm = MemberViewModel(self.container)
        self.title_ref = ft.Ref[ft.Text]()
        
        self.profile = None
        self.drugs = []
        self.is_loading = True
        self.main_container = self # MemberView is the container
        
        # 狀態變數
        self.is_editing_profile = False
        self.is_editing_drugs = False
        
        # UI 元件
        self.drug_list_container = ft.Column(spacing=10)
        self.date_picker = None

        # Initial UI sync
        self._sync_ui()


    def did_mount(self):
        self.page.run_task(self._init_data)

    async def _init_data(self):
        try:
            # 1. 載入資料
            self.profile = await asyncio.to_thread(self.vm.load_profile)
            self.drugs = await asyncio.to_thread(self.vm.load_drugs)
            
            # 2. 獲取寵物資訊
            user = self.container.auth_service.get_current_user()
            pet = await self.container.pet_repo.get_pet(user.id) if user else None
            pet_name = pet.pet_name if pet else "寵物"
            
            self.is_loading = False
            
            # 3. 建立 UI
            self._sync_ui()
            self.refresh_drug_list()
            self.update()
            
            if self.title_ref.current:
                self.title_ref.current.value = f"回到{pet_name}身邊"
                self.title_ref.current.update()
                
        except Exception as e:
            print(f"Error loading member data: {e}")
            import traceback
            traceback.print_exc()
            self.is_loading = False
            self._sync_ui()
            self.update()

    def set_field_style(self, field: ft.TextField, editing: bool):
        field.read_only = not editing
        field.border = ft.InputBorder.OUTLINE if editing else ft.InputBorder.NONE
        field.bgcolor = ft.colors.WHITE if editing else ft.colors.TRANSPARENT
        field.label_style = ft.TextStyle(color=colors.PRIMARY if editing else colors.TEXT_SECONDARY)

    def refresh_drug_list(self):
        self.drug_list_container.controls.clear()
        win_w = self.page.window.width if self.page.window.width else 450
        scale_ratio = min(1.0, max(0.0, (win_w - 400) / 600))
        name_size = 14 + (6 * scale_ratio)
        info_size = 12 + (6 * scale_ratio)

        async def on_drug_card_click(drug_id):
            if self.is_editing_drugs:
                self.page.go(f"/add_drug?drug_id={drug_id}")
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text("請先點擊右側的編輯按鈕以進行修改設定"), action="好")
                self.page.snack_bar.open = True
                self.page.update()

        async def delete_drug_confirmed(drug_id):
            async def do_delete(e):
                await self.vm.delete_drug(drug_id)
                self.page.dialog.open = False
                self.page.snack_bar = ft.SnackBar(ft.Text("已刪除藥品"))
                self.page.snack_bar.open = True
                self.drugs = await asyncio.to_thread(self.vm.load_drugs)
                self.refresh_drug_list()
                self.page.update()

            self.page.dialog = ft.AlertDialog(
                title=ft.Text("確定刪除？"),
                content=ft.Text("刪除後將無法恢復此藥品的紀錄連動。"),
                actions=[
                    ft.TextButton("確定刪除", on_click=do_delete, icon=ft.icons.DELETE, icon_color=ft.colors.ERROR_CONTAINER),
                    ft.TextButton("取消", on_click=lambda _: (setattr(self.page.dialog, "open", False), self.page.update())),
                ],
                actions_alignment="center",
            )
            self.page.dialog.open = True
            self.page.update()

        if not self.drugs:
            self.drug_list_container.controls.append(ft.Text("尚未登錄任何藥品", color=colors.TEXT_SECONDARY, italic=True))
        else:
            for drug in self.drugs:
                meal_periods = [p for p in drug.intake_periods if p in ["breakfast", "lunch", "dinner"]]
                has_sleep = "sleep" in drug.intake_periods
                meal_order = ["breakfast", "lunch", "dinner"]
                sorted_meals = sorted(meal_periods, key=lambda x: meal_order.index(x))
                if len(sorted_meals) == 3: meal_str = "三餐"
                elif len(sorted_meals) == 1: meal_str = {"breakfast": "早餐", "lunch": "中餐", "dinner": "晚餐"}[sorted_meals[0]]
                elif len(sorted_meals) == 2: meal_str = "".join([{"breakfast": "早", "lunch": "中", "dinner": "晚"}[p] for p in sorted_meals])
                else: meal_str = ""
                sleep_str = "睡前" if has_sleep else ""
                period_str = f"{meal_str} {sleep_str}".strip() if meal_str and sleep_str else f"{meal_str}{sleep_str}"
                timing_str = {"before_meal": "飯前", "after_meal": "飯後", "anytime": "不限"}.get(drug.intake_timing, "") if not (len(drug.intake_periods) == 1 and drug.intake_periods[0] == "sleep") else ""
                pills_str = f"{drug.pills_per_intake:g}"
                
                self.drug_list_container.controls.append(
                    ft.Container(
                        width=float("inf"), padding=12, bgcolor=colors.WHITE, border_radius=12,
                        border=ft.border.all(1, ft.colors.with_opacity(0.08, colors.PRIMARY)), ink=True,
                        on_click=lambda e, did=drug.id: self.page.run_task(on_drug_card_click, did),
                        content=ft.Row([
                            ft.Container(expand=2, content=ft.Text(drug.drug_name, size=name_size, weight="w600", color=colors.TEXT_PRIMARY, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)),
                            ft.Container(expand=2, content=ft.Text(f"{period_str} {timing_str}", size=info_size, color=ft.colors.with_opacity(0.75, colors.TEXT_SECONDARY))),
                            ft.Container(expand=1, alignment=ft.alignment.center_right, content=ft.Text(f"{pills_str}顆", size=info_size, weight="w600", color=colors.TEXT_PRIMARY)),
                            ft.IconButton(icon=ft.icons.DELETE_OUTLINE, icon_color=ft.colors.ERROR, visible=self.is_editing_drugs, on_click=lambda e, did=drug.id: self.page.run_task(delete_drug_confirmed, did)),
                        ])
                    )
                )
        self.update()

    def _sync_ui(self):

        if self.is_loading:
            self.main_container.content = ft.Container(content=ft.ProgressRing(), alignment=ft.alignment.center, expand=True)
            return

        self.page.locale = "zh_TW"
        self.date_picker = ft.DatePicker(
            first_date=datetime(1900, 1, 1), last_date=datetime.now(),
            on_change=lambda e: (setattr(self.birthday_field, "value", e.control.value.strftime('%Y-%m-%d')), self.update()) if e.control.value else None
        )
        self.page.overlay[:] = [c for c in self.page.overlay if not isinstance(c, ft.DatePicker)]
        self.page.overlay.append(self.date_picker)

        self.name_field = ft.TextField(label="您的名字", value=self.profile.name, color=colors.TEXT_PRIMARY)
        self.birthday_field = ft.TextField(label="您的生日", value=self.profile.birthday or "", color=colors.TEXT_PRIMARY, read_only=True, suffix=ft.Icon(ft.icons.CALENDAR_TODAY))
        self.birthday_overlay = ft.Container(bgcolor=ft.colors.TRANSPARENT, on_click=lambda _: self.date_picker.pick_date(), visible=False, left=0, top=0, right=0, bottom=0)
        self.birthday_stack = ft.Stack([self.birthday_field, self.birthday_overlay], width=float("inf"))
        
        self.breakfast_field = ft.TextField(label="早餐", value=self.profile.breakfast_time, color=colors.TEXT_PRIMARY)
        self.lunch_field = ft.TextField(label="午餐", value=self.profile.lunch_time, color=colors.TEXT_PRIMARY)
        self.dinner_field = ft.TextField(label="晚餐", value=self.profile.dinner_time, color=colors.TEXT_PRIMARY)
        self.sleep_time_field = ft.TextField(label="睡前", value=self.profile.sleep_time, color=colors.TEXT_PRIMARY)
        
        fields = [self.name_field, self.birthday_field, self.breakfast_field, self.lunch_field, self.dinner_field, self.sleep_time_field]
        for f in fields: self.set_field_style(f, False)

        async def toggle_profile_edit(e):
            if self.is_editing_profile:
                try:
                    self.profile.name = self.name_field.value
                    self.profile.birthday = self.birthday_field.value
                    self.profile.breakfast_time = self.breakfast_field.value
                    self.profile.lunch_time = self.lunch_field.value
                    self.profile.dinner_time = self.dinner_field.value
                    self.profile.sleep_time = self.sleep_time_field.value
                    await self.vm.save_profile(self.profile)
                    self.page.snack_bar = ft.SnackBar(ft.Text("✅ 設定儲存成功！"), bgcolor=colors.SUCCESS, open=True)
                except Exception as ex:
                    self.page.snack_bar = ft.SnackBar(ft.Text(f"❌ 儲存失敗: {ex}"), bgcolor=ft.colors.ERROR, open=True)
                    return
            self.is_editing_profile = not self.is_editing_profile
            edit_profile_btn.text = "存檔" if self.is_editing_profile else "編輯"
            edit_profile_btn.icon = ft.icons.SAVE if self.is_editing_profile else ft.icons.EDIT
            for f in fields: self.set_field_style(f, self.is_editing_profile)
            self.birthday_overlay.visible = self.is_editing_profile
            self.update()

        async def toggle_drug_edit(e):
            self.is_editing_drugs = not self.is_editing_drugs
            edit_drug_btn.text = "完成" if self.is_editing_drugs else "編輯"
            edit_drug_btn.icon = ft.icons.CHECK if self.is_editing_drugs else ft.icons.EDIT
            self.refresh_drug_list()

        edit_profile_btn = ft.TextButton("編輯", icon=ft.icons.EDIT, on_click=lambda e: self.page.run_task(toggle_profile_edit, e))
        edit_drug_btn = ft.TextButton("編輯", icon=ft.icons.EDIT, on_click=lambda e: self.page.run_task(toggle_drug_edit, e))

        self.main_container.content = ft.Column([
            ft.Row([ft.Text("個人設定與偏好", size=24, color=colors.TEXT_PRIMARY, weight="bold"), edit_profile_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(height=1, color=colors.PRIMARY),
            self.name_field, self.birthday_stack,
            ft.Row([ft.Column([self.breakfast_field], expand=True), ft.Column([self.lunch_field], expand=True)]),
            ft.Row([ft.Column([self.dinner_field], expand=True), ft.Column([self.sleep_time_field], expand=True)]),
            ft.Container(height=20),
            ft.Row([ft.Text("已登錄藥品", size=24, color=colors.TEXT_PRIMARY, weight="bold"), edit_drug_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(height=1, color="#EADEB8"),
            self.drug_list_container,
            ft.Container(height=30),
            ft.Row([ft.ElevatedButton("登出系統", on_click=self.on_logout_click, bgcolor=colors.TEXT_PRIMARY, color=colors.WHITE)], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=20),
        ], spacing=20, scroll=ft.ScrollMode.AUTO, expand=True)

async def build_member(page: ft.Page, on_logout) -> ft.Control:
    view = MemberView(page, on_logout)
    return app_scaffold(view, selected_tab="Member", page=page, title_ref=view.title_ref, top_bar_title="設定")
