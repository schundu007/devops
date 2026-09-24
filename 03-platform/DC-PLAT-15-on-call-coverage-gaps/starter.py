"""DC-PLAT-15 On-Call Coverage Gaps — your attempt.

Run your code against the tests:
    make try CHIP=03-platform/DC-PLAT-15-on-call-coverage-gaps
"""
from __future__ import annotations


def coverage_gaps(schedules: list[list[list[int]]]) -> list[list[int]]:
    """Return every [start, end] with nobody on call, in time order.

    schedules[p] lists engineer p's shifts as [start, end] (end exclusive),
    sorted by start and not overlapping each other. Only gaps between the first
    shift start and the last shift end count; a gap must have positive length
    (shifts that touch, like [0, 8] and [8, 16], leave no gap).
    """
    # TODO
    raise NotImplementedError
