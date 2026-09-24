"""DC-OBS-06 Longest Stable Latency Window — reference solution."""
from __future__ import annotations

from collections import deque


def longest_stable_window(latency_ms: list[int], limit: int) -> int:
    """Length of the longest run of consecutive samples with max - min <= limit."""
    maxq: deque[int] = deque()  # indices, values decreasing: front is the window max
    minq: deque[int] = deque()  # indices, values increasing: front is the window min
    left = 0
    best = 0
    for right, x in enumerate(latency_ms):
        while maxq and latency_ms[maxq[-1]] < x:
            maxq.pop()
        maxq.append(right)
        while minq and latency_ms[minq[-1]] > x:
            minq.pop()
        minq.append(right)
        # Shrink from the left until the band fits again.
        while latency_ms[maxq[0]] - latency_ms[minq[0]] > limit:
            left += 1
            if maxq[0] < left:
                maxq.popleft()
            if minq[0] < left:
                minq.popleft()
        best = max(best, right - left + 1)
    return best
