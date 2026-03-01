
import flet as ft

def main(page: ft.Page):
    print("DEBUG: Simple main started")
    page.add(
        ft.Text("HELLO WORLD - TEST", size=50, color="red", weight="bold"),
        ft.ElevatedButton("Click Me", on_click=lambda _: print("Clicked"))
    )
    page.update()
    print("DEBUG: Page updated")

if __name__ == "__main__":
    ft.app(target=main)
