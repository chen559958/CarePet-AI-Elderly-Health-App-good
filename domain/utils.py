from __future__ import annotations
from datetime import datetime, timezone, timedelta

def get_now_taiwan() -> datetime:
    """獲取台灣時間 (UTC+8)"""
    return datetime.now(timezone(timedelta(hours=8)))

def to_taiwan_time(dt: datetime | str) -> datetime:
    """將 ISO 字串或 naive/其他時區的 datetime 轉為台灣時間"""
    if isinstance(dt, str):
        # 如果是 SQLite 存儲的字串格式
        try:
            # 去掉可能的多餘毫秒或 Z 標記
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            # 退而求其次嘗試基本格式
            try:
                dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return get_now_taiwan() # 保底

    if dt.tzinfo is None:
        # 在開發環境中，許多資料庫存 naive datetimes 其實就是當地時間
        # 這裡改為假設 naive datetime 是台灣時間以避免 8 小時偏移問題
        dt = dt.replace(tzinfo=timezone(timedelta(hours=8)))
    return dt.astimezone(timezone(timedelta(hours=8)))
