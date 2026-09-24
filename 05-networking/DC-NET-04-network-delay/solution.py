"""DC-NET-04 Network Delay Time — reference solution."""
from __future__ import annotations

import heapq


def network_delay(links: list[tuple[int, int, int]], n: int, source: int) -> int:
    """Time until a signal flooded from `source` reaches all n routers, or -1.

    links[i] = (u, v, ms): a one-way link from router u to router v taking ms milliseconds.
    Routers are numbered 1..n.
    """
    graph: list[list[tuple[int, int]]] = [[] for _ in range(n + 1)]
    for u, v, ms in links:
        graph[u].append((v, ms))

    # Dijkstra: always finalise the router with the smallest known arrival time.
    arrival: dict[int, int] = {}
    heap = [(0, source)]
    while heap:
        t, node = heapq.heappop(heap)
        if node in arrival:
            continue  # stale entry: a faster arrival was already finalised
        arrival[node] = t
        for nxt, ms in graph[node]:
            if nxt not in arrival:
                heapq.heappush(heap, (t + ms, nxt))

    # Some router never heard the signal: the network is partitioned.
    return max(arrival.values()) if len(arrival) == n else -1
