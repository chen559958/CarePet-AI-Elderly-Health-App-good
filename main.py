import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main app
from app.main import main
import flet as ft

if __name__ == "__main__":
    print(">>> 正在啟動 main.py...")
    # Set assets directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_path = os.path.join(base_dir, "assets")
    
    print(f">>> DEBUG: assets_dir 設定為: {assets_path}")
    print(">>> 準備呼叫 ft.app()...")
    try:
        ft.app(target=main, assets_dir=assets_path)
    except Exception as e:
        print(f">>> Flet 啟動異常: {e}")
        import traceback
        traceback.print_exc()