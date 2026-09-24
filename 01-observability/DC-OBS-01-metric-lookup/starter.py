"""DC-OBS-01 Metric Point-in-Time Lookup — your attempt.

Run your code against the tests:
    make try CHIP=01-observability/DC-OBS-01-metric-lookup
"""
from __future__ import annotations


class MetricStore:
    def __init__(self) -> None:
        # TODO: choose a structure that makes both calls fast.
        pass

    def record(self, metric: str, value: float, timestamp: int) -> None:
        """Store one sample.

        For each metric, calls arrive with strictly increasing timestamps
        (a scraper never goes back in time).
        """
        # TODO
        raise NotImplementedError

    def value_at(self, metric: str, timestamp: int) -> float | None:
        """Return the latest value of `metric` recorded at or before `timestamp`.

        Return None if the metric is unknown or has no sample that early.
        """
        # TODO
        raise NotImplementedError
