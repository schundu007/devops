"""DC-SEC-13 Secret Exposure Over Time — your attempt.

Run your code against the tests:
    make try CHIP=02-security/DC-SEC-13-secret-exposure-over-time
"""
from __future__ import annotations


def exposed(n: int, sessions: list[list[int]], first: int) -> list[int]:
    """Return every party that ends up holding the secret, sorted ascending.

    Parties are 0..n-1. Party 0 and party `first` hold it at time 0.
    sessions[i] = [a, b, t]: a and b connect at time t. If either side holds
    the secret at that moment, both do afterwards. Sessions at the same time
    can pass the secret along a chain instantly.
    """
    # TODO
    raise NotImplementedError
