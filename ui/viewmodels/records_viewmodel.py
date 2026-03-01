from __future__ import annotations
from datetime import datetime
from app.container import Container

class RecordsViewModel:
    def __init__(self, container: Container):
        self.container = container
        self.reminder_repo = container.reminder_repo
        self.drug_repo = container.drug_repo
        self.bp_repo = container.bp_repo

    def load_records(self) -> dict[str, list[dict]]:
        user = self.container.auth_service.get_current_user()
        if not user:
            return {}
        
        events = self.reminder_repo.list_all_events(user.id, limit=200)
        
        # Get drug info for mapping
        drugs_list = self.drug_repo.list_active_drugs(user.id)
        drugs_map = {d.id: d for d in drugs_list}
        
        # Group by date -> drug_id
        grouped = {}
        for e in events:
            date_str = e.date  # "YYYY-MM-DD"
            if date_str not in grouped:
                grouped[date_str] = {}
            
            if e.drug_id not in grouped[date_str]:
                drug = drugs_map.get(e.drug_id)
                grouped[date_str][e.drug_id] = {
                    "drug_name": drug.drug_name if drug else f"藥品 {e.drug_id}",
                    "hospital": drug.hospital if drug else None,
                    "intakes": [],
                    "total": 0,
                    "taken": 0
                }
            
            d_item = grouped[date_str][e.drug_id]
            d_item["total"] += 1
            if e.status == "taken":
                d_item["taken"] += 1
            
            d_item["intakes"].append({
                "planned_time": e.planned_time.strftime("%H:%M"),
                "action_time": e.action_time.strftime("%H:%M") if e.action_time else "---",
                "status": e.status,
                "status_label": self._get_status_label(e.status),
                "status_color": self._get_status_color(e.status)
            })

        # Final formatting
        result = {}
        # Sort dates descending
        for date_str in sorted(grouped.keys(), reverse=True):
            items = []
            for drug_id, info in grouped[date_str].items():
                # Add summary info
                info["summary_label"] = "達成率"
                info["summary_status"] = f"{info['taken']}/{info['total']}"
                percentage = (info['taken'] / info['total']) if info['total'] > 0 else 0
                info["summary_color"] = "green" if percentage == 1 else ("orange" if percentage > 0 else "red")
                
                # Sort intakes by planned_time
                info["intakes"].sort(key=lambda x: x["planned_time"])
                items.append(info)
            result[date_str] = items
            
        return result

    def _get_status_label(self, status: str) -> str:
        labels = {
            "taken": "已服用",
            "missed": "已錯過",
            "snoozed": "稍後提醒",
            "scheduled": "未設定",
            "notified": "待執行",
        }
        return labels.get(status, "未知")

    def get_daily_adherence_stats(self) -> list[dict]:
        """Returns taken count and total count for each of the last 7 days."""
        user = self.container.auth_service.get_current_user()
        if not user:
            return []
        # 1. Fetch more events to cover 7 days
        events = self.reminder_repo.list_all_events(user.id, limit=500)
        
        # 2. Group by date
        daily_stats = {}
        for e in events:
            date_str = e.planned_time.strftime("%m/%d")
            if date_str not in daily_stats:
                daily_stats[date_str] = {"taken": 0, "total": 0}
            
            daily_stats[date_str]["total"] += 1
            if e.status == "taken":
                daily_stats[date_str]["taken"] += 1
        
        # 3. Sort by date and take last 7
        sorted_dates = sorted(daily_stats.keys())[-7:]
        return [
            {
                "date": d,
                "taken": daily_stats[d]["taken"],
                "total": daily_stats[d]["total"],
                "percentage": (daily_stats[d]["taken"] / daily_stats[d]["total"] * 100) if daily_stats[d]["total"] > 0 else 0
            } for d in sorted_dates
        ]

    def get_bp_stats(self) -> list[dict]:
        """Returns systolic and diastolic values for the last 7 measurements."""
        user = self.container.auth_service.get_current_user()
        if not user:
            return []
        records = self.bp_repo.list_recent_records(user.id, limit=7)
        # Reverse to get chronological order
        records.reverse()
        
        formatted_records = []
        for r in records:
            try:
                dt = r["created_at"]
                if isinstance(dt, str):
                    dt = datetime.fromisoformat(dt)
                
                formatted_records.append({
                    "date": dt.strftime("%m/%d"),
                    "systolic": r["systolic"],
                    "diastolic": r["diastolic"],
                    "pulse": r.get("pulse"),
                })
            except Exception as e:
                print(f"Error parsing BP record: {e}")
                continue
        return formatted_records

    def _get_status_color(self, status: str) -> str:
        colors = {
            "taken": "green",
            "missed": "red",
            "snoozed": "orange",
            "scheduled": "blue",
            "notified": "blue",
        }
        return colors.get(status, "grey")
