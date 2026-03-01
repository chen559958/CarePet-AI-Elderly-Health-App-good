from __future__ import annotations
import flet as ft
from ui.components.app_scaffold import app_scaffold
from app.container import Container
from ui.styles import colors
from ui.viewmodels.gallery_viewmodel import GalleryViewModel

class GalleryView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.page = page
        self.container = Container.get_instance()
        self.vm = GalleryViewModel(self.container)
        self.title_ref = ft.Ref[ft.Text]()
        self.items = []
        self.is_loading = True
        self.main_container = self # GalleryView is the container
        
        # Initial UI sync
        self._sync_ui()


    def _sync_ui(self):
        if self.is_loading:
            self.main_container.content = ft.Container(
                content=ft.ProgressRing(),
                alignment=ft.alignment.center,
                expand=True
            )
            return

        def gallery_item_card(item):
            name = item["name"]
            img_src = item["image_path"] 
            if img_src and img_src.startswith("assets/"):
                img_src = "/" + img_src.replace("assets/", "")
            elif img_src and not img_src.startswith("/"):
                img_src = "/" + img_src
            
            is_unlocked = item["is_unlocked"]

            return ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Image(
                            src=img_src, fit=ft.ImageFit.CONTAIN,
                            color=ft.colors.BLACK if not is_unlocked else None,
                            color_blend_mode=ft.BlendMode.SRC_IN if not is_unlocked else None,
                        ),
                        height=140, width=140, padding=15, bgcolor=colors.BACKGROUND, border_radius=10, alignment=ft.alignment.center,
                    ),
                    ft.Text(name if is_unlocked else "", size=16, color=colors.TEXT_PRIMARY, weight="bold", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                padding=10, width=160, height=220, bgcolor=colors.WHITE, border_radius=15, border=ft.border.all(1, colors.PRIMARY),
            )

        grid = ft.GridView(expand=True, runs_count=0, max_extent=180, child_aspect_ratio=0.7, spacing=10, run_spacing=10, padding=10)
        
        if not self.items:
            grid_content = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.HISTORY_EDU, size=60, color=colors.TEXT_SECONDARY),
                    ft.Text("目前還沒有畢業的寵物喔", size=16, color=colors.TEXT_SECONDARY),
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center, expand=True
            )
        else:
            for item in self.items:
                grid.controls.append(gallery_item_card(item))
            grid_content = ft.Container(content=grid, expand=True)

        self.main_container.content = ft.Column([
            ft.Text("寵物圖鑑", size=24, color=colors.TEXT_PRIMARY, weight="bold"),
            ft.Divider(height=1, color=colors.PRIMARY),
            grid_content,
        ], spacing=10, expand=True)

async def build_gallery(page: ft.Page) -> ft.Control:
    view = GalleryView(page)
    return app_scaffold(view, selected_tab="Gallery", page=page, title_ref=view.title_ref, top_bar_title="圖鑑")
