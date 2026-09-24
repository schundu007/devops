"""DC-SEC-17 Streaming Secret Scanner — your attempt.

Run your code against the tests:
    make try CHIP=02-security/DC-SEC-17-streaming-secret-scanner
"""
from __future__ import annotations


class SecretScanner:
    def __init__(self, patterns: list[str]) -> None:
        """patterns: the fixed strings to look for (at least one, none empty)."""
        # TODO
        pass

    def feed(self, ch: str) -> bool:
        """Append one character to the stream.

        Return True if some pattern equals the text that ends at this character
        (a suffix of everything fed so far), else False.
        """
        # TODO
        raise NotImplementedError
