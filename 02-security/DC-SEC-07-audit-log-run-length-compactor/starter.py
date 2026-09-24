"""DC-SEC-07 Audit Log Run-Length Compactor — your attempt.

Run your code against the tests:
    make try CHIP=02-security/DC-SEC-07-audit-log-run-length-compactor
"""
from __future__ import annotations


def compress(buf: list[str]) -> int:
    """Run-length encode `buf` in place and return the new length.

    Each run of equal characters becomes the character, then the run
    length in decimal digits if the run is longer than 1 ("aaa" -> "a3",
    "b" -> "b"). Use O(1) extra space: write into `buf` itself.
    """
    # TODO
    raise NotImplementedError
