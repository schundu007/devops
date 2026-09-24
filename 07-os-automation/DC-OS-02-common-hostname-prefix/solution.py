"""DC-OS-02 Common Hostname Prefix — reference solution (vertical scan)."""
from __future__ import annotations


def common_prefix(hosts: list[str]) -> str:
    """Longest string that every hostname starts with ("" if none or no hosts)."""
    if not hosts:
        return ""
    first = hosts[0]
    for i, ch in enumerate(first):
        # Compare column i across every host; stop at the first mismatch or a short host.
        for h in hosts[1:]:
            if i == len(h) or h[i] != ch:
                return first[:i]
    return first  # the first host is a prefix of every other host
