"""DC-CAP-02 Backup Window Bandwidth — reference solution."""
from __future__ import annotations


def min_nightly_capacity(files: list[int], nights: int) -> int:
    """Smallest nightly capacity that copies all files, in order, within `nights` nights."""

    def nights_needed(cap: int) -> int:
        used, count = 0, 1
        for size in files:
            if used + size > cap:  # tonight is full: this file starts the next night
                count += 1
                used = 0
            used += size
        return count

    # Capacity below the largest file can never work; the total always fits in one night.
    lo, hi = max(files), sum(files)
    while lo < hi:
        mid = (lo + hi) // 2
        if nights_needed(mid) <= nights:
            hi = mid  # mid works, so try smaller
        else:
            lo = mid + 1
    return lo
