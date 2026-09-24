"""DC-SEC-12 Blast Radius of a Leaked Credential — reference solution."""
from __future__ import annotations


def blast_radius(holds: list[list[int]], leaked: int) -> list[int]:
    """Every resource reachable from `leaked`, following held credentials. Sorted."""
    seen = {leaked}
    stack = [leaked]  # iterative DFS: no recursion limit on long chains
    while stack:
        node = stack.pop()
        for nxt in holds[node]:
            if nxt not in seen:
                seen.add(nxt)  # mark on push so each resource is expanded once
                stack.append(nxt)
    return sorted(seen)
