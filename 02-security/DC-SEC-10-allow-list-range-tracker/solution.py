"""DC-SEC-10 Allow-List Range Tracker — reference solution."""
from __future__ import annotations

from bisect import bisect_left, bisect_right


class AllowList:
    """Half-open ranges [lo, hi) kept sorted, disjoint and non-touching."""

    def __init__(self) -> None:
        # Parallel lists so bisect works on plain ints: range k is [starts[k], ends[k]).
        self._starts: list[int] = []
        self._ends: list[int] = []

    def add(self, lo: int, hi: int) -> None:
        """Allow every value in [lo, hi)."""
        # Ranges that overlap OR touch [lo, hi) get merged into one.
        i = bisect_left(self._ends, lo)     # first range with end >= lo
        j = bisect_right(self._starts, hi)  # ranges before j start at or before hi
        if i < j:
            lo = min(lo, self._starts[i])
            hi = max(hi, self._ends[j - 1])
        self._starts[i:j] = [lo]
        self._ends[i:j] = [hi]

    def remove(self, lo: int, hi: int) -> None:
        """Stop allowing every value in [lo, hi). May split one range into two."""
        i = bisect_right(self._ends, lo)    # first range with end > lo
        j = bisect_left(self._starts, hi)   # ranges before j start before hi
        if i >= j:
            return  # nothing overlaps
        new_starts: list[int] = []
        new_ends: list[int] = []
        if self._starts[i] < lo:            # keep the left piece of the first range
            new_starts.append(self._starts[i])
            new_ends.append(lo)
        if self._ends[j - 1] > hi:          # keep the right piece of the last range
            new_starts.append(hi)
            new_ends.append(self._ends[j - 1])
        self._starts[i:j] = new_starts
        self._ends[i:j] = new_ends

    def covers(self, lo: int, hi: int) -> bool:
        """True if every value in [lo, hi) is allowed."""
        k = bisect_right(self._starts, lo) - 1   # last range starting at or before lo
        # Ranges never touch, so [lo, hi) must fit inside that single range.
        return k >= 0 and self._ends[k] >= hi

    def ranges(self) -> list[tuple[int, int]]:
        """Current allowed ranges, sorted, as (lo, hi) half-open pairs."""
        return list(zip(self._starts, self._ends))
