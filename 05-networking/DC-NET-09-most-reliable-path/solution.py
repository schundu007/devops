"""DC-NET-09 Most Reliable Path — reference solution."""
from __future__ import annotations

import heapq


def most_reliable_path(
    n: int, links: list[list[int]], success: list[float], src: int, dst: int
) -> float:
    """Highest end-to-end success probability from src to dst (0.0 if unreachable)."""
    adj: list[list[tuple[int, float]]] = [[] for _ in range(n)]
    for (a, b), p in zip(links, success):
        adj[a].append((b, p))  # links work in both directions
        adj[b].append((a, p))

    best = [0.0] * n
    best[src] = 1.0
    heap = [(-1.0, src)]  # max-heap via negated probabilities
    while heap:
        neg_p, node = heapq.heappop(heap)
        p = -neg_p
        if node == dst:
            return p  # the first time dst is popped, its probability is final
        if p < best[node]:
            continue  # stale entry: a better path to this node was already found
        for nxt, link_p in adj[node]:
            cand = p * link_p  # probabilities multiply along a path and never grow
            if cand > best[nxt]:
                best[nxt] = cand
                heapq.heappush(heap, (-cand, nxt))
    return 0.0
