"""DC-PLAT-10 Weighted Canary Router — reference solution."""
from __future__ import annotations

import random
from bisect import bisect_right
from itertools import accumulate


class WeightedRouter:
    def __init__(self, weights: list[int], rng: random.Random | None = None) -> None:
        """weights[i] is backend i's share of traffic. 0 means drained."""
        if not weights or any(w < 0 for w in weights):
            raise ValueError("weights must be a non-empty list of non-negative ints")
        # prefix[i] = weights[0] + ... + weights[i]; backend i owns [prefix[i-1], prefix[i]).
        self._prefix = list(accumulate(weights))
        if self._prefix[-1] == 0:
            raise ValueError("at least one backend needs a positive weight")
        self._rng = rng if rng is not None else random.Random()

    def pick(self) -> int:
        """Choose a backend index with probability weights[i] / sum(weights)."""
        ticket = self._rng.randrange(self._prefix[-1])  # 0 .. total-1
        # First backend whose range ends after the ticket. bisect_right skips
        # zero-weight backends because their prefix equals the previous one.
        return bisect_right(self._prefix, ticket)
