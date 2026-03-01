import flet as ft

def main(page: ft.Page):
    print("--- FULL PAGE MEMBERS ---")
    for attr in sorted(dir(page)):
        print(f" - {attr}")
    page.window_destroy() if hasattr(page, "window_destroy") else None

ft.app(target=main)
