"""DC-SEC-19 Config Comment Stripper — your attempt.

Run your code against the tests:
    make try CHIP=02-security/DC-SEC-19-config-comment-stripper
"""
from __future__ import annotations


def strip_comments(lines: list[str]) -> list[str]:
    """Remove comments from config source lines.

    - "//" starts a line comment: drop the rest of that line.
    - "/*" starts a block comment that ends at the next "*/" (possibly on a
      later line). The text before and after a multi-line block comment joins
      into one line.
    - Drop lines that end up empty.
    The first comment marker wins: "//" inside a block, or "/*" after "//", is plain comment text.
    Every "/*" is closed. There are no string literals.
    """
    # TODO
    raise NotImplementedError
