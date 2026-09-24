"""DC-NET-07 Heal a Network Partition — your attempt.

Run your code against the tests:
    make try CHIP=05-networking/DC-NET-07-heal-partition
"""
from __future__ import annotations


def min_link_moves(n: int, links: list[tuple[int, int]]) -> int:
    """Return the fewest link moves that connect all n devices, or -1 if impossible.

    Devices are 0..n-1; links[i] = (a, b) is an undirected cable. One move =
    unplug one existing cable and plug it between any two devices. No new cables
    can be added.
    """
    # TODO
    raise NotImplementedError
