"""DC-OBS-05 Top-K Noisy Pods Board — reference solution."""
from __future__ import annotations

import heapq


class NoisyBoard:
    def __init__(self) -> None:
        self._counts: dict[str, int] = {}  # key (pod or API key) -> running total

    def add(self, key: str, amount: int) -> None:
        """Add `amount` (>= 1) to `key`'s total, creating it at 0 if new."""
        self._counts[key] = self._counts.get(key, 0) + amount

    def reset(self, key: str) -> None:
        """Forget `key` (the pod was deleted, or the counter window rolled over)."""
        self._counts.pop(key, None)

    def top(self, k: int) -> list[tuple[str, int]]:
        """The k largest totals as (key, total), largest first; ties by key, A to Z."""
        # nsmallest on (-total, key) keeps a heap of size k: O(n log k),
        # and handles the tie-break without a custom comparator.
        return heapq.nsmallest(k, self._counts.items(), key=lambda kv: (-kv[1], kv[0]))

    def top_total(self, k: int) -> int:
        """Sum of the k largest totals (the value the classic problem returns)."""
        return sum(total for _, total in self.top(k))
