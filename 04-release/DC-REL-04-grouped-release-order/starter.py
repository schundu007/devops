"""DC-REL-04 Grouped Release Order — your attempt.

Run your code against the tests:
    make try CHIP=04-release/DC-REL-04-grouped-release-order
"""
from __future__ import annotations


def release_order(n: int, m: int, service: list[int], before: list[list[int]]) -> list[int]:
    """Order the release-train steps 0..n-1.

    service[i]: which of the m services (0..m-1) step i belongs to, or -1 if the step
    belongs to no service. before[i]: steps that must run before step i.

    Return any order of all n steps where every service's steps are next to each
    other (contiguous) and every before[] rule holds. Return [] if none exists.
    """
    # TODO
    raise NotImplementedError
