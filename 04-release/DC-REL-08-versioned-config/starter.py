"""DC-REL-08 Versioned Config Store — your attempt.

Run your code against the tests:
    make try CHIP=04-release/DC-REL-08-versioned-config
"""
from __future__ import annotations


class ConfigStore:
    def __init__(self) -> None:
        # TODO
        pass

    def set(self, key: str, value: str) -> None:
        """Set key to value in the working copy (it becomes part of the next snapshot)."""
        # TODO
        raise NotImplementedError

    def snapshot(self) -> int:
        """Freeze the working copy. Return its id: 0 for the first call, then 1, 2, ..."""
        # TODO
        raise NotImplementedError

    def get(self, key: str, snap_id: int) -> str | None:
        """Value of key as it was in snapshot snap_id, or None if it was not set then.

        snap_id is always an id that snapshot() has already returned.
        """
        # TODO
        raise NotImplementedError
