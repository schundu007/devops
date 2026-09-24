"""DC-REL-07 Safe Services Finder — reference solution."""
from __future__ import annotations

from collections import deque


def safe_services(waits_on: list[list[int]]) -> list[int]:
    """Services whose every dependency chain ends at a service that waits on nothing."""
    n = len(waits_on)
    pending = [len(deps) for deps in waits_on]      # dependencies not yet proven safe
    waited_by: list[list[int]] = [[] for _ in range(n)]
    for s, deps in enumerate(waits_on):
        for d in deps:
            waited_by[d].append(s)                  # reverse edge: d is waited on by s

    ready = deque(s for s in range(n) if pending[s] == 0)  # waits on nothing: safe
    safe = [False] * n
    while ready:
        d = ready.popleft()
        safe[d] = True
        for s in waited_by[d]:
            pending[s] -= 1
            if pending[s] == 0:                     # every dependency of s is safe
                ready.append(s)
    return [s for s in range(n) if safe[s]]
