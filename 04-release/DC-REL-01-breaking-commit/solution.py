"""DC-REL-01 Find the Breaking Commit — reference solution."""
from __future__ import annotations

from typing import Callable


def first_bad_commit(n: int, is_bad: Callable[[int], bool]) -> int:
    """Return the first bad commit among 1..n. Commit n is known to be bad."""
    lo, hi = 1, n  # the answer is always inside [lo, hi]
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if is_bad(mid):
            hi = mid          # mid is bad: the first bad one is mid or earlier
        else:
            lo = mid + 1      # mid is good: the first bad one is after it
    return lo
