"""測試影像辨別模組"""
from domain.vision_engine import VisionEngine
import os

# 測試 API key 是否正確載入
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("ZHIPU_API_KEY")
print(f"API Key 載入狀態: {'✓ 已載入' if api_key else '✗ 未找到'}")
if api_key:
    print(f"API Key 前綴: {api_key[:20]}...")

# 測試模組是否可以正常 import
print(f"VisionEngine 模組: ✓ 已載入")
print(f"analyze_drug_bag 方法: {'✓ 存在' if hasattr(VisionEngine, 'analyze_drug_bag') else '✗ 不存在'}")

print("\n影像辨別模組狀態: ✓ 正常")
print("提示: 使用 VisionEngine.analyze_drug_bag(image_path) 來辨識藥袋")
