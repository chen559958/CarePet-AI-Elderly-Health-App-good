import flet as ft
def main(page: ft.Page):
    page.add(ft.Text("Hello World"))
if __name__ == "__main__":
    print("Starting Flet...")
    ft.app(target=main)
