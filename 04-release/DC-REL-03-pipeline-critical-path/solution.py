"""DC-REL-03 Pipeline Critical Path — reference solution."""
from __future__ import annotations

from collections import deque


def pipeline_time(n: int, deps: list[tuple[int, int]], duration: list[int]) -> int:
    """Minimum wall-clock time to finish stages 0..n-1 with unlimited parallel runners.

    deps holds (a, b) pairs: stage b cannot start until stage a has finished.
    """
    children: list[list[int]] = [[] for _ in range(n)]
    waiting = [0] * n                     # unfinished dependencies per stage
    for a, b in deps:
        children[a].append(b)
        waiting[b] += 1

    start = [0] * n                       # earliest start = latest finish among its deps
    ready = deque(i for i in range(n) if waiting[i] == 0)
    total = 0
    while ready:                          # Kahn's order: a stage runs after all its deps
        s = ready.popleft()
        finish = start[s] + duration[s]
        total = max(total, finish)
        for nxt in children[s]:
            start[nxt] = max(start[nxt], finish)
            waiting[nxt] -= 1
            if waiting[nxt] == 0:
                ready.append(nxt)
    return total
