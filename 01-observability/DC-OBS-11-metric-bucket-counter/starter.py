"""DC-OBS-11 Metric Bucket Counter — your attempt.

Run your code against the tests:
    make try CHIP=01-observability/DC-OBS-11-metric-bucket-counter
"""
from __future__ import annotations

BUCKET_SECONDS = {"minute": 60, "hour": 3600, "day": 86400}


class EventCounter:
    def __init__(self) -> None:
        # TODO
        pass

    def record(self, name: str, time: int) -> None:
        """Store one event of `name` at `time` (seconds). Times may arrive out of order."""
        # TODO
        raise NotImplementedError

    def counts(self, step: str, name: str, start: int, end: int) -> list[int]:
        """Count events of `name` in each bucket of `step` ("minute", "hour" or "day").

        Buckets start at `start`: [start, start+size-1], [start+size, ...], and the last
        one is cut off at `end`. Both `start` and `end` are inclusive.
        """
        # TODO
        raise NotImplementedError
