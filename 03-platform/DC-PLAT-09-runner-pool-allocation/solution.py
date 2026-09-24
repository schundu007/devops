"""DC-PLAT-09 Runner Pool Allocation — reference solution."""
from __future__ import annotations

import heapq


def busiest_runner(n: int, jobs: list[list[int]]) -> int:
    """Return the runner that ran the most jobs (lowest number on a tie).

    Runners are numbered 0..n-1. jobs[i] = [queued_at, planned_end]; queued_at
    values are unique. A job takes the lowest-numbered idle runner. If none is
    idle, it waits for the runner that frees up first (lowest number on a tie)
    and keeps its full duration, so it ends later than planned.
    """
    idle = list(range(n))            # min-heap of idle runner numbers
    busy: list[tuple[int, int]] = []  # min-heap of (free_at, runner)
    ran = [0] * n

    for start, end in sorted(jobs):
        # Every runner that finished by `start` is idle again.
        while busy and busy[0][0] <= start:
            _, runner = heapq.heappop(busy)
            heapq.heappush(idle, runner)

        if idle:
            runner = heapq.heappop(idle)
            heapq.heappush(busy, (end, runner))
        else:
            # Nobody is idle: the job waits for the earliest runner to free up.
            free_at, runner = heapq.heappop(busy)
            heapq.heappush(busy, (free_at + (end - start), runner))
        ran[runner] += 1

    # Most jobs first; on a tie, the lower runner number wins.
    return max(range(n), key=lambda r: (ran[r], -r))
