from __future__ import annotations
import flet as ft
from ui.components.app_scaffold import app_scaffold
from ui.viewmodels.records_viewmodel import RecordsViewModel
from app.container import Container
from ui.styles import colors
import math
import asyncio

class RecordsView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.page = page
        self.container = Container.get_instance()
        self.vm = RecordsViewModel(self.container)
        self.title_ref = ft.Ref[ft.Text]()
        
        self.stats = []
        self.bp_records = []
        self.is_loading = True
        self.main_container = self # RecordsView is the container
        
        # Initial UI sync
        self._sync_ui()


    def _sync_ui(self):
        if self.is_loading:
            self.main_container.content = ft.Container(content=ft.ProgressRing(), alignment=ft.alignment.center, expand=True)
            return

        win_w = self.page.window.width if self.page.window.width else 450
        res_chart_w = max(300, min(win_w - 60, 500)) if win_w > 400 else 300

        adherence_data = [(s["date"], s["percentage"]) for s in self.stats]
        adherence_chart = self.create_line_chart(adherence_data, colors.SUCCESS, chart_width=res_chart_w, chart_height=200, max_val=120, tooltip_suffix="%")

        bp_elements = []
        if self.bp_records:
            chart_width, chart_height, padding_x, max_val = res_chart_w, 200, 20, 220
            sys_points, dia_points = [], []
            for i, r in enumerate(self.bp_records):
                x = padding_x + (i * ((chart_width - 2 * padding_x) / (len(self.bp_records) - 1 if len(self.bp_records) > 1 else 1)))
                sys_y, dia_y = chart_height - (r["systolic"] / max_val * chart_height), chart_height - (r["diastolic"] / max_val * chart_height)
                sys_points.append((x, sys_y, r["date"], r["systolic"])); dia_points.append((x, dia_y, r["date"], r["diastolic"]))

            for grid_y in [60, 90, 120, 140, 180, 200]:
                y_pos = chart_height - (grid_y / max_val * chart_height)
                bp_elements.append(ft.Container(bgcolor="#f0f0f0", width=chart_width, height=1, top=y_pos, left=0))

            def draw_series(points, color, label):
                for i in range(len(points)):
                    cx, cy, date, val = points[i]
                    if i < len(points) - 1:
                        nx, ny, _, _ = points[i+1]
                        dist, angle = math.sqrt((nx-cx)**2 + (ny-cy)**2), math.atan2(ny-cy, nx-cx)
                        bp_elements.append(ft.Container(bgcolor=color, width=dist, height=2, top=cy, left=cx, rotate=ft.Rotate(angle, alignment=ft.Alignment(-1, 0))))
                    tl_text = f"{date} {label}: {val}" + (f"\nPulse: {self.bp_records[i]['pulse']}" if self.bp_records[i].get('pulse') else "")
                    bp_elements.append(ft.Container(width=6, height=6, bgcolor=color, border_radius=3, top=cy - 3, left=cx - 3, tooltip=tl_text))

            draw_series(sys_points, colors.SECONDARY, "Sys"); draw_series(dia_points, colors.PRIMARY, "Dia")
            for cx, _, date, _ in sys_points: bp_elements.append(ft.Container(content=ft.Text(date, size=10, color="grey"), top=chart_height + 5, left=cx - 15))

        bp_chart_content = ft.Container(content=ft.Stack(bp_elements), width=res_chart_w, height=250, padding=5) if self.bp_records else ft.Container(content=ft.Column([ft.Icon(ft.icons.QUERY_STATS, color="grey"), ft.Text("尚無週血壓紀錄", color="grey")], alignment="center"), width=res_chart_w, height=250, alignment=ft.alignment.center)

        ad_section = ft.Container(content=ft.Column([ft.Row([ft.Icon(ft.icons.SHOW_CHART, colors.SUCCESS), ft.Text("用藥達成率 (%)", size=16, weight="bold")]), ft.Container(adherence_chart, alignment=ft.alignment.center), ft.Row([ft.Row([ft.Container(width=10, height=10, bgcolor=colors.SUCCESS), ft.Text("達成率", size=12)], spacing=5)], alignment="center")], spacing=10), padding=15, bgcolor=colors.WHITE, border_radius=15, border=ft.border.all(1, colors.PRIMARY), height=360)
        bp_section = ft.Container(content=ft.Column([ft.Row([ft.Icon(ft.icons.FAVORITE, colors.SECONDARY), ft.Text("血壓趨勢 (mmHg)", size=16, weight="bold")]), ft.Container(bp_chart_content, alignment=ft.alignment.center), ft.Row([ft.Row([ft.Container(width=10, height=10, bgcolor=colors.SECONDARY), ft.Text("收縮壓", size=12)], spacing=5), ft.Row([ft.Container(width=10, height=10, bgcolor=colors.PRIMARY), ft.Text("舒張壓", size=12)], spacing=5)], alignment="center", spacing=20)], spacing=10), padding=15, bgcolor=colors.WHITE, border_radius=15, border=ft.border.all(1, colors.PRIMARY), height=360)

        record_list = ft.Column(spacing=10)
        for date_str, items in self.records.items():
            day_items = [ft.Container(padding=15, bgcolor=colors.WHITE, border=ft.border.only(bottom=ft.border.BorderSide(1, colors.PRIMARY)), content=ft.Column([ft.Row([ft.Column([ft.Text(item["drug_name"], size=18, weight="bold"), ft.Text(item.get("hospital", "一般藥品"), size=13, color="grey")], expand=True), ft.Container(content=ft.Text(f" {item['summary_label']} {item['summary_status']} ", color="white", weight="bold", size=12), bgcolor=item["summary_color"], padding=ft.padding.symmetric(horizontal=10, vertical=5), border_radius=5)], alignment="justify"), ft.Column([ft.Row([ft.Text(f"• {ink['planned_time']}", size=14, color=colors.TEXT_SECONDARY), ft.Text(ink["status_label"], size=12, color=ink["status_color"], weight="bold"), ft.Text(f"(執行: {ink['action_time']})", size=12, color="grey") if ink["action_time"] != "---" else ft.Container()], spacing=10) for ink in item["intakes"]], spacing=5)], spacing=10)) for item in items] if items else [ft.Text("當日無紀錄", color="grey", size=14)]
            day_col = ft.Column(day_items, visible=False, spacing=0)
            arr = ft.Icon(ft.icons.KEYBOARD_ARROW_DOWN, colors.TEXT_SECONDARY)
            record_list.controls.append(ft.Container(bgcolor=colors.WHITE, border_radius=12, border=ft.border.all(1, colors.PRIMARY), content=ft.Column([ft.Container(content=ft.Row([ft.Icon(ft.icons.CALENDAR_MONTH, colors.TEXT_PRIMARY), ft.Column([ft.Text(f"{date_str} 用藥史", size=18, weight="bold"), ft.Text(f"共 {len(items)} 筆紀錄", size=13) if items else ft.Text("尚無紀錄")], expand=True), arr], spacing=15), padding=15, on_click=lambda e, c=day_col, i=arr: (setattr(c, "visible", not c.visible), setattr(i, "name", ft.icons.KEYBOARD_ARROW_UP if c.visible else ft.icons.KEYBOARD_ARROW_DOWN), c.update(), i.update()), ink=True), ft.Container(day_col, padding=ft.padding.only(left=5, right=5, bottom=10))], spacing=0)))

        self.main_container.content = ft.Column([
            ft.Text("健康趨勢與紀錄", size=24, color=colors.TEXT_PRIMARY, weight="bold"),
            ft.ResponsiveRow([ft.Column([ad_section], col={"sm": 12, "md": 6}), ft.Column([bp_section], col={"sm": 12, "md": 6})], spacing=20, run_spacing=20),
            ft.Text("詳細用藥歷史", size=24, color=colors.TEXT_PRIMARY, weight="bold"),
            ft.Divider(height=1, color=colors.PRIMARY),
            record_list,
        ], spacing=20, scroll=ft.ScrollMode.AUTO, expand=True)

async def build_records(page: ft.Page) -> ft.Control:
    view = RecordsView(page)
    return app_scaffold(view, selected_tab="Records", page=page, title_ref=view.title_ref, top_bar_title="紀錄")
