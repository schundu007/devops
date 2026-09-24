"""DC-PLAT-09 Runner Pool Allocation — your attempt.

Run your code against the tests:
    make try CHIP=03-platform/DC-PLAT-09-runner-pool-allocation
"""
from __future__ import annotations


def busiest_runner(n: int, jobs: list[list[int]]) -> int:
    """Return the runner (0..n-1) that ran the most jobs; lowest number on a tie.

    jobs[i] = [queued_at, planned_end] with unique queued_at values.
    - A job takes the lowest-numbered idle runner.
    - If no runner is idle, it waits for the runner that frees up first
      (lowest number if several free up at the same moment) and then runs
      for its full duration (planned_end - queued_at).
    - A runner that frees up at time t is idle for a job queued at t.
    Return 0 if there are no jobs.
    """
    # TODO
    raise NotImplementedError
