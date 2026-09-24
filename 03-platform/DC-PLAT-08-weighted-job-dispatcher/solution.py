"""DC-PLAT-08 Weighted Job Dispatcher — reference solution."""
from __future__ import annotations

import heapq


def assign_jobs(weights: list[int], durations: list[int]) -> list[int]:
    """Worker index that runs each job, in job order."""
    free = [(w, i) for i, w in enumerate(weights)]   # idle workers: lowest weight, then lowest index
    heapq.heapify(free)
    busy: list[tuple[int, int, int]] = []            # (time it is idle again, weight, index)
    out: list[int] = []
    now = 0
    for j, d in enumerate(durations):
        # Job j is queued at second j; jobs are dispatched in order, so time never goes back.
        now = max(now, j)
        if not free:
            now = max(now, busy[0][0])  # nobody idle: wait for the next worker to finish
        while busy and busy[0][0] <= now:
            t, w, i = heapq.heappop(busy)
            heapq.heappush(free, (w, i))
        w, i = heapq.heappop(free)
        out.append(i)
        heapq.heappush(busy, (now + d, w, i))
    return out
