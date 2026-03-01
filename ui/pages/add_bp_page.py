from __future__ import annotations
import asyncio
import flet as ft
from ui.components.app_scaffold import app_scaffold
from ui.viewmodels.add_bp_viewmodel import AddBPViewModel
from app.container import Container
from ui.styles import colors

class AddBPView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.page = page
        self.container = Container.get_instance()
        self.vm = AddBPViewModel(self.container)
        self.title_ref = ft.Ref[ft.Text]()
        
        self.is_loading = True
        self.systolic_field = ft.TextField(label="收縮壓 (SYS)", hint_text="例如: 120", keyboard_type=ft.KeyboardType.NUMBER, color=colors.TEXT_PRIMARY, border_color=colors.PRIMARY)
        self.diastolic_field = ft.TextField(label="舒張壓 (DIA)", hint_text="例如: 80", keyboard_type=ft.KeyboardType.NUMBER, color=colors.TEXT_PRIMARY, border_color=colors.PRIMARY)
        self.pulse_field = ft.TextField(label="脈搏 (選填)", hint_text="例如：72", keyboard_type=ft.KeyboardType.NUMBER, color=colors.TEXT_PRIMARY, border_color=colors.PRIMARY)
        self.dlg_status = ft.Text("", color=colors.TEXT_PRIMARY, italic=True)
        self.save_btn = None
        self.main_container = self  # AddBPView is the container

        # Initial UI sync
        self._sync_ui()


    def did_mount(self):
        self.page.run_task(self._init_data)

    async def _init_data(self):
        try:
            user = self.container.auth_service.get_current_user()
            pet = await self.container.pet_repo.get_pet(user.id) if user else None
            pet_name = pet.pet_name if pet else "寵物"
            
            self.is_loading = False
            self._sync_ui()  # Update UI content
            self.update()
            
            if self.title_ref.current:
                self.title_ref.current.value = f"幫{pet_name}量血壓吧"
                self.title_ref.current.update()
            
            await self.check_auto_run()
        except Exception as e:
            print(f"Error loading add_bp data: {e}")
            self.is_loading = False
            self._sync_ui()
            self.update()

    async def check_auto_run(self):
        await asyncio.sleep(0.3)
        def select_mode(m):
            dlg.open = False
            self.page.update()
            if m == "camera": self.page.run_task(self.run_camera_scan)
            elif m == "upload": self.page.run_task(self.run_upload)

        def create_btn(icon, text, color, m):
            return ft.Container(content=ft.Column([ft.Icon(icon, size=30, color=color), ft.Text(text, size=12, weight="bold")], alignment="center"), bgcolor=colors.WHITE, padding=10, border_radius=8, border=ft.border.all(1, colors.PRIMARY), on_click=lambda _: select_mode(m), ink=True, width=80, height=80)

        dlg = ft.AlertDialog(title=ft.Text("選擇量測方式", weight="bold"), content=ft.Column([ft.Text("您想如何輸入血壓數據？"), ft.Row([create_btn(ft.icons.CAMERA_ALT, "拍照辨識", colors.SECONDARY, "camera"), create_btn(ft.icons.UPLOAD_FILE, "上傳照片", ft.colors.GREEN, "upload"), create_btn(ft.icons.EDIT, "手動輸入", colors.PRIMARY, None)], alignment="center")], tight=True, spacing=20))
        self.page.overlay.clear()
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    async def run_camera_scan(self):
        self.dlg_status.value = "AI 正在辨識血壓計..."
        self.update()
        await asyncio.sleep(1.5)
        result = await asyncio.to_thread(self.vm.scan_bp_report, "bp_cam.jpg")
        self.systolic_field.value, self.diastolic_field.value = str(result.systolic), str(result.diastolic)
        self.dlg_status.value = "辨識完成！"; self.update()

    async def run_upload(self):
        self.dlg_status.value = "正在處理照片..."
        self.update()
        await asyncio.sleep(1.5)
        result = await asyncio.to_thread(self.vm.scan_bp_report, "bp_upload.jpg")
        self.systolic_field.value, self.diastolic_field.value = str(result.systolic), str(result.diastolic)
        self.dlg_status.value = "照片辨識完成！"; self.update()

    def _sync_ui(self):

        if self.is_loading:
            self.main_container.content = ft.Container(content=ft.ProgressRing(), alignment=ft.alignment.center, expand=True)
            return

        async def on_save(_):
            if not self.systolic_field.value or not self.diastolic_field.value:
                self.page.snack_bar = ft.SnackBar(ft.Text("請輸入完整的血壓數值"), open=True); self.page.update(); return
            self.save_btn.disabled = True; self.update()
            try:
                success = await self.vm.save_bp(int(self.systolic_field.value), int(self.diastolic_field.value), int(self.pulse_field.value) if self.pulse_field.value else None)
                if success:
                    self.page.overlay.clear()
                    if not hasattr(self.page, "extra_data"): self.page.extra_data = {}
                    self.page.extra_data["task_recently_completed"] = True
                    self.page.snack_bar = ft.SnackBar(ft.Text("血壓紀錄已儲存！"), open=True)
                    self.page.go("/tasks")
                else: self.page.snack_bar = ft.SnackBar(ft.Text("儲存失敗"), open=True); self.save_btn.disabled = False
            except Exception as e: self.page.snack_bar = ft.SnackBar(ft.Text(f"錯誤: {e}"), open=True); self.save_btn.disabled = False
            self.update()

        self.save_btn = ft.Container(content=ft.Text("儲存紀錄", color="white", weight="bold"), bgcolor=colors.SECONDARY, padding=ft.padding.symmetric(horizontal=40, vertical=15), border_radius=10, on_click=lambda e: self.page.run_task(on_save, e), ink=True)

        self.main_container.content = ft.Column([
            ft.Text("血壓量測紀錄", size=24, color=colors.TEXT_PRIMARY, weight="bold"),
            ft.Divider(height=1, color=colors.PRIMARY),
            ft.Row([self.dlg_status], alignment="center"),
            ft.Text("血壓數值", size=16, weight="bold"),
            self.systolic_field, self.diastolic_field, self.pulse_field,
            ft.Row([self.save_btn], alignment="center"),
        ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)

async def build_add_bp(page: ft.Page) -> ft.Control:
    view = AddBPView(page)
    return app_scaffold(view, selected_tab="Tasks", page=page, title_ref=view.title_ref, top_bar_title="血壓")
