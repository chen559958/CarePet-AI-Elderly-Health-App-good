from __future__ import annotations
import base64
import requests
import json
import os
from dataclasses import dataclass, field
from typing import Sequence, Optional
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

@dataclass
class ScannedMedication:
    name: str = ""
    periods: Sequence[str] = field(default_factory=list)
    pills_per_intake: float = 1.0  # Changed to float to support 0.5
    confidence: float = 0.0
    hospital: Optional[str] = None
    doctor: Optional[str] = None
    department: Optional[str] = None
    timing: str = "after_meal" # after_meal, before_meal
    patient_name: Optional[str] = None  # 藥袋上的病患姓名
    raw_data: Optional[dict] = None

class VisionEngine:
    @staticmethod
    def encode_image(image_path: str) -> str:
        """將圖片轉為 base64 編碼"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    @staticmethod
    def analyze_drug_bag(image_path: str) -> list[ScannedMedication]:
        """
        使用智譜 AI GLM-4V 辨識藥袋圖片。
        回傳辨識到的藥品列表。
        """
        api_key = os.getenv("ZHIPU_API_KEY")
        if not api_key:
            print("ERROR: ZHIPU_API_KEY not found in environment variables.")
            return []

        print(f"DEBUG: VisionEngine analyzing {image_path} with GLM-4V...")
        
        try:
            image_base64 = None
            
            # 嘗試縮小圖片以避免 timeout
            try:
                # 優先嘗試 cv2
                import cv2
                import numpy as np
                
                img = cv2.imread(image_path)
                if img is not None:
                    h, w = img.shape[:2]
                    max_size = 1024
                    if max(h, w) > max_size:
                        scale = max_size / max(h, w)
                        img = cv2.resize(img, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
                    
                    _, buffer = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                    image_base64 = base64.b64encode(buffer).decode('utf-8')
            except ImportError:
                pass
            except Exception as e:
                print(f"DEBUG: CV2 resize failed: {e}")

            if not image_base64:
                # cv2 失敗或未安裝，嘗試 PIL
                try:
                    from PIL import Image
                    import io
                    
                    with Image.open(image_path) as img:
                        # 轉換為 RGB 避免 RGBA 問題
                        if img.mode in ('RGBA', 'P'): img = img.convert('RGB')
                            
                        w, h = img.size
                        max_size = 1024
                        if max(w, h) > max_size:
                            scale = max_size / max(w, h)
                            new_w = int(w * scale)
                            new_h = int(h * scale)
                            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                        
                        buffer = io.BytesIO()
                        img.save(buffer, format="JPEG", quality=85)
                        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                except Exception as e:
                    print(f"DEBUG: PIL resize failed: {e}")
                    pass

            # 如果都失敗，使用原始圖片
            if not image_base64:
                print("DEBUG: Using original image without resize")
                image_base64 = VisionEngine.encode_image(image_path)
                
            url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            payload = {
                "model": "glm-4v-flash",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """請仔細辨識這張藥袋上的所有資訊,並包含以下欄位,以 JSON 格式回傳:
{
  "patient_name": "病患姓名",
  "hospital": "醫院名稱",
  "department": "科別",
  "doctor": "醫師姓名",
  "medicines": [
    {
      "name": "藥品名稱(中文)",
      "pills_per_intake": "每次服用顆數(數字,注意:半粒=0.5、一粒=1、兩粒=2)",
      "frequency": "服用頻率(需包含:早、中、晚、睡前,例如:每日三次、早晚各一次)",
      "timing": "服用時間(需包含:飯後、飯前、空腹)"
    }
  ]
}
**重要**:
1. patient_name 請特別注意辨識藥袋上的病患姓名,通常會標示在明顯位置。
2. pills_per_intake 必須特別注意「半粒」、「半顆」、「0.5」等描述,請回傳 0.5 而非 1。
如果某些欄位在藥袋上找不到,請填入 null。只回傳 JSON。"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ]
            }
            
            content = None
            # Retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(f"DEBUG: Sending request to GLM-4V (Attempt {attempt+1}/{max_retries})...")
                    response = requests.post(url, headers=headers, json=payload, timeout=60)
                    response.raise_for_status()
                    result = response.json()
                    
                    content = result["choices"][0]["message"]["content"]
                    print(f"DEBUG: VisionEngine raw content: {content}")
                    break
                except Exception as e:
                    print(f"WARNING: Request failed (Attempt {attempt+1}/{max_retries}): {e}")
                    if attempt == max_retries - 1:
                        raise e
                    import time
                    time.sleep(2)
            
            if not content:
                raise Exception("Failed to get content from API")

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            data = json.loads(content)
            med_list = data.get("medicines", [])
            results = []

            for med in med_list:
                # 解析時段（智慧展開）
                freq_str = (med.get("frequency", "") or "") + (med.get("timing", "") or "")
                periods = []
                
                # 智慧展開：如果看到「三次」或「3次」，自動勾選早中晚
                if any(k in freq_str for k in ["三次", "3次", "每日三次", "每天三次"]):
                    periods = ["breakfast", "lunch", "dinner"]
                else:
                    # 逐一檢查關鍵字
                    if any(k in freq_str for k in ["早", "朝", "晨"]): periods.append("breakfast")
                    if any(k in freq_str for k in ["中", "午"]): periods.append("lunch")
                    if any(k in freq_str for k in ["晚", "夕"]): periods.append("dinner")
                
                # 睡前獨立判斷（可與早中晚共存）
                if any(k in freq_str for k in ["睡", "眠", "bed", "睡前"]):
                    if "sleep" not in periods:
                        periods.append("sleep")
                
                # 預設至少一餐
                if not periods: 
                    periods = ["breakfast"]
                
                # 解析顆數
                try:
                    # 優先從 pills_per_intake 欄位讀取
                    if "pills_per_intake" in med and med["pills_per_intake"]:
                        raw_pills = str(med["pills_per_intake"])
                    else:
                        # Fallback: 從 frequency 或 dosage 提取
                        raw_pills = str(med.get("frequency", "")) + str(med.get("dosage", "1"))
                    
                    import re
                    # 尋找「每次X粒」、「X粒」等模式
                    nums = re.findall(r'(\d*\.?\d+)', raw_pills)
                    pills = float(nums[0]) if nums else 1.0
                    pills = max(0.5, min(10.0, pills))
                except:
                    pills = 1.0
                
                # 解析時機
                timing_str = med.get("timing") or ""
                timing_val = "after_meal"
                if any(k in timing_str for k in ["前", "空腹"]):
                    timing_val = "before_meal"

                results.append(ScannedMedication(
                    name=med.get("name", "未知藥品"),
                    periods=periods,
                    pills_per_intake=pills,
                    confidence=0.95,
                    hospital=data.get("hospital"),
                    doctor=data.get("doctor"),
                    department=data.get("department"),
                    timing=timing_val,
                    patient_name=data.get("patient_name"),
                    raw_data=data
                ))
                
            return results
            
        except Exception as e:
            print(f"VisionEngine Error: {e}")
            import traceback
            traceback.print_exc()
            return []
