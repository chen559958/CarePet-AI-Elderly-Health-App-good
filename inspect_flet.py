import flet as ft

def main(page: ft.Page):
    fp = ft.FilePicker()
    print("FilePicker attributes:")
    for attr in dir(fp):
        if attr.startswith("on_"):
            print(f" - {attr}")
    page.window_destroy()

ft.app(target=main)
