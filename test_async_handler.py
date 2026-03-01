import flet as ft
import asyncio

def main(page: ft.Page):
    t = ft.Text("Testing...")
    page.add(t)
    
    async def on_click(e):
        t.value = "Waiting 1s..."
        page.update()
        await asyncio.sleep(1)
        t.value = "Async Click Worked!"
        page.update()
        
    page.add(ft.ElevatedButton("Click Me", on_click=on_click))

ft.app(target=main)
# ft.run(main)
