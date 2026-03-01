import flet as ft

async def main(page: ft.Page):
    fp = ft.FilePicker()
    page.overlay.append(fp)
    page.add(ft.Text("If you see this and no error, FilePicker is valid."))
    page.update()

if __name__ == "__main__":
    ft.run(main)
