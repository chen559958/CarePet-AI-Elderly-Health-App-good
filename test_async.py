import flet as ft
import asyncio

async def main(page: ft.Page):
    page.add(ft.Text("Async Main Works!"))
    await asyncio.sleep(1)
    page.add(ft.Text("Step 2"))
    page.update()

ft.app(target=main)
# Or ft.run(main) if app() is deprecated
