"""DC-PLAT-15 On-Call Coverage Gaps — reference solution."""
from __future__ import annotations

import heapq


def coverage_gaps(schedules: list[list[list[int]]]) -> list[list[int]]:
    """Return every [start, end] with nobody on call, between the first shift
    start and the last shift end, in time order.

    schedules[p] is engineer p's shifts: [start, end] pairs (end exclusive),
    sorted by start and not overlapping each other.
    """
    gaps: list[list[int]] = []
    covered_until: int | None = None
    # Each engineer's list is already sorted, so a k-way merge yields all shifts
    # in start order in O(N log k) without re-sorting everything.
    for start, end in heapq.merge(*schedules):
        if covered_until is not None and start > covered_until:
            gaps.append([covered_until, start])  # nobody on call in between
        covered_until = end if covered_until is None else max(covered_until, end)
    return gaps
