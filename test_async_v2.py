import flet as ft
import asyncio

async def main(page: ft.Page):
    t = ft.Text("Initialization")
    page.add(t)
    
    async def simulate_scan():
        t.value = "Scanning..."
        page.update()
        await asyncio.sleep(1)
        t.value = "Scan Complete!"
        page.update()
        print("ASYNC_SUCCESS")

    # Call it immediately to see if it works in this environment
    await simulate_scan()
    
    # Keep it open for a bit
    await asyncio.sleep(2)
    page.window_destroy() if hasattr(page, "window_destroy") else None

if __name__ == "__main__":
    ft.app(target=main)
