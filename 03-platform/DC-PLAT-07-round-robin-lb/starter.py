"""DC-PLAT-07 Round-Robin Load Balancer — your attempt.

Run your code against the tests:
    make try CHIP=03-platform/DC-PLAT-07-round-robin-lb
"""
from __future__ import annotations


def busiest_backends(k: int, arrival: list[int], load: list[int]) -> list[int]:
    """Return the backend IDs that served the most requests, in increasing order.

    Request i arrives at arrival[i] (strictly increasing) and keeps a backend
    busy for load[i] time units, so the backend is free again at arrival[i] + load[i].
    Request i tries backend i % k first, then i % k + 1, ... wrapping around to 0.
    It takes the first idle backend. If every backend is busy, it is dropped.
    """
    # TODO
    raise NotImplementedError
