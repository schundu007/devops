"""DC-PLAT-08 Weighted Job Dispatcher — your attempt.

Run your code against the tests:
    make try CHIP=03-platform/DC-PLAT-08-weighted-job-dispatcher
"""
from __future__ import annotations


def assign_jobs(weights: list[int], durations: list[int]) -> list[int]:
    """Return the worker index that runs each job, in job order.

    Worker i has cost weight weights[i]. Job j is queued at second j and
    runs for durations[j] seconds. Jobs are dispatched strictly in order.
    A job goes to the idle worker with the smallest weight (ties: smallest
    index). If no worker is idle, the job waits until one finishes, and
    starts at that moment. A worker finishing at t is idle at t.
    """
    # TODO
    raise NotImplementedError
