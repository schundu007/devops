"""DC-OBS-12 Late & Corrected Samples — your attempt.

Run your code against the tests:
    make try CHIP=01-observability/DC-OBS-12-late-corrected-samples
"""
from __future__ import annotations


class SampleTracker:
    def __init__(self) -> None:
        # TODO
        pass

    def update(self, timestamp: int, value: float) -> None:
        """Record a sample. Timestamps may arrive late (out of order).

        If `timestamp` was seen before, this is a correction: the new value replaces the old one.
        """
        # TODO
        raise NotImplementedError

    def current(self) -> float:
        """Value at the newest timestamp seen so far."""
        # TODO
        raise NotImplementedError

    def maximum(self) -> float:
        """Highest value across all timestamps, using corrected values only."""
        # TODO
        raise NotImplementedError

    def minimum(self) -> float:
        """Lowest value across all timestamps, using corrected values only."""
        # TODO
        raise NotImplementedError
