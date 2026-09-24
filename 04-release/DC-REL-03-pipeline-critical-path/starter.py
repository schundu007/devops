"""DC-REL-03 Pipeline Critical Path — your attempt.

Run your code against the tests:
    make try CHIP=04-release/DC-REL-03-pipeline-critical-path
"""
from __future__ import annotations


def pipeline_time(n: int, deps: list[tuple[int, int]], duration: list[int]) -> int:
    """Minimum total time to run pipeline stages 0..n-1.

    deps: (a, b) means stage b cannot start until stage a has finished.
    duration[i]: minutes stage i takes. Any number of stages may run in parallel.
    The dependency graph has no cycles.
    """
    # TODO
    raise NotImplementedError
