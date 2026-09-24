"""Capra Playground export for DC-REL-08 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "design", "fn": "ConfigStore", "params": [], "types": {}, "ret": "value", "cmp": "exact"}


def ops(*calls):
    """ops(("set", "k", "v"), ("snapshot",), ("get", "k", 0)) -> handbook design args."""
    return {"ops": ["ConfigStore"] + [c[0] for c in calls], "vals": [[]] + [list(c[1:]) for c in calls]}


EXAMPLES = [
    {"args": ops(("set", "replicas", "3"), ("snapshot",), ("set", "replicas", "5"), ("get", "replicas", 0), ("snapshot",), ("get", "replicas", 1)),
     "explanation": "Snapshot 0 froze replicas = 3. The later change to 5 lands in snapshot 1, so get(…, 0) is still 3 and get(…, 1) is 5.",
     "why": {"t": "Read an old snapshot", "d": "A later change must not leak into an earlier snapshot."}},
    {"args": ops(("snapshot",), ("set", "image", "api:1.4"), ("get", "image", 0), ("get", "log_level", 0)),
     "explanation": "image was set after snapshot 0 was taken, and log_level was never set: both reads return None.",
     "why": {"t": "Not yet set · unknown key", "d": "Keys that have no value at that snapshot return None."}},
]


def _large():
    rng = random.Random(1146)
    keys = [f"svc{i}.replicas" for i in range(15)]
    calls, snaps = [], 0
    for _ in range(700):
        r = rng.random()
        if r < 0.5:
            calls.append(("set", rng.choice(keys), str(rng.randint(1, 50))))
        elif r < 0.7:
            calls.append(("snapshot",))
            snaps += 1
        elif snaps:
            calls.append(("get", rng.choice(keys), rng.randrange(snaps)))
    return ops(*calls)


TESTS = [
    {"args": ops(("snapshot",), ("get", "x", 0)), "why": {"t": "Empty store", "d": "A snapshot of nothing."}},
    {"args": ops(("set", "x", "1"), ("set", "x", "2"), ("snapshot",), ("get", "x", 0)), "why": {"t": "Two sets, one snapshot", "d": "The last value before the snapshot wins."}},
    {"args": ops(("set", "x", "1"), ("snapshot",), ("snapshot",), ("snapshot",), ("get", "x", 2)), "why": {"t": "Unchanged across snapshots", "d": "A value carries forward until it changes."}},
    {"args": ops(("snapshot",), ("snapshot",), ("set", "x", "a"), ("snapshot",), ("get", "x", 0), ("get", "x", 1), ("get", "x", 2)), "why": {"t": "Boundary", "d": "Snapshots before and after the first set."}},
    {"args": ops(("set", "a", "1"), ("set", "b", "2"), ("snapshot",), ("set", "a", "9"), ("snapshot",), ("get", "b", 1), ("get", "a", 0), ("get", "a", 1)), "why": {"t": "Independent keys", "d": "Changing one key does not affect another."}},
    {"args": ops(("set", "x", ""), ("snapshot",), ("get", "x", 0)), "why": {"t": "Empty string value", "d": "An empty string is a real value, not None."}},
    {"args": ops(("set", "feature.checkout_v2", "off"), ("snapshot",), ("set", "feature.checkout_v2", "on"), ("snapshot",),
                 ("set", "feature.checkout_v2", "off"), ("snapshot",), ("get", "feature.checkout_v2", 0), ("get", "feature.checkout_v2", 1), ("get", "feature.checkout_v2", 2)),
     "why": {"t": "Rollback audit", "d": "A flag turned on and back off: which value did each release see?"}},
    {"args": _large(), "why": {"t": "Large input", "d": "About 700 random sets, snapshots and reads."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "History per key + binary search (Optimal)",
     "description": "Store, for each key, the snapshot ids at which it changed and the values. A second change before the same snapshot overwrites the last entry. get binary searches for the last change at or before snap_id.",
     "time": "O(1) set and snapshot, O(log c) get", "space": "O(total set calls)",
     "keyPoints": ["Store changes, never full copies", "Same-snapshot changes overwrite", "bisect_right - 1 finds the value in force"]},
    {"name": "Copy on snapshot", "slow": True,
     "description": "Keep the current values in a dict and store a full copy of it at every snapshot.",
     "time": "O(keys) snapshot, O(1) get", "space": "O(keys · snapshots)",
     "keyPoints": ["Trivial to write", "Memory explodes with many keys and snapshots"],
     "code": '''from __future__ import annotations


class ConfigStore:
    def __init__(self) -> None:
        self._current: dict[str, str] = {}
        self._snaps: list[dict[str, str]] = []

    def set(self, key: str, value: str) -> None:
        self._current[key] = value

    def snapshot(self) -> int:
        self._snaps.append(dict(self._current))
        return len(self._snaps) - 1

    def get(self, key: str, snap_id: int) -> str | None:
        return self._snaps[snap_id].get(key)
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Copy on snapshot", "idea": "Save a full copy of every value at each snapshot.",
     "time": "O(keys) per snapshot", "space": "O(keys · snapshots)", "use": "Tiny configs with few snapshots."},
    {"name": "Per-key history + binary search", "idea": "Record only changes, tagged with the snapshot id; search the id on read.",
     "time": "O(log c) per get", "space": "O(changes)", "use": "Real stores: etcd revisions, S3 object versions."},
]
