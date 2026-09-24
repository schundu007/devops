"""DC-SEC-04 Domain Suffix Compactor — reference solution."""
from __future__ import annotations


def _normalize(host: str) -> str:
    # DNS names are case-insensitive, and a trailing dot only marks the root.
    return host.lower().rstrip(".")


def compact(hostnames: list[str]) -> list[str]:
    """Hostnames that are not a label-suffix of another hostname, sorted.

    "prod.example.com" is covered by "api.prod.example.com", so only the
    longer name needs to be stored. "ample.com" is NOT covered by
    "example.com": suffixes are compared by whole labels.
    """
    names = sorted({_normalize(h) for h in hostnames if _normalize(h)})
    # Reverse trie over labels: com -> example -> prod -> api.
    root: dict[str, dict] = {}
    ends: list[tuple[str, dict]] = []
    for name in names:
        node = root
        for label in reversed(name.split(".")):
            node = node.setdefault(label, {})
        ends.append((name, node))
    # A name is covered if its last node has children: a longer name passes through it.
    return [name for name, node in ends if not node]


def encoded_length(hostnames: list[str]) -> int:
    """Length of a string holding every kept name, each followed by one '#'."""
    return sum(len(name) + 1 for name in compact(hostnames))
