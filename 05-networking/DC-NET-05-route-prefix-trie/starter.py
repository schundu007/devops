"""DC-NET-05 Route Prefix Trie — your attempt.  (added: the handbook has no stored starter)

Signatures match Source: Handbook #36 Implement Trie (Prefix Tree).
Run your code against the tests:
    make try CHIP=05-networking/DC-NET-05-route-prefix-trie
"""


class Trie:
    def __init__(self):
        # TODO
        pass

    def insert(self, word: str) -> None:
        """Add one route (word) to the table."""
        # TODO
        raise NotImplementedError

    def search(self, word: str) -> bool:
        """True if this exact route (word) was inserted."""
        # TODO
        raise NotImplementedError

    def startsWith(self, prefix: str) -> bool:
        """True if any inserted route (word) starts with prefix."""
        # TODO
        raise NotImplementedError
