from __future__ import annotations


class HapticsService:
    def __init__(self) -> None:
        self.enabled = True

    def configure(self, enabled: bool) -> None:
        self.enabled = enabled

    def tap(self) -> None:
        if not self.enabled:
            return
        # Placeholder for platform haptics call
        print("[haptics] tap")

    def success(self) -> None:
        if not self.enabled:
            return
        print("[haptics] success")
