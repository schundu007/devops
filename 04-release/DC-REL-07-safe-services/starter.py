"""DC-REL-07 Safe Services Finder — your attempt.

Run your code against the tests:
    make try CHIP=04-release/DC-REL-07-safe-services
"""
from __future__ import annotations


def safe_services(waits_on: list[list[int]]) -> list[int]:
    """Return the safe services, sorted ascending.

    Services are 0..n-1. waits_on[i] lists the services i waits for before it can
    start. A service is safe if every chain of waits starting from it ends at a
    service that waits on nothing, so it can never get stuck in a cycle.
    """
    # TODO
    raise NotImplementedError
