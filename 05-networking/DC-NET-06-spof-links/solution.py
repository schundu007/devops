"""DC-NET-06 Single-Point-of-Failure Links — reference solution (iterative Tarjan)."""
from __future__ import annotations

from typing import Iterator


def critical_links(n: int, links: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Every link whose failure disconnects part of the network (a bridge).

    Devices are 0..n-1; links are undirected. Two parallel links between the same
    pair back each other up, so neither is critical.
    """
    # Store the link id with each neighbour, so we skip only the exact link we came
    # in on (not every link to the parent). That keeps parallel links correct.
    adj: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    for eid, (a, b) in enumerate(links):
        adj[a].append((b, eid))
        adj[b].append((a, eid))

    disc = [-1] * n  # discovery time of each device in the DFS
    low = [0] * n    # earliest discovery time reachable from its subtree via one back link
    timer = 0
    bridges: list[tuple[int, int]] = []

    for root in range(n):
        if disc[root] != -1:
            continue
        disc[root] = low[root] = timer
        timer += 1
        # Explicit stack of (device, link id used to enter it, neighbour iterator):
        # no recursion, so a 100,000-device chain cannot hit Python's recursion limit.
        stack: list[tuple[int, int, Iterator[tuple[int, int]]]] = [(root, -1, iter(adj[root]))]
        while stack:
            u, parent_link, neighbours = stack[-1]
            descended = False
            for v, eid in neighbours:
                if eid == parent_link:
                    continue
                if disc[v] == -1:            # tree link: go deeper
                    disc[v] = low[v] = timer
                    timer += 1
                    stack.append((v, eid, iter(adj[v])))
                    descended = True
                    break
                low[u] = min(low[u], disc[v])  # back link: a second way up
            if descended:
                continue
            stack.pop()                        # u is finished
            if stack:
                p = stack[-1][0]
                low[p] = min(low[p], low[u])
                # Nothing under u can reach p or above without the link p-u: it is a bridge.
                if low[u] > disc[p]:
                    bridges.append((p, u))
    return bridges
