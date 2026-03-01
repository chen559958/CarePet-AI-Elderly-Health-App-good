from __future__ import annotations
import asyncio
import flet as ft
from ui.components.app_scaffold import app_scaffold
from ui.viewmodels.add_drug_viewmodel import AddDrugViewModel
from app.container import Container
from ui.styles import colors
import urllib.parse

class AddDrugView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.page = page
        self.container = Container.get_instance()
        self.vm = AddDrugViewModel(self.container)
        self.title_ref = ft.Ref[ft.Text]()
        
        self.drug_id = None
        self.is_edit_mode = False
        self.drug_data = None
        self.is_loading = True
        self.main_container = self # AddDrugView is the container
        
        # UI 元件
        self.name_field = ft.TextField(label="藥品名稱 (必填)", color="#7E584A", border_color="#EADEB8")
        self.usage_group = ft.RadioGroup(content=ft.Row([ft.Radio(value="吸入", label="吸入"), ft.Radio(value="口服", label="口服"), ft.Radio(value="外敷", label="外敷")]))
        self.usage_group.value = "口服"
        self.timing_state = {"value": "after_meal"}
        self.breakfast_cb = ft.Checkbox(label="早", value=True)
        self.lunch_cb = ft.Checkbox(label="中", value=False)
        self.dinner_cb = ft.Checkbox(label="晚", value=False)
        self.sleep_cb = ft.Checkbox(label="睡前", value=False)
        self.pills_idx = {"val": 1}
        self.PILL_VALUES = [0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        self.pills_val_text = ft.Text("1 顆", size=20, weight="bold", color="#7E584A", width=80, text_align=ft.TextAlign.CENTER)
        self.hospital_field = ft.TextField(label="醫院 (選填)", color="#7E584A", border_color="#EADEB8")
        self.doctor_field = ft.TextField(label="醫生 (選填)", color="#7E584A", border_color="#EADEB8")
        self.department_field = ft.TextField(label="科別 (選填)", color="#7E584A", border_color="#EADEB8")
        self.dlg_status = ft.Text("", color="#7E584A", italic=True)
        
        # 提前初始化 file_picker
        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        self._file_picker_added = False

        # Initial UI sync
        self._sync_ui()


    def did_mount(self):
        print("DEBUG: AddDrugView.did_mount() called")
        # 立即加入 file_picker 到 overlay
        if not self._file_picker_added:
            self.page.overlay.append(self.file_picker)
            self._file_picker_added = True
        self.page.run_task(self._init_data)

    async def _init_data(self):
        print("DEBUG: AddDrugView._init_data() started")
        try:
            # 解析參數
            query_params = {}
            if "?" in self.page.route:
                query_str = self.page.route.split("?")[1]
                query_params = dict(urllib.parse.parse_qsl(query_str))
            
            drug_id_str = query_params.get("drug_id")
            self.drug_id = int(drug_id_str) if drug_id_str else None
            self.is_edit_mode = self.drug_id is not None
            
            if self.is_edit_mode:
                self.drug_data = await asyncio.to_thread(self.vm.get_drug, self.drug_id)
            
            user = self.container.auth_service.get_current_user()
            pet = await self.container.pet_repo.get_pet(user.id) if user else None
            pet_name = pet.pet_name if pet else "寵物"
            
            print(f"DEBUG: AddDrugView setting is_loading=False")
            self.is_loading = False
            # 觸發 UI 更新
            self._sync_ui()
            self.update()
            print(f"DEBUG: AddDrugView.update() called, is_loading={self.is_loading}")
            
            if self.title_ref.current:
                self.title_ref.current.value = f"幫{pet_name}修改藥藥資訊" if self.is_edit_mode else f"幫{pet_name}記下新的藥藥吧"
                self.title_ref.current.update()
            
            # 初始化欄位 - 只在編輯模式且 UI 已建立後執行
            if self.is_edit_mode and self.drug_data:
                # 等待 UI 元件建立完成
                await asyncio.sleep(0.1)
                
                self.name_field.value = self.drug_data.drug_name
                self.usage_group.value = self.drug_data.usage_method
                self.timing_state["value"] = self.drug_data.intake_timing
                self.breakfast_cb.value = "breakfast" in self.drug_data.intake_periods
                self.lunch_cb.value = "lunch" in self.drug_data.intake_periods
                self.dinner_cb.value = "dinner" in self.drug_data.intake_periods
                self.sleep_cb.value = "sleep" in self.drug_data.intake_periods
                self.hospital_field.value = self.drug_data.hospital
                self.doctor_field.value = self.drug_data.doctor
                self.department_field.value = self.drug_data.department
                
                pills_float = float(self.drug_data.pills_per_intake)
                self.pills_idx["val"] = min(range(len(self.PILL_VALUES)), key=lambda i: abs(self.PILL_VALUES[i] - pills_float))
                self.update_pills_ui()
                self.update_timing_ui()
            
            await self.check_auto_run()
            print("DEBUG: AddDrugView._init_data() completed")
            
        except Exception as e:
            print(f"Error loading add_drug data: {e}")
            import traceback
            traceback.print_exc()
            self.is_loading = False
            self.update()

    def update_timing_ui(self):
        is_after = self.timing_state["value"] == "after_meal"
        self.timing_aft_btn.bgcolor = "#7E584A" if is_after else "grey"
        self.timing_bef_btn.bgcolor = "#7E584A" if not is_after else "grey"
        self.update()

    def update_pills_ui(self):
        val = self.PILL_VALUES[self.pills_idx["val"]]
        self.pills_val_text.value = f"{val:g} 顆"
        self.minus_btn.disabled = self.pills_idx["val"] <= 0
        self.plus_btn.disabled = self.pills_idx["val"] >= len(self.PILL_VALUES) - 1
        self.update()

    async def check_auto_run(self):
        await asyncio.sleep(0.3)
        mode = None
        if hasattr(self.page, 'data') and self.page.data and "add_drug_mode" in self.page.data:
            mode = self.page.data.get("add_drug_mode")
            self.page.data["add_drug_mode"] = None
        
        if mode == "camera": await self.run_camera_scan()
        elif mode == "upload": await self.run_upload()
        elif not mode and not self.is_edit_mode:
            self.show_mode_selector()

    def show_mode_selector(self):
        def select_mode(m):
            dlg.open = False
            self.page.update()
            if m == "camera": self.page.run_task(self.run_camera_scan)
            elif m == "upload": self.page.run_task(self.run_upload)

        def create_btn(icon, text, color, m):
            return ft.Container(content=ft.Column([ft.Icon(icon, size=30, color=color), ft.Text(text, size=12, weight="bold")], alignment="center"), bgcolor=colors.WHITE, padding=10, border_radius=8, border=ft.border.all(1, colors.PRIMARY), on_click=lambda _: select_mode(m), ink=True, width=80, height=80)

        dlg = ft.AlertDialog(title=ft.Text("選擇新增方式", weight="bold"), content=ft.Column([ft.Text("您想如何輸入藥品資訊？"), ft.Row([create_btn(ft.icons.CAMERA_ALT, "拍照辨識", colors.SECONDARY, "camera"), create_btn(ft.icons.UPLOAD_FILE, "上傳照片", ft.colors.GREEN, "upload"), create_btn(ft.icons.EDIT, "手動輸入", colors.PRIMARY, None)], alignment="center")], tight=True, spacing=20))
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    async def run_camera_scan(self):
        self.dlg_status.value = "相機功能尚未實作，請使用上傳照片功能"
        self.update()

    async def run_upload(self):
        self.file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE)

    async def on_file_picked(self, e: ft.FilePickerResultEvent):
        if not e.files: return
        self.dlg_status.value = "AI 正在辨識藥袋內容..."
        self.update()
        try:
            results = await self.vm.scan_medication(e.files[0].path)
            if results:
                result = results[0]
                self.name_field.value = result.name
                self.timing_state["value"] = result.timing
                self.breakfast_cb.value = "breakfast" in result.periods
                self.lunch_cb.value = "lunch" in result.periods
                self.dinner_cb.value = "dinner" in result.periods
                self.sleep_cb.value = "sleep" in result.periods
                p_val = float(result.pills_per_intake)
                self.pills_idx["val"] = min(range(len(self.PILL_VALUES)), key=lambda i: abs(self.PILL_VALUES[i] - p_val))
                self.hospital_field.value = result.hospital
                self.doctor_field.value = result.doctor
                self.department_field.value = result.department
                self.dlg_status.value = "辨識成功!"
                self.update_pills_ui(); self.update_timing_ui()
            else: self.dlg_status.value = "辨識失敗，請手動輸入"
        except Exception as ex: self.dlg_status.value = f"辨識錯誤: {ex}"
        self.update()

    def _sync_ui(self):
        print(f"DEBUG: AddDrugView._sync_ui() called, is_loading={self.is_loading}")
        if self.is_loading:
            self.main_container.content = ft.Container(content=ft.ProgressRing(), alignment=ft.alignment.center, expand=True)
            return

        self.timing_bef_btn = ft.Container(content=ft.Text("餐前", color="white"), bgcolor="grey", padding=10, border_radius=5, on_click=lambda _: (setattr(self.timing_state, "value", "before_meal"), self.update_timing_ui()), ink=True)
        self.timing_aft_btn = ft.Container(content=ft.Text("餐後", color="white"), bgcolor="#7E584A", padding=10, border_radius=5, on_click=lambda _: (setattr(self.timing_state, "value", "after_meal"), self.update_timing_ui()), ink=True)
        self.minus_btn = ft.IconButton(ft.icons.REMOVE_CIRCLE_OUTLINE, colors.PRIMARY, 32, on_click=lambda _: (setattr(self.pills_idx, "val", max(0, self.pills_idx["val"]-1)), self.update_pills_ui()))
        self.plus_btn = ft.IconButton(ft.icons.ADD_CIRCLE_OUTLINE, colors.PRIMARY, 32, on_click=lambda _: (setattr(self.pills_idx, "val", min(len(self.PILL_VALUES)-1, self.pills_idx["val"]+1)), self.update_pills_ui()))

        async def on_save(_):
            periods = []
            if self.breakfast_cb.value: periods.append("breakfast")
            if self.lunch_cb.value: periods.append("lunch")
            if self.dinner_cb.value: periods.append("dinner")
            if self.sleep_cb.value: periods.append("sleep")
            if not self.name_field.value:
                self.page.snack_bar = ft.SnackBar(ft.Text("請輸入藥品名稱!"), open=True); self.page.update(); return
            
            args = {"name": self.name_field.value, "periods": periods, "timing": self.timing_state["value"], "pills": self.PILL_VALUES[self.pills_idx["val"]], "usage_method": self.usage_group.value, "hospital": self.hospital_field.value, "doctor": self.doctor_field.value, "department": self.department_field.value}
            if self.is_edit_mode: success = await asyncio.to_thread(self.vm.update_medication, drug_id=self.drug_id, **args)
            else: success = await asyncio.to_thread(self.vm.add_medication, **args)
            
            if success:
                self.page.snack_bar = ft.SnackBar(ft.Text("藥品儲存成功!"), open=True); self.page.update(); self.page.go("/member")

        self.main_container.content = ft.Column([
            ft.Text("編輯藥品" if self.is_edit_mode else "新增藥品", size=24, color=colors.TEXT_PRIMARY, weight="bold"),
            ft.Divider(height=1, color=colors.PRIMARY),
            ft.Row([self.dlg_status], alignment="center"),
            ft.Text("必填資訊", size=16, color="#F7A89A", weight="bold"),
            self.name_field, ft.Text("用法"), self.usage_group, ft.Text("時間"),
            ft.Row([self.timing_bef_btn, self.timing_aft_btn]),
            ft.Row([self.breakfast_cb, self.lunch_cb, self.dinner_cb, self.sleep_cb]),
            ft.Text("顆數"), ft.Row([self.minus_btn, self.pills_val_text, self.plus_btn], alignment="center"),
            ft.Divider(height=20, color="#EADEB8"),
            ft.Text("選填資訊", size=16, color="grey", weight="bold"),
            self.hospital_field, self.doctor_field, self.department_field,
            ft.Row([ft.Container(content=ft.Text("儲存", color="white", weight="bold"), bgcolor=colors.SECONDARY, padding=ft.padding.symmetric(horizontal=40, vertical=15), border_radius=10, on_click=on_save, ink=True)], alignment="center"),
        ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

async def build_add_drug(page: ft.Page) -> ft.Control:
    view = AddDrugView(page)
    return app_scaffold(view, selected_tab="Home", page=page, title_ref=view.title_ref, top_bar_title="新增藥品")
