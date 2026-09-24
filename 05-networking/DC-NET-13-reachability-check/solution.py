"""DC-NET-13 Reachability Check — reference solution (iterative BFS)."""
from __future__ import annotations

from collections import deque


def can_reach(n: int, links: list[list[int]], source: int, target: int) -> bool:
    """True if target can be reached from source over two-way links."""
    if source == target:
        return True
    adj: list[list[int]] = [[] for _ in range(n)]
    for a, b in links:
        adj[a].append(b)
        adj[b].append(a)
    seen = [False] * n
    seen[source] = True
    queue = deque([source])
    while queue:
        node = queue.popleft()
        for nxt in adj[node]:
            if nxt == target:
                return True  # stop as soon as the target shows up
            if not seen[nxt]:
                seen[nxt] = True  # mark when enqueued, so each node is queued once
                queue.append(nxt)
    return False
