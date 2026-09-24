"""DC-REL-08 Versioned Config Store — reference solution."""
from __future__ import annotations

from bisect import bisect_right


class ConfigStore:
    def __init__(self) -> None:
        # key -> (snapshot ids when the key changed, value set in that snapshot).
        # Only changes are stored, not a full copy per snapshot.
        self._history: dict[str, tuple[list[int], list[str]]] = {}
        self._current = 0                      # id the next snapshot() will return

    def set(self, key: str, value: str) -> None:
        ids, values = self._history.setdefault(key, ([], []))
        if ids and ids[-1] == self._current:   # changed twice before one snapshot: keep the last
            values[-1] = value
        else:
            ids.append(self._current)
            values.append(value)

    def snapshot(self) -> int:
        self._current += 1
        return self._current - 1

    def get(self, key: str, snap_id: int) -> str | None:
        history = self._history.get(key)
        if history is None:
            return None
        ids, values = history
        i = bisect_right(ids, snap_id) - 1     # last change made at or before snap_id
        return values[i] if i >= 0 else None
