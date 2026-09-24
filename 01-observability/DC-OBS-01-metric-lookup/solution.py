"""DC-OBS-01 Metric Point-in-Time Lookup — reference solution."""
from __future__ import annotations

from bisect import bisect_right


class MetricStore:
    def __init__(self) -> None:
        # metric name -> (sorted sample times, values in the same order).
        # Two parallel lists keep bisect working on plain ints.
        self._series: dict[str, tuple[list[int], list[float]]] = {}

    def record(self, metric: str, value: float, timestamp: int) -> None:
        """Store one sample. Times for a metric arrive in strictly increasing order."""
        times, values = self._series.setdefault(metric, ([], []))
        # Arrival order is time order, so appending keeps the list sorted.
        times.append(timestamp)
        values.append(value)

    def value_at(self, metric: str, timestamp: int) -> float | None:
        """Latest value of `metric` recorded at or before `timestamp`, else None."""
        series = self._series.get(metric)
        if series is None:
            return None
        times, values = series
        # bisect_right returns the first index with time > timestamp,
        # so the index just before it is the last sample at or before it.
        i = bisect_right(times, timestamp) - 1
        return values[i] if i >= 0 else None
