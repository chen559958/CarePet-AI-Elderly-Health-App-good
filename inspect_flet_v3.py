import flet as ft
import inspect

def main(page: ft.Page):
    sig = inspect.signature(ft.FilePicker.__init__)
    print("FilePicker.__init__ signature:")
    print(sig)
    page.window_destroy()

ft.app(target=main)
