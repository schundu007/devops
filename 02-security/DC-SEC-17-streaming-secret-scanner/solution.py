"""DC-SEC-17 Streaming Secret Scanner — reference solution."""
from __future__ import annotations

from collections import deque

_END = "$end"  # end-of-pattern marker; trie edges are single characters, so it never clashes


class SecretScanner:
    def __init__(self, patterns: list[str]) -> None:
        # Reverse trie: insert each pattern backwards, so we can walk from the
        # newest character toward older ones.
        self.root: dict = {}
        for p in patterns:
            node = self.root
            for ch in reversed(p):
                node = node.setdefault(ch, {})
            node[_END] = True
        # Only the last max-length characters can ever complete a match.
        self.recent: deque[str] = deque(maxlen=max(map(len, patterns)))

    def feed(self, ch: str) -> bool:
        """Add one character; True if some pattern ends exactly at it."""
        self.recent.append(ch)
        node = self.root
        for c in reversed(self.recent):  # newest first
            node = node.get(c)
            if node is None:
                return False
            if _END in node:
                return True
        return False
