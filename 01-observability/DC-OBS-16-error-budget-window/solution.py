"""DC-OBS-16 Error Budget Window — reference solution."""
from __future__ import annotations


def longest_window(checks: list[int], budget: int) -> int:
    """Length of the longest run of consecutive checks with at most `budget` failures.

    checks[i] is 1 for a passed health check and 0 for a failed one.
    """
    left = 0
    failures = 0
    best = 0
    for right, ok in enumerate(checks):
        if ok == 0:
            failures += 1
        # Over budget: shrink from the left until the window is valid again.
        while failures > budget:
            if checks[left] == 0:
                failures -= 1
            left += 1
        best = max(best, right - left + 1)
    return best
