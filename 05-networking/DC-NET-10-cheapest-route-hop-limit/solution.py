"""DC-NET-10 Cheapest Route Within Hop Limit — reference solution."""
from __future__ import annotations


def cheapest_route(
    n: int, routes: list[list[int]], src: int, dst: int, max_transit: int
) -> int:
    """Lowest total cost from src to dst through at most max_transit middle regions, or -1."""
    INF = float("inf")
    cost = [INF] * n
    cost[src] = 0
    # At most max_transit middle regions means at most max_transit + 1 hops.
    # Round r of Bellman-Ford finds the cheapest paths that use at most r hops.
    for _ in range(max_transit + 1):
        prev = cost[:]  # read from the last round only, so each round adds one hop at most
        for a, b, price in routes:
            if prev[a] + price < cost[b]:
                cost[b] = prev[a] + price
    return -1 if cost[dst] == INF else int(cost[dst])
