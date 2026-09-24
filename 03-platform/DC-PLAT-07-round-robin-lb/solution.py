"""DC-PLAT-07 Round-Robin Load Balancer — reference solution."""
from __future__ import annotations

import heapq
from bisect import bisect_left, insort


def busiest_backends(k: int, arrival: list[int], load: list[int]) -> list[int]:
    """Backend IDs that served the most requests, in increasing order."""
    served = [0] * k
    free = list(range(k))              # sorted IDs of idle backends
    busy: list[tuple[int, int]] = []   # min-heap of (time it becomes free, backend)

    for i, (t, d) in enumerate(zip(arrival, load)):
        # Release every backend that has finished by time t (finished at t counts).
        while busy and busy[0][0] <= t:
            insort(free, heapq.heappop(busy)[1])
        if not free:
            continue                   # every backend busy: the request is dropped (503)
        # Preferred backend is i % k; otherwise the next idle one, wrapping around.
        j = bisect_left(free, i % k)
        if j == len(free):
            j = 0
        backend = free.pop(j)
        served[backend] += 1
        heapq.heappush(busy, (t + d, backend))

    top = max(served)
    return [b for b in range(k) if served[b] == top]
