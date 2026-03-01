import flet as ft

def main(page: ft.Page):
    fp = ft.FilePicker()
    print("--- FilePicker members ---")
    for attr in dir(fp):
        print(attr)
        
    print("\n--- Page members ---")
    for attr in dir(page):
        if "file" in attr.lower() or "picker" in attr.lower():
            print(attr)
    
    # Just close the session
    page.window_close() if hasattr(page, "window_close") else None

ft.app(target=main)
