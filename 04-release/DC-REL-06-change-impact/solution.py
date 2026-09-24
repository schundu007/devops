"""DC-REL-06 Change Impact Query — reference solution."""
from __future__ import annotations

from collections import deque


def impacts(n: int, deps: list[tuple[int, int]], queries: list[tuple[int, int]]) -> list[bool]:
    """For each (u, v) query: does v depend on u, directly or through other components?

    deps holds (upstream, downstream) pairs; the graph has no cycles.
    """
    children: list[list[int]] = [[] for _ in range(n)]
    indegree = [0] * n
    for up, down in deps:
        children[up].append(down)
        indegree[down] += 1

    order: list[int] = []                         # Kahn's topological order
    ready = deque(v for v in range(n) if indegree[v] == 0)
    while ready:
        v = ready.popleft()
        order.append(v)
        for w in children[v]:
            indegree[w] -= 1
            if indegree[w] == 0:
                ready.append(w)

    # reach[u] is a bitmask of every component downstream of u.
    # Walk in reverse order so each child's mask is final before its parents use it.
    reach = [0] * n
    for u in reversed(order):
        for w in children[u]:
            reach[u] |= (1 << w) | reach[w]

    return [bool(reach[u] >> v & 1) for u, v in queries]
