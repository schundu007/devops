"""DC-PLAT-10 Weighted Canary Router — your attempt.

Run your code against the tests:
    make try CHIP=03-platform/DC-PLAT-10-weighted-canary-router
"""
from __future__ import annotations

import random


class WeightedRouter:
    def __init__(self, weights: list[int], rng: random.Random | None = None) -> None:
        """weights[i] is backend i's share of traffic; 0 means drained.

        Raise ValueError if weights is empty, has a negative value, or sums to 0.
        Use rng (default: a new random.Random()) as the only source of randomness,
        and draw exactly one number per pick with rng.randrange(sum(weights)).
        """
        # TODO
        raise NotImplementedError

    def pick(self) -> int:
        """Return backend i with probability weights[i] / sum(weights).

        Draw ticket = rng.randrange(total). Backend 0 owns tickets
        [0, w0), backend 1 owns [w0, w0 + w1), and so on.
        """
        # TODO
        raise NotImplementedError
