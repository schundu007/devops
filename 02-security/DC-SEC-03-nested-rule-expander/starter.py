"""DC-SEC-03 Nested Rule Expander — your attempt.

Run your code against the tests:
    make try CHIP=02-security/DC-SEC-03-nested-rule-expander
"""
from __future__ import annotations


def expand(template: str, max_output: int = 100_000) -> str:
    """Expand every `k[body]` block into `body` repeated k times.

    Blocks can nest. Characters outside blocks are copied as they are.
    Raise ValueError if the result, or any block while it is being expanded,
    would be longer than `max_output`.
    """
    # TODO
    raise NotImplementedError
