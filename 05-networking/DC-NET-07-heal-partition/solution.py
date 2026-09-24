"""DC-NET-07 Heal a Network Partition — reference solution."""
from __future__ import annotations


def min_link_moves(n: int, links: list[tuple[int, int]]) -> int:
    """Fewest cables to unplug and re-plug so all n devices connect, or -1 if impossible."""
    # n devices need at least n - 1 links to be connected at all.
    if len(links) < n - 1:
        return -1

    parent = list(range(n))
    size = [1] * n

    def find(x: int) -> int:
        # Path halving: point every other node at its grandparent while walking up.
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    segments = n
    for a, b in links:
        ra, rb = find(a), find(b)
        if ra == rb:
            continue  # a spare link: it closes a loop, so it can be moved
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra  # union by size keeps trees shallow
        size[ra] += size[rb]
        segments -= 1

    # Enough links overall means enough spare ones: each move joins two segments.
    return segments - 1
