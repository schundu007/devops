"""DC-NET-11 Cheapest Full Connectivity — reference solution (Prim, dense graph)."""
from __future__ import annotations


def min_interconnect_cost(sites: list[list[int]]) -> int:
    """Least total cable length that connects every site (Manhattan distance per link)."""
    n = len(sites)
    if n <= 1:
        return 0
    INF = float("inf")
    in_tree = [False] * n
    # dist[i] = cheapest link from site i to any site already in the tree.
    dist = [INF] * n
    dist[0] = 0
    total = 0
    for _ in range(n):
        # Pick the cheapest site not yet connected. A plain O(n) scan beats a heap
        # here because every pair of sites can be linked (the graph is complete).
        u = min((i for i in range(n) if not in_tree[i]), key=dist.__getitem__)
        in_tree[u] = True
        total += dist[u]
        ux, uy = sites[u]
        for v in range(n):
            if not in_tree[v]:
                d = abs(ux - sites[v][0]) + abs(uy - sites[v][1])
                if d < dist[v]:
                    dist[v] = d
    return int(total)
