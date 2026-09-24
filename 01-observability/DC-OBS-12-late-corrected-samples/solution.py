"""DC-OBS-12 Late & Corrected Samples — reference solution."""
from __future__ import annotations

import heapq


class SampleTracker:
    def __init__(self) -> None:
        self._value_at: dict[int, float] = {}   # timestamp -> current (corrected) value
        self._latest = -1                        # newest timestamp seen
        self._max_heap: list[tuple[float, int]] = []  # (-value, timestamp)
        self._min_heap: list[tuple[float, int]] = []  # (value, timestamp)

    def update(self, timestamp: int, value: float) -> None:
        """Record a sample. A repeat timestamp is a correction and replaces the old value."""
        self._value_at[timestamp] = value
        self._latest = max(self._latest, timestamp)
        # Never search the heaps to delete the old value: push the new pair and let
        # stale pairs be discarded when they surface at the top (lazy deletion).
        heapq.heappush(self._max_heap, (-value, timestamp))
        heapq.heappush(self._min_heap, (value, timestamp))

    def current(self) -> float:
        """Value at the newest timestamp."""
        return self._value_at[self._latest]

    def maximum(self) -> float:
        # A heap entry is stale if its timestamp has since been corrected to another value.
        while self._value_at[self._max_heap[0][1]] != -self._max_heap[0][0]:
            heapq.heappop(self._max_heap)
        return -self._max_heap[0][0]

    def minimum(self) -> float:
        while self._value_at[self._min_heap[0][1]] != self._min_heap[0][0]:
            heapq.heappop(self._min_heap)
        return self._min_heap[0][0]
