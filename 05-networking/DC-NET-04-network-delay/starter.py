"""DC-NET-04 Network Delay Time — your attempt.

Run your code against the tests:
    make try CHIP=05-networking/DC-NET-04-network-delay
"""
from __future__ import annotations


def network_delay(links: list[tuple[int, int, int]], n: int, source: int) -> int:
    """Return the time (ms) until a signal sent from `source` has reached every router.

    links[i] = (u, v, ms): a one-way link from router u to router v with delay ms (ms >= 0).
    Routers are numbered 1..n. The signal travels along every link at once, so each
    router hears it by its fastest path. Return -1 if some router is never reached.
    """
    # TODO
    raise NotImplementedError
