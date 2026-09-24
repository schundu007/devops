"""DC-SEC-08 IAM Wildcard Matcher — your attempt.

Run your code against the tests:
    make try CHIP=02-security/DC-SEC-08-iam-wildcard-matcher
"""
from __future__ import annotations


def matches(pattern: str, value: str) -> bool:
    """Return True if the whole of `value` matches `pattern`.

    `*` matches any sequence of characters, including an empty one and
    including ':' and '/'. `?` matches exactly one character. Every other
    character matches only itself (case-sensitive).
    """
    # TODO
    raise NotImplementedError
