"""DC-NET-06 Single-Point-of-Failure Links — your attempt.

Run your code against the tests:
    make try CHIP=05-networking/DC-NET-06-spof-links
"""
from __future__ import annotations


def critical_links(n: int, links: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Return every link whose failure splits the network, in any order.

    Devices are numbered 0..n-1. links[i] = (a, b) is an undirected link.
    A link is critical if removing it leaves some pair of devices, which were
    connected before, with no path between them. Each link may be returned as
    (a, b) or (b, a). Tip: the tests include a 100,000-device chain, so avoid
    deep recursion.
    """
    # TODO
    raise NotImplementedError
