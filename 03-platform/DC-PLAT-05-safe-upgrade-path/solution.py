"""DC-PLAT-05 Shortest Safe Upgrade Path — reference solution."""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Sequence

State = tuple[str, ...]


def min_upgrade_steps(start: Sequence[str], target: Sequence[str], approved: list[Sequence[str]]) -> int:
    """Fewest one-component changes from start to target, visiting only approved states.

    Returns -1 if the target cannot be reached.
    """
    src, dst = tuple(start), tuple(target)
    if src == dst:
        return 0
    allowed = {tuple(s) for s in approved}
    if dst not in allowed:
        return -1

    # Bucket states by "pattern with one position blanked out". Two states are one
    # change apart exactly when they share such a pattern, so neighbours are found
    # without comparing every pair of states.
    buckets: dict[tuple[int, State], list[State]] = defaultdict(list)
    for s in allowed:
        for i in range(len(s)):
            buckets[(i, s[:i] + s[i + 1:])].append(s)

    seen = {src}
    queue: deque[tuple[State, int]] = deque([(src, 0)])
    while queue:
        state, steps = queue.popleft()
        for i in range(len(state)):
            key = (i, state[:i] + state[i + 1:])
            for nxt in buckets.get(key, ()):
                if nxt == dst:
                    return steps + 1
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, steps + 1))
            buckets.pop(key, None)  # every state in this bucket is now queued
    return -1
