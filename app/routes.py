from __future__ import annotations

import flet as ft

from ui.pages.home_page import build_home
from ui.pages.records_page import build_records
from ui.pages.shop_page import build_shop
from ui.pages.member_page import build_member


def register(app: ft.App) -> None:
    app.page_routes = {
        "/": build_home,
        "/records": build_records,
        "/shop": build_shop,
        "/member": build_member,
    }
