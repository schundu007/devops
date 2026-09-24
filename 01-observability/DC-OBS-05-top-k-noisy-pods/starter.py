"""DC-OBS-05 Top-K Noisy Pods Board — your attempt.

Run your code against the tests:
    make try CHIP=01-observability/DC-OBS-05-top-k-noisy-pods
"""
from __future__ import annotations


class NoisyBoard:
    def __init__(self) -> None:
        # TODO
        pass

    def add(self, key: str, amount: int) -> None:
        """Add `amount` (>= 1) to `key`'s total, creating it at 0 if new."""
        # TODO
        raise NotImplementedError

    def reset(self, key: str) -> None:
        """Forget `key` completely. Unknown keys are ignored."""
        # TODO
        raise NotImplementedError

    def top(self, k: int) -> list[tuple[str, int]]:
        """The k largest totals as (key, total), largest first.

        Break ties by key in ascending order. If fewer than k keys exist, return them all.
        """
        # TODO
        raise NotImplementedError

    def top_total(self, k: int) -> int:
        """Sum of the totals returned by top(k)."""
        # TODO
        raise NotImplementedError
