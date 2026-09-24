"""DC-OBS-10 Log Time-Range Query — reference solution."""
from __future__ import annotations

from bisect import bisect_left, bisect_right, insort

# Timestamps look like "2026:09:23:02:14:05" (Year:Month:Day:Hour:Minute:Second).
# Every field is zero-padded to a fixed width, so string order == time order,
# and a granularity is just "keep the first N characters".
_PREFIX_LEN = {"Year": 4, "Month": 7, "Day": 10, "Hour": 13, "Minute": 16, "Second": 19}


class LogStore:
    def __init__(self) -> None:
        self._entries: list[tuple[str, int]] = []  # (timestamp, log id), kept sorted

    def put(self, log_id: int, timestamp: str) -> None:
        # O(n) list insert; fine for this chip (see Level Up for a real index).
        insort(self._entries, (timestamp, log_id))

    def retrieve(self, start: str, end: str, granularity: str) -> list[int]:
        """IDs of logs whose timestamp, cut to `granularity`, lies in [start, end]; ascending."""
        n = _PREFIX_LEN[granularity]
        # Lowest possible timestamp with start's prefix, and highest with end's prefix.
        # ":" sorts below every digit and "~" above, so these bounds are exact.
        lo = (start[:n], -1)
        hi = (end[:n] + "~", -1)
        i = bisect_left(self._entries, lo)
        j = bisect_right(self._entries, hi)
        return sorted(log_id for _, log_id in self._entries[i:j])
