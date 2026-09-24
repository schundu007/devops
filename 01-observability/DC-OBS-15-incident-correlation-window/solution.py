"""DC-OBS-15 Incident Correlation Window — reference solution."""
from __future__ import annotations

import heapq


def tightest_window(error_times: list[list[int]]) -> list[int]:
    """Smallest [start, end] holding at least one error time from every service.

    Each inner list is one service's error times, sorted ascending and non-empty.
    Ties on width go to the window that starts earlier.
    """
    # Heap holds one pointer per service: (time, service index, position in its list).
    heap = [(times[0], s, 0) for s, times in enumerate(error_times)]
    heapq.heapify(heap)
    hi = max(times[0] for times in error_times)  # current window end = largest head
    best = [heap[0][0], hi]
    while True:
        lo, s, i = heapq.heappop(heap)  # current window start = smallest head
        if hi - lo < best[1] - best[0] or (hi - lo == best[1] - best[0] and lo < best[0]):
            best = [lo, hi]
        if i + 1 == len(error_times[s]):
            return best  # this service has no later error: no window can start later
        nxt = error_times[s][i + 1]
        hi = max(hi, nxt)
        heapq.heappush(heap, (nxt, s, i + 1))
