"""DC-OBS-11 Metric Bucket Counter — reference solution."""
from __future__ import annotations

from bisect import bisect_left, bisect_right, insort

BUCKET_SECONDS = {"minute": 60, "hour": 3600, "day": 86400}


class EventCounter:
    def __init__(self) -> None:
        # event name -> sorted list of event times (seconds)
        self._times: dict[str, list[int]] = {}

    def record(self, name: str, time: int) -> None:
        """Store one event. Events may arrive in any time order."""
        insort(self._times.setdefault(name, []), time)

    def counts(self, step: str, name: str, start: int, end: int) -> list[int]:
        """Events per step-sized bucket over [start, end], both ends inclusive."""
        size = BUCKET_SECONDS[step]
        buckets = [0] * ((end - start) // size + 1)
        times = self._times.get(name, [])
        # Only look at events inside [start, end]: two binary searches.
        lo, hi = bisect_left(times, start), bisect_right(times, end)
        for t in times[lo:hi]:
            buckets[(t - start) // size] += 1  # align to the query's start, not to the clock
        return buckets
