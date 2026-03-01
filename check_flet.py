import flet as ft
import inspect

print(f"Flet Version: {ft.__version__}")
print("Image __init__ signature:")
print(inspect.signature(ft.Image.__init__))
