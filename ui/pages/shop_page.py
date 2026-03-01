from __future__ import annotations
import flet as ft
from ui.components.app_scaffold import app_scaffold
from ui.viewmodels.shop_viewmodel import ShopViewModel
from app.container import Container
from ui.styles import colors
import asyncio

class ShopView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.page = page
        self.container = Container.get_instance()
        self.vm = ShopViewModel(self.container)
        self.title_ref = ft.Ref[ft.Text]()
        self.balance_value_stack = None
        self.item_grid = None
        self.data = None
        self.is_loading = True
        self.main_container = self # ShopView is the container
        
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
        
        if not self.data or "items" not in self.data:
            self.main_container.content = ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                content=ft.Column([
                    ft.Icon(ft.icons.SHOPPING_CART_OFF, size=50, color=colors.ERROR),
                    ft.Text("目前無法載入商店商品", size=16, color=colors.TEXT_SECONDARY),
                    ft.ElevatedButton("重試", on_click=lambda _: self.page.run_task(self._init_data))
                ], horizontal_alignment="center", spacing=20)
            )
            return

        # 這裡放置原本 build_shop 的佈局內容
        curr_width = self.page.window.width if self.page.window.width else 450
        title_size = min(28, max(18, 14 + curr_width * 0.015))
        balance_size = min(26, max(16, 12 + curr_width * 0.015))
        icon_size = min(32, max(20, 16 + curr_width * 0.02))

        shop_title_icon_inner = ft.Icon(ft.icons.STARS, color=colors.SECONDARY, size=icon_size)
        shop_title_icon_container = ft.Container(
            content=shop_title_icon_inner,
            bgcolor=ft.colors.WHITE,
            shape=ft.BoxShape.CIRCLE,
            padding=ft.padding.all(0.8),
            margin=ft.margin.only(top=3),
        )

        shop_title_text_stack = self.outlined_text("點數商城", title_size, colors.TEXT_PRIMARY)
        balance_label_stack = self.outlined_text("當前餘額:", balance_size, colors.TEXT_PRIMARY)
        self.balance_value_stack = self.outlined_text(f"{self.data['balance']} 點", balance_size, colors.SECONDARY)

        async def purchase(item, quantity):
            success, message = await self.vm.buy_item(item["id"], quantity=quantity)
            self.page.snack_bar = ft.SnackBar(ft.Text(message))
            self.page.snack_bar.open = True
            new_data = self.vm.load_shop_data()
            for ctrl in self.balance_value_stack.controls:
                ctrl.value = f"{new_data['balance']} 點"
            self.update()

        def show_purchase_dialog(item):
            qty = 1
            img_src = ("/" + item["image_path"].replace("assets/", "")) if item["image_path"] else None
            qty_text = ft.Text(str(qty), size=24, weight="bold")
            total_text = ft.Text(f"總計: {item['cost'] * qty} 點", size=20, color="#7E584A", weight="bold")

            def update_qty(delta):
                nonlocal qty
                qty = max(1, qty + delta)
                qty_text.value = str(qty)
                total_text.value = f"總計: {item['cost'] * qty} 點"
                self.page.update()

            def on_confirm(_):
                dialog.open = False
                self.page.update()
                self.page.run_task(purchase, item, qty)

            dialog = ft.AlertDialog(
                title=ft.Text("確認購買", size=24, weight="bold", color=colors.TEXT_PRIMARY),
                content=ft.Column([
                    ft.Container(
                        content=ft.Image(src=img_src, width=120, height=120, fit="contain") if img_src else ft.Icon(ft.icons.SHOPPING_BAG, size=70, color="grey"),
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Text(item["name"], size=22, weight="bold", text_align="center", color=colors.TEXT_PRIMARY),
                    ft.Text(f"單價: {item['cost']} 點", size=16, color=colors.TEXT_SECONDARY, text_align="center"),
                    ft.Divider(height=20, color="transparent"),
                    ft.Row([
                        ft.IconButton(ft.icons.REMOVE_CIRCLE_OUTLINE, on_click=lambda _: update_qty(-1), icon_color=colors.SECONDARY, icon_size=30),
                        qty_text,
                        ft.IconButton(ft.icons.ADD_CIRCLE_OUTLINE, on_click=lambda _: update_qty(1), icon_color=colors.SUCCESS, icon_size=30),
                    ], alignment="center", spacing=20),
                    total_text,
                ], tight=True, horizontal_alignment="center", spacing=10),
                actions=[
                    ft.TextButton("取消", on_click=lambda _: (setattr(dialog, "open", False), self.page.update())),
                    ft.ElevatedButton("確定購買", on_click=on_confirm, bgcolor=colors.SECONDARY, color=colors.WHITE),
                ],
                actions_alignment="center",
                open=True
            )
            self.page.overlay.append(dialog)
            self.page.update()

        def show_inventory_dialog(_):
            inventory = self.vm.load_inventory()
            
            async def on_use(item_id, use_dlg, inventory_dlg):
                use_dlg.open = False
                self.page.update()
                success, message, category = await self.vm.use_item(item_id)
                if success:
                    inventory_dlg.open = False
                    self.page.update()
                    # 直接獲取物品詳情用於 Jump 動畫
                    item = self.vm.shop_repo.get_item(item_id)
                    item_image = item.image_path if item else "assets/food.png"
                    self.page.go(f"/?used_item_id={item_id}&item_category={category}&item_image={item_image}")
                else:
                    self.page.snack_bar = ft.SnackBar(ft.Text(message), open=True)
                    self.page.update()

            def show_use_item_dialog(item, inventory_dlg):
                img_src = ("/" + item["image_path"].replace("assets/", "")) if item["image_path"] else None
                use_dlg = ft.AlertDialog(
                    title=ft.Text("使用物品", size=22, weight="bold", color=colors.TEXT_PRIMARY),
                    content=ft.Column([
                        ft.Container(
                            content=ft.Image(src=img_src, width=100, height=100, fit="contain") if img_src else ft.Icon(ft.icons.IMAGE, size=70, color="grey"),
                            alignment=ft.Alignment(0, 0),
                        ),
                        ft.Text(item["name"], size=20, weight="bold", text_align="center", color=colors.TEXT_PRIMARY),
                        ft.Text(f"持有數量: {item['quantity']}", size=14, color=colors.TEXT_SECONDARY, text_align="center"),
                    ], tight=True, horizontal_alignment="center", spacing=10),
                    actions=[
                        ft.TextButton("取消", on_click=lambda _: (setattr(use_dlg, "open", False), self.page.update())),
                        ft.ElevatedButton("使用", on_click=lambda _: self.page.run_task(on_use, item["item_id"], use_dlg, inventory_dlg), bgcolor=colors.SUCCESS, color=colors.WHITE),
                    ],
                    actions_alignment="center",
                    open=True
                )
                self.page.overlay.append(use_dlg)
                self.page.update()

            grid_items = []
            if not inventory:
                grid_items.append(ft.Text("背包空空的", color=colors.TEXT_SECONDARY))
            else:
                for item in inventory:
                    img_src = ("/" + item["image_path"].replace("assets/", "")) if item["image_path"] else None
                    grid_items.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Container(
                                    content=ft.Image(src=img_src, fit="contain") if img_src else ft.Icon(ft.icons.IMAGE),
                                    border=ft.border.all(1, colors.PRIMARY), border_radius=8, bgcolor=ft.colors.WHITE, height=115,
                                ),
                                ft.Text(f"x{item['quantity']}", weight="bold"),
                                ft.Text(item["name"], size=16, color=colors.TEXT_SECONDARY, max_lines=1),
                            ], spacing=5),
                            on_click=lambda e, i=item: show_use_item_dialog(i, inventory_dlg)
                        )
                    )

            inventory_grid = ft.GridView(controls=grid_items, runs_count=2, child_aspect_ratio=0.85, spacing=10)
            inventory_dlg = ft.AlertDialog(
                title=ft.Text("我的背包", size=24, weight="bold", text_align="center"),
                content=ft.Container(content=inventory_grid, width=380, height=500),
                actions=[ft.TextButton("關閉", on_click=lambda _: (setattr(inventory_dlg, "open", False), self.page.update()))],
                actions_alignment="center",
                open=True
            )
            self.page.overlay.append(inventory_dlg)
            self.page.update()

        def shop_item_card(item):
            img_src = ("/" + item["image_path"].replace("assets/", "")) if item["image_path"] else None
            return ft.Container(
                bgcolor="white", border=ft.border.all(1, colors.PRIMARY), border_radius=15,
                padding=10, ink=True, on_click=lambda _: show_purchase_dialog(item),
                content=ft.Column([
                    ft.Container(content=ft.Image(src=img_src, fit=ft.ImageFit.CONTAIN) if img_src else ft.Icon(ft.icons.SHOPPING_BAG), expand=True, alignment=ft.Alignment(0,0)),
                    ft.Column([
                        ft.Text(item["name"], size=16, weight="bold", text_align="center", max_lines=2),
                        ft.Text(f"{item['cost']} 點", size=16, color=colors.SECONDARY, weight="bold"),
                    ], horizontal_alignment="center", spacing=2)
                ], horizontal_alignment="center", expand=True)
            )

        self.item_grid = ft.GridView(max_extent=180, child_aspect_ratio=0.85, spacing=15, run_spacing=15, expand=True)
        for item in self.data["items"]:
            self.item_grid.controls.append(shop_item_card(item))

        calc_bg_h = lambda w: min(250, max(110, 100 + w * 0.1))
        shop_bg_h = calc_bg_h(curr_width)

        bg_image = ft.Container(
            height=shop_bg_h,
            content=ft.Stack([
                ft.Image(src="/shop_background.png", height=shop_bg_h * 2.38, fit=ft.ImageFit.FIT_HEIGHT, bottom=0, left=0, right=0)
            ], alignment=ft.alignment.bottom_center),
        )

        header_container = ft.Container(
            height=shop_bg_h,
            content=ft.Row([
                ft.Row([shop_title_icon_container, shop_title_text_stack], spacing=5),
                ft.Container(
                    content=ft.Row([balance_label_stack, self.balance_value_stack], spacing=5),
                    bgcolor=ft.colors.with_opacity(0.6, ft.colors.WHITE),
                    padding=12, border_radius=15,
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(left=20, right=15),
        )

        self.main_container.content = ft.Stack([
            bg_image,
            ft.Container(
                content=ft.Column([
                    header_container,
                    ft.Container(content=self.item_grid, expand=True, bgcolor=ft.colors.with_opacity(0.5, colors.WHITE), border_radius=10, padding=10)
                ], spacing=0, expand=True),
            ),
            ft.Container(
                content=ft.Container(
                    content=ft.Image(src="/backpack.png", width=64, height=64),
                    bgcolor=ft.colors.WHITE, border_radius=32, border=ft.border.all(2, colors.SECONDARY),
                    on_click=show_inventory_dialog, ink=True,
                ),
                right=30, bottom=30
            )
        ], expand=True)

async def build_shop(page: ft.Page) -> ft.Control:
    view = ShopView(page)
    return app_scaffold(view, selected_tab="Shop", page=page, padding=0, title_ref=view.title_ref, top_bar_title="商店")
