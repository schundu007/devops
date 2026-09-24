"""DC-SEC-14 Identity Linker — reference solution."""
from __future__ import annotations


def link_identities(accounts: list[list[str]]) -> list[list[str]]:
    """Merge accounts that share any email.

    Returns [name, *sorted_emails] per person, sorted by (name, first email).
    """
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]  # path halving
            x = parent[x]
        return x

    owner: dict[str, str] = {}  # email -> display name
    for name, *emails in accounts:
        for email in emails:
            parent.setdefault(email, email)
            owner[email] = name
        # Every email in one account belongs to the same person: link them to the first.
        root = find(emails[0])
        for email in emails[1:]:
            other = find(email)
            if other != root:
                parent[other] = root

    groups: dict[str, list[str]] = {}
    for email in parent:
        groups.setdefault(find(email), []).append(email)
    merged = [[owner[root], *sorted(emails)] for root, emails in groups.items()]
    return sorted(merged, key=lambda row: (row[0], row[1]))
