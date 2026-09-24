"""DC-NET-08 Find the Loop Link — reference solution."""
from __future__ import annotations


def find_loop_link(n: int, links: list[list[int]]) -> list[int]:
    """Return the link that closes a loop, choosing the one listed last if several could."""
    parent = list(range(n + 1))  # switches are numbered 1..n
    size = [1] * (n + 1)

    def find(x: int) -> int:
        # Path halving: point every other node at its grandparent on the way up.
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in links:
        ra, rb = find(a), find(b)
        if ra == rb:
            # a and b were already connected, so this link closes a loop. Every
            # other link on the loop came earlier, so this is the last one listed.
            return [a, b]
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra  # union by size keeps the trees shallow
        size[ra] += size[rb]
    return []  # unreachable for valid input: there is always exactly one extra link
