"""DC-NET-09 Most Reliable Path — your attempt.

Run your code against the tests:
    make try CHIP=05-networking/DC-NET-09-most-reliable-path
"""
from __future__ import annotations


def most_reliable_path(
    n: int, links: list[list[int]], success: list[float], src: int, dst: int
) -> float:
    """Return the highest end-to-end success probability of any path from src to dst.

    links[i] = [a, b] is a two-way link that works with probability success[i].
    Nodes are 0..n-1. Return 0.0 if dst cannot be reached.
    """
    # TODO
    raise NotImplementedError
