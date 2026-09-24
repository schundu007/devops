"""DC-REL-01 Find the Breaking Commit — your attempt.

Run your code against the tests:
    make try CHIP=04-release/DC-REL-01-breaking-commit
"""
from __future__ import annotations

from typing import Callable


def first_bad_commit(n: int, is_bad: Callable[[int], bool]) -> int:
    """Return the first bad commit among commits 1..n.

    Commits are in history order. Every commit before the first bad one is good,
    and every commit from it onward is bad. Commit n (HEAD) is known to be bad.
    Each is_bad call is one full CI run, so call it as few times as possible.
    """
    # TODO
    raise NotImplementedError
