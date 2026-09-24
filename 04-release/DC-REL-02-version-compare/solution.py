"""DC-REL-02 Version Comparator — reference solution."""
from __future__ import annotations


def compare_versions(a: str, b: str) -> int:
    """Return 1 if a is newer than b, -1 if older, 0 if they are the same release."""
    pa, pb = a.split("."), b.split(".")
    # Walk both lists together; a missing part counts as 0 ("1.2" == "1.2.0").
    for i in range(max(len(pa), len(pb))):
        x = int(pa[i]) if i < len(pa) else 0   # int() drops leading zeros: "010" -> 10
        y = int(pb[i]) if i < len(pb) else 0
        if x != y:
            return 1 if x > y else -1
    return 0
