"""DC-SEC-10 Allow-List Range Tracker — your attempt.

Run your code against the tests:
    make try CHIP=02-security/DC-SEC-10-allow-list-range-tracker
"""
from __future__ import annotations


class AllowList:
    """Tracks allowed values as half-open ranges [lo, hi): lo is in, hi is out."""

    def __init__(self) -> None:
        # TODO
        pass

    def add(self, lo: int, hi: int) -> None:
        """Allow every value in [lo, hi)."""
        # TODO
        raise NotImplementedError

    def remove(self, lo: int, hi: int) -> None:
        """Stop allowing every value in [lo, hi). A range can split in two."""
        # TODO
        raise NotImplementedError

    def covers(self, lo: int, hi: int) -> bool:
        """Return True if every value in [lo, hi) is currently allowed."""
        # TODO
        raise NotImplementedError

    def ranges(self) -> list[tuple[int, int]]:
        """Return the allowed ranges as sorted, merged (lo, hi) pairs.

        Ranges that touch, like (10, 20) and (20, 30), are reported as (10, 30).
        """
        # TODO
        raise NotImplementedError
