"""DC-SEC-13 Secret Exposure Over Time — reference solution."""
from __future__ import annotations

from itertools import groupby


def exposed(n: int, sessions: list[list[int]], first: int) -> list[int]:
    """Everyone who ends up holding the secret, sorted. Party 0 and `first` start exposed."""
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]  # path halving keeps trees shallow
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            # Always hang the other root under 0's root, so "exposed" == find(x) == find(0).
            if find(0) == rb:
                ra, rb = rb, ra
            parent[rb] = ra

    union(0, first)
    for _, group in groupby(sorted(sessions, key=lambda s: s[2]), key=lambda s: s[2]):
        group = list(group)
        # Sessions at the same moment can chain: link them all first.
        for a, b, _t in group:
            union(a, b)
        # Anyone in this time slot who did not reach party 0 was not exposed.
        # Undo their links so a later session cannot expose them retroactively.
        root0 = find(0)
        for a, b, _t in group:
            for p in (a, b):
                if find(p) != root0:
                    parent[p] = p
    root0 = find(0)
    return [p for p in range(n) if find(p) == root0]
