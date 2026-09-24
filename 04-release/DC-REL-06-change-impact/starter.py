"""DC-REL-06 Change Impact Query — your attempt.

Run your code against the tests:
    make try CHIP=04-release/DC-REL-06-change-impact
"""
from __future__ import annotations


def impacts(n: int, deps: list[tuple[int, int]], queries: list[tuple[int, int]]) -> list[bool]:
    """Answer many "does a change to u reach v?" questions.

    Components are 0..n-1. deps holds (upstream, downstream) pairs: downstream uses
    upstream directly. The graph has no cycles. For each query (u, v), return True
    if v depends on u directly or through a chain of other components.
    """
    # TODO
    raise NotImplementedError
