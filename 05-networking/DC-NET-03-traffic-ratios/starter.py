"""DC-NET-03 Capacity & Traffic Ratio Calculator — your attempt.

Run your code against the tests:
    make try CHIP=05-networking/DC-NET-03-traffic-ratios
"""
from __future__ import annotations


def calc_ratios(
    facts: list[tuple[str, str]],
    values: list[float],
    queries: list[tuple[str, str]],
) -> list[float]:
    """facts[i] = (a, b) with values[i] = v means "one a holds v of b" (v > 0).

    For each query (x, y), return how many y one x holds, derived by chaining facts
    (forwards or backwards). Return -1.0 if x or y never appears in any fact, or if
    no chain connects them. (x, x) is 1.0 when x is known.
    """
    # TODO
    raise NotImplementedError
