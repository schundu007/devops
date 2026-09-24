"""DC-NET-10 Cheapest Route Within Hop Limit — your attempt.

Run your code against the tests:
    make try CHIP=05-networking/DC-NET-10-cheapest-route-hop-limit
"""
from __future__ import annotations


def cheapest_route(
    n: int, routes: list[list[int]], src: int, dst: int, max_transit: int
) -> int:
    """Return the lowest total transfer cost from src to dst.

    routes[i] = [a, b, price] is a one-way transfer from region a to region b.
    The path may pass through at most `max_transit` regions between src and dst.
    Return -1 if no such path exists.
    """
    # TODO
    raise NotImplementedError
