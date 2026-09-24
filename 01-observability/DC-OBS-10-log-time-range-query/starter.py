"""DC-OBS-10 Log Time-Range Query — your attempt.

Run your code against the tests:
    make try CHIP=01-observability/DC-OBS-10-log-time-range-query
"""
from __future__ import annotations


class LogStore:
    def __init__(self) -> None:
        # TODO
        pass

    def put(self, log_id: int, timestamp: str) -> None:
        """Store a log line's id with its timestamp "YYYY:MM:DD:hh:mm:ss"."""
        # TODO
        raise NotImplementedError

    def retrieve(self, start: str, end: str, granularity: str) -> list[int]:
        """IDs of logs in [start, end], comparing only down to `granularity`.

        granularity is one of "Year", "Month", "Day", "Hour", "Minute", "Second".
        Fields finer than the granularity are ignored on start, end and the logs.
        Return the ids in ascending order.
        """
        # TODO
        raise NotImplementedError
