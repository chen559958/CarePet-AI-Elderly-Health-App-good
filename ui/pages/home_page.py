from __future__ import annotations
import os
import flet as ft
from app.container import Container
from ui.components.app_scaffold import app_scaffold
from ui.components.pet_panel import pet_panel
from ui.viewmodels.home_viewmodel import HomeViewModel
from ui.styles import colors
from domain.models import PetState
from domain.watcher import reminder_watcher, pet_watcher
import urllib.parse
import asyncio

class HomeView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.page_ref = page
        self.container = Container.get_instance()
        self.vm = HomeViewModel(self.container)
        self.pet = None
        self.can_graduate = False
        self.item_animation_widget = None
        self.auto_refresh_task_handle = None
        self._subscription_reminders = None
        self._subscription_pet = None
        self.data = {}
        self.is_loading = True
        self.fetch_error = False
        self._fetching_lock = asyncio.Lock()
        self.main_container = self # HomeView itself is the container
        
        # Parse Query Params
        self.query_params = {}
        if page.route and "?" in page.route:
            try:
                query_string = page.route.split("?", 1)[1]
                self.query_params = dict(urllib.parse.parse_qsl(query_string))
            except Exception:
                pass
        
        self.used_item_id = self.query_params.get("used_item_id")
        self.item_category = self.query_params.get("item_category", "").lower()
        self.item_image = self.query_params.get("item_image", "")
        self.show_reward = self.query_params.get("show_reward") == "1"

        # Initial content update
        self._update_content()


    def _update_content(self):
        """決定的 UI 內容轉換"""
        print(f">>> DEBUG: HomeView: _update_content() 被呼叫。is_loading={self.is_loading}, pet={self.pet}")
        try:

            if self.is_loading:
                self.main_container.content = ft.Container(expand=True, alignment=ft.alignment.center, content=ft.ProgressRing())
                return
            
            if self.pet is None:
                self.main_container.content = ft.Container(
                    expand=True,
                    alignment=ft.alignment.center,
                    content=ft.Column([
                        ft.Icon(ft.icons.REPLAY_CIRCLE_FILLED, size=50, color=colors.PRIMARY),
                        ft.Text("資料讀取失敗或尚未初始化", size=16, color=colors.TEXT_SECONDARY),
                        ft.ElevatedButton("重試", on_click=lambda _: self.page.run_task(self._load_data, True))
                    ], horizontal_alignment="center", spacing=20)
                )
                return

            self.item_animation_widget = None
            if self.used_item_id and self.item_image:
                 img_src = ("/" + self.item_image.replace("assets/", ""))
                 animatable_img = ft.Container(content=ft.Image(src=img_src, width=80, height=80, fit=ft.ImageFit.CONTAIN), width=80, height=80, rotate=ft.transform.Rotate(0, alignment=ft.alignment.center), animate_rotation=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT))
                 item_img_container = ft.Container(content=animatable_img, visible=True, top=0, left=0, right=0, bottom=0, alignment=ft.alignment.top_center, offset=ft.transform.Offset(0, -1.0), animate_offset=ft.animation.Animation(800, ft.AnimationCurve.EASE_OUT), animate_scale=ft.animation.Animation(500, ft.AnimationCurve.EASE_OUT), scale=1.0)
                 async def play_animation():
                     while not item_img_container.page: await asyncio.sleep(0.1)
                     await asyncio.sleep(0.3)
                     item_img_container.scale = 1.2
                     item_img_container.offset = ft.transform.Offset(-0.35, 0.65) if self.item_category == "foods" else ft.transform.Offset(0.235, 0.85)
                     self.update()
                     await asyncio.sleep(0.8)
                     animatable_img.rotate.angle = -2.356 if self.item_category == "foods" else 0
                     self.update()
                     await asyncio.sleep(0.4)
                     for _ in range(3):
                         animatable_img.rotate.angle -= 0.087; self.update(); await asyncio.sleep(0.1)
                         animatable_img.rotate.angle += 0.087; self.update(); await asyncio.sleep(0.1)
                     await asyncio.sleep(0.5)
                     self.page.go("/")
                 self.vm._create_task(play_animation())
                 self.item_animation_widget = item_img_container

            self.main_container.content = ft.Container(
                expand=True,
                image_src="background.png",
                image_fit=ft.ImageFit.COVER,
                bgcolor=colors.BACKGROUND,
                content=ft.Column([
                    pet_panel(
                        pet_name=self.pet.pet_name,
                        level=self.pet.level,
                        exp=self.pet.exp,
                        mood=self.pet.mood,
                        stamina=self.pet.stamina,
                        image_path=self.pet.image_path,
                        page=self.page_ref,
                        on_bowl_click=self.on_bowl_click,
                        on_pet_click=self.on_pet_click,
                        item_animation_widget=self.item_animation_widget,
                        reward_trigger=self.show_reward,
                    ),
                ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
            )
        except Exception as e:
            print(f"ERROR: HomeView._update_content CRASHED: {e}")
            import traceback
            traceback.print_exc()
            self.main_container.content = ft.Text(f"渲染錯誤: {e}", color="red")

async def build_home(page: ft.Page, padding: int = 0) -> ft.Control:
    return app_scaffold(HomeView(page), selected_tab="Home", page=page, padding=0)
