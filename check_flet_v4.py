import flet as ft
with open("flet_version.txt", "w") as f:
    try:
        f.write(f"Flet version: {ft.version.version}\n")
    except AttributeError:
        f.write("Flet version: unknown (v0.26.0+ likely)\n")
    try:
        f.write(f"Has UserControl: {hasattr(ft, 'UserControl')}\n")
    except:
        f.write("Has UserControl: Error checking\n")
