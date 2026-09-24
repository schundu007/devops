"""DC-SEC-08 IAM Wildcard Matcher — reference solution."""
from __future__ import annotations


def matches(pattern: str, value: str) -> bool:
    """True if `value` matches `pattern` in full.

    `*` matches any run of characters (including none, and including ':' and '/').
    `?` matches exactly one character. Everything else matches itself (case-sensitive).
    """
    p = v = 0
    star = -1        # index of the most recent '*' in pattern, or -1
    star_v = 0       # position in value where that '*' started matching
    while v < len(value):
        if p < len(pattern) and (pattern[p] == "?" or pattern[p] == value[v]):
            p += 1
            v += 1
        elif p < len(pattern) and pattern[p] == "*":
            # Let '*' match nothing for now; remember where to come back.
            star, star_v = p, v
            p += 1
        elif star != -1:
            # Mismatch: let the last '*' swallow one more character and retry.
            star_v += 1
            v = star_v
            p = star + 1
        else:
            return False
    # Value used up: whatever is left of the pattern must be all '*'.
    while p < len(pattern) and pattern[p] == "*":
        p += 1
    return p == len(pattern)
