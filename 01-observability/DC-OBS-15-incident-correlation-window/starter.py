"""DC-OBS-15 Incident Correlation Window — your attempt.

Run your code against the tests:
    make try CHIP=01-observability/DC-OBS-15-incident-correlation-window
"""
from __future__ import annotations


def tightest_window(error_times: list[list[int]]) -> list[int]:
    """Return [start, end]: the narrowest time window that holds at least one
    error time from every service (both ends inclusive).

    error_times[s] is service s's error times, sorted ascending, never empty.
    If two windows are equally narrow, return the one that starts earlier.
    """
    # TODO
    raise NotImplementedError
