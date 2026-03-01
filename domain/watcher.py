from __future__ import annotations
from typing import Callable, Any

class Watcher:
    """A simple observable pattern to notify UI of data changes."""
    def __init__(self):
        self._listeners: list[Callable[[], Any]] = []

    def subscribe(self, callback: Callable[[], Any]):
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unsubscribe(self, callback: Callable[[], Any]):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def notify(self):
        for listener in self._listeners:
            try:
                listener()
            except Exception as e:
                print(f"Error in watcher notification: {e}")

# Global watchers for major entities
reminder_watcher = Watcher()
pet_watcher = Watcher()
user_watcher = Watcher()
