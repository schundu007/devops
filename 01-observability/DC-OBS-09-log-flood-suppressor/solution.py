"""DC-OBS-09 Log Flood Suppressor — reference solution."""
from __future__ import annotations


class LogSuppressor:
    def __init__(self, window: int = 10) -> None:
        self.window = window
        # message -> the earliest second it may be printed again.
        self._next_allowed: dict[str, int] = {}

    def should_print(self, timestamp: int, message: str) -> bool:
        """True if `message` was not printed in the last `window` seconds (then record it)."""
        if timestamp < self._next_allowed.get(message, timestamp):
            return False  # suppressed: do NOT extend the quiet period
        self._next_allowed[message] = timestamp + self.window
        return True
