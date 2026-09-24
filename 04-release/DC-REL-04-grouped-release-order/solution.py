"""DC-REL-04 Grouped Release Order — reference solution."""
from __future__ import annotations

from collections import deque


def _topo(adj: list[list[int]], indegree: list[int]) -> list[int] | None:
    """Kahn's algorithm. Returns None if the graph has a cycle."""
    indegree = indegree[:]
    ready = deque(v for v in range(len(adj)) if indegree[v] == 0)
    order: list[int] = []
    while ready:
        v = ready.popleft()
        order.append(v)
        for w in adj[v]:
            indegree[w] -= 1
            if indegree[w] == 0:
                ready.append(w)
    return order if len(order) == len(adj) else None


def release_order(n: int, m: int, service: list[int], before: list[list[int]]) -> list[int]:
    """Order steps 0..n-1 so each service's steps are contiguous and every
    before[i] step comes earlier than step i. Return [] if impossible."""
    # Give each standalone step (service -1) its own one-step group.
    group = list(service)
    groups = m
    for i in range(n):
        if group[i] == -1:
            group[i] = groups
            groups += 1

    step_adj: list[list[int]] = [[] for _ in range(n)]
    step_in = [0] * n
    group_adj: list[list[int]] = [[] for _ in range(groups)]
    group_in = [0] * groups
    for i in range(n):
        for p in before[i]:                 # p must run before i
            step_adj[p].append(i)
            step_in[i] += 1
            if group[p] != group[i]:        # a cross-service edge also orders the services
                group_adj[group[p]].append(group[i])
                group_in[group[i]] += 1

    step_order = _topo(step_adj, step_in)
    group_order = _topo(group_adj, group_in)
    if step_order is None or group_order is None:
        return []

    # Bucket steps by service, keeping the global step order inside each bucket.
    buckets: list[list[int]] = [[] for _ in range(groups)]
    for s in step_order:
        buckets[group[s]].append(s)
    return [s for g in group_order for s in buckets[g]]
