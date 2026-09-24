"""DC-SEC-20 Nested Config Parser — your attempt.

Run your code against the tests:
    make try CHIP=02-security/DC-SEC-20-nested-config-parser
"""
from __future__ import annotations

Nested = int | list  # an int, or a list of Nested


def parse(s: str, max_depth: int = 64) -> Nested:
    """Parse a serialized nested value into Python ints and lists.

    s is either an integer ("-42") or a list ("[1,[2,[3]],[]]") with no spaces.
    A bare integer has depth 0; "[1]" has depth 1; "[[1]]" has depth 2.
    Raise ValueError if the depth is greater than max_depth.
    """
    # TODO
    raise NotImplementedError
