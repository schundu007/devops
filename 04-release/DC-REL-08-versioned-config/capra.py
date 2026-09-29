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

VARIANT_TITLE = "Snapshot reads"
VARIANT_APPROACH = "History per key + binary search · O(log c) get · O(changes)"


def _diff_large():
    rng = random.Random(808)
    keys = [f"svc{i}.image" for i in range(25)]
    calls, snaps = [], 0
    for _ in range(700):
        r = rng.random()
        if r < 0.55:
            calls.append(("set", rng.choice(keys), f"v{rng.randint(1, 4)}"))
        elif r < 0.75 or snaps < 2:
            calls.append(("snapshot",))
            snaps += 1
        else:
            calls.append(("diff", rng.randrange(snaps), rng.randrange(snaps)))
    return ops(*calls)


def _tomb_large():
    rng = random.Random(1146)
    keys = [f"flag.{i}" for i in range(20)]
    calls, snaps = [], 0
    for _ in range(800):
        r = rng.random()
        if r < 0.4:
            calls.append(("set", rng.choice(keys), rng.choice(["on", "off"])))
        elif r < 0.55:
            calls.append(("delete", rng.choice(keys)))
        elif r < 0.7:
            calls.append(("snapshot",))
            snaps += 1
        elif snaps:
            calls.append(("get", rng.choice(keys), rng.randrange(snaps)))
    return ops(*calls)


VARIANTS = [
    {
        "key": "snapshot-diff",
        "title": "What changed between two releases",
        "approach": "Keys changed per snapshot + history lookups · O(c log c) per diff · O(changes)",
        "spec": {"kind": "design", "fn": "ConfigStore", "params": []},
        "statement": (
            "List which settings differ between two snapshots, so on-call can compare the release that worked with the one that broke.\n"
            "\n"
            "### Methods\n"
            "- `set(key, value)`: change the current value\n"
            "- `snapshot()`: freeze the current values and return the snapshot id `0, 1, 2, …`\n"
            "- `diff(a, b)`: the sorted list of keys whose value differs between snapshots `a` and `b`\n"
            "\n"
            "### Rules\n"
            "- A key that exists in only one of the snapshots differs\n"
            "- `a` may be larger than `b`; `diff(a, a)` is `[]`\n"
            "- A key set to a new value and then back to the old one before the later snapshot is **not** a difference"
        ),
        "examples": [
            {"args": ops(("set", "replicas", "3"), ("set", "image", "api:1.4"), ("snapshot",), ("set", "image", "api:1.5"),
                         ("set", "timeout", "30s"), ("snapshot",), ("diff", 0, 1)),
             "explanation": "image changed and timeout appeared; replicas did not change.",
             "why": {"t": "Changed and new keys", "d": "Both a new value and a new key count."}},
            {"args": ops(("set", "flag", "off"), ("snapshot",), ("set", "flag", "on"), ("snapshot",), ("set", "flag", "off"),
                         ("snapshot",), ("diff", 0, 2), ("diff", 2, 1)),
             "explanation": "The flag went on and back off, so snapshots 0 and 2 agree. Snapshots 1 and 2 differ, in either order.",
             "why": {"t": "Set back · Reversed ids", "d": "Touched is not the same as different."}},
        ],
        "constraints": ["At most 2000 calls", "Snapshot ids passed to diff exist", "Keys and values are strings"],
        "hints": [
            "Only keys set in the snapshots after the earlier id and up to the later one can differ.",
            "Record, per snapshot id, which keys were set while it was the current one.",
            "For each candidate, compare its value at both ids with the same bisect lookup as get.",
        ],
        "tests": [
            {"args": ops(("snapshot",), ("diff", 0, 0)), "why": {"t": "Same snapshot", "d": "A snapshot never differs from itself."}},
            {"args": ops(("snapshot",), ("snapshot",), ("diff", 0, 1)), "why": {"t": "Empty store", "d": "Nothing set: no differences."}},
            {"args": ops(("snapshot",), ("set", "a", "1"), ("snapshot",), ("diff", 1, 0)), "why": {"t": "Key appears", "d": "Missing in one snapshot, present in the other."}},
            {"args": ops(("set", "a", "1"), ("set", "a", "2"), ("set", "a", "1"), ("snapshot",), ("snapshot",), ("diff", 0, 1)),
             "why": {"t": "Churn before a snapshot", "d": "Several sets in one epoch; only the final value counts."}},
            {"args": ops(("set", "b", "1"), ("set", "a", "1"), ("snapshot",), ("set", "b", "2"), ("set", "a", "2"), ("set", "c", "x"), ("snapshot",),
                         ("snapshot",), ("diff", 0, 2), ("diff", 1, 2)),
             "why": {"t": "Sorted output · Gap", "d": "Keys come back sorted; unchanged snapshots in between add nothing."}},
            {"args": ops(("set", "x", ""), ("snapshot",), ("set", "x", "0"), ("snapshot",), ("diff", 0, 1)), "why": {"t": "Empty string value", "d": "An empty string is a value, not absence."}},
            {"args": _diff_large(), "why": {"t": "Large input", "d": "About 700 sets, snapshots and diffs over 25 keys."}},
        ],
        "solutions": [
            {"name": "Changed keys per snapshot + history (Optimal)",
             "description": "Keep each key's (snapshot id, value) history and, per snapshot id, the set of keys changed while it was current. diff unions the changed keys in (lo, hi] and keeps those whose values really differ.",
             "time": "O(1) set, O(c log c) diff for c candidate keys", "space": "O(changes)",
             "keyPoints": ["Only keys touched between the two ids are candidates", "Compare values to drop set-and-set-back", "Normalize a > b by swapping"],
             "code": '''from bisect import bisect_right


class ConfigStore:
    def __init__(self):
        self.hist = {}
        self.changed = [set()]
        self.cur = 0

    def set(self, key, value):
        ids, vals = self.hist.setdefault(key, ([], []))
        if ids and ids[-1] == self.cur:
            vals[-1] = value
        else:
            ids.append(self.cur)
            vals.append(value)
        self.changed[self.cur].add(key)

    def snapshot(self):
        self.cur += 1
        self.changed.append(set())
        return self.cur - 1

    def _get(self, key, snap):
        ids, vals = self.hist[key]
        i = bisect_right(ids, snap) - 1
        return vals[i] if i >= 0 else None

    def diff(self, a, b):
        lo, hi = min(a, b), max(a, b)
        cand = set()
        for s in range(lo + 1, hi + 1):
            cand |= self.changed[s]
        return sorted(k for k in cand if self._get(k, lo) != self._get(k, hi))
'''},
            {"name": "Copy on snapshot", "slow": True,
             "description": "Store a full copy of the values at every snapshot and compare the two copies key by key.",
             "time": "O(keys) snapshot and diff", "space": "O(keys · snapshots)",
             "keyPoints": ["Trivial diff", "Memory grows with every snapshot"],
             "code": '''class ConfigStore:
    def __init__(self):
        self.current = {}
        self.snaps = []

    def set(self, key, value):
        self.current[key] = value

    def snapshot(self):
        self.snaps.append(dict(self.current))
        return len(self.snaps) - 1

    def diff(self, a, b):
        x, y = self.snaps[a], self.snaps[b]
        return sorted(k for k in set(x) | set(y) if x.get(k) != y.get(k))
'''},
        ],
        "starter": '''class ConfigStore:
    def __init__(self):
        pass

    def set(self, key, value):
        pass

    def snapshot(self):
        pass

    def diff(self, a, b):
        pass
''',
    },
    {
        "key": "tombstones",
        "title": "Deleted keys (tombstones)",
        "approach": "History per key with tombstones + binary search · O(log c) get · O(changes)",
        "spec": {"kind": "design", "fn": "ConfigStore", "params": []},
        "statement": (
            "Support deletes: an old snapshot must still show a key that was deleted later, like an etcd read at an older revision.\n"
            "\n"
            "### Methods\n"
            "- `set(key, value)`: change the current value\n"
            "- `delete(key)`: remove the key from the current values\n"
            "- `snapshot()`: freeze the current values and return the snapshot id `0, 1, 2, …`\n"
            "- `get(key, snap_id)`: the key's value in that snapshot; `None` if it did not exist then\n"
            "\n"
            "### Rules\n"
            "- Deleting a missing key does nothing"
        ),
        "examples": [
            {"args": ops(("set", "legacy_auth", "on"), ("snapshot",), ("delete", "legacy_auth"), ("snapshot",),
                         ("get", "legacy_auth", 0), ("get", "legacy_auth", 1)),
             "explanation": "Snapshot 0 still has the key; snapshot 1 was taken after the delete.",
             "why": {"t": "Delete after a snapshot", "d": "A delete must not reach back into older snapshots."}},
            {"args": ops(("set", "x", "1"), ("delete", "x"), ("set", "x", "2"), ("snapshot",), ("get", "x", 0)),
             "explanation": "Deleted and recreated in the same epoch: only the final state, 2, is frozen.",
             "why": {"t": "Delete then recreate", "d": "The last change before a snapshot wins, deletes included."}},
        ],
        "constraints": ["At most 2000 calls", "get uses an existing snapshot id", "Keys and values are strings"],
        "hints": [
            "Store a delete as one more change in the key's history, with the value None.",
            "Reads stay the same: bisect for the last change at or before snap_id and return its value, which may be None.",
        ],
        "tests": [
            {"args": ops(("delete", "x"), ("snapshot",), ("get", "x", 0)), "why": {"t": "Delete missing key", "d": "Nothing to delete: still None."}},
            {"args": ops(("set", "x", "1"), ("delete", "x"), ("snapshot",), ("get", "x", 0)), "why": {"t": "Set then delete", "d": "Both in one epoch: the key is gone."}},
            {"args": ops(("set", "x", "1"), ("snapshot",), ("delete", "x"), ("delete", "x"), ("snapshot",), ("set", "x", "3"), ("snapshot",),
                         ("get", "x", 0), ("get", "x", 1), ("get", "x", 2)),
             "why": {"t": "Delete twice, then recreate", "d": "Three snapshots: present, gone, back."}},
            {"args": ops(("set", "a", "1"), ("set", "b", "2"), ("snapshot",), ("delete", "a"), ("snapshot",), ("get", "b", 1), ("get", "a", 1)),
             "why": {"t": "Independent keys", "d": "Deleting one key leaves another alone."}},
            {"args": ops(("set", "x", ""), ("snapshot",), ("delete", "x"), ("snapshot",), ("get", "x", 0), ("get", "x", 1)),
             "why": {"t": "Empty string vs deleted", "d": "An empty value is not the same as a deleted key."}},
            {"args": ops(("snapshot",), ("snapshot",), ("get", "never", 1)), "why": {"t": "Unknown key", "d": "A key never set returns None."}},
            {"args": _tomb_large(), "why": {"t": "Large input", "d": "About 800 sets, deletes, snapshots and reads."}},
        ],
        "solutions": [
            {"name": "History with tombstones (Optimal)",
             "description": "Each key keeps (snapshot id, value) changes, where a delete records None. Same-epoch changes overwrite the last entry; get bisects.",
             "time": "O(1) set and delete, O(log c) get", "space": "O(changes)",
             "keyPoints": ["A delete is a change to None", "Skip deletes of keys that are already absent", "bisect_right - 1 finds the state in force"],
             "code": '''from bisect import bisect_right


class ConfigStore:
    def __init__(self):
        self.hist = {}
        self.cur = 0

    def _write(self, key, value):
        ids, vals = self.hist.setdefault(key, ([], []))
        if ids and ids[-1] == self.cur:
            vals[-1] = value
        else:
            ids.append(self.cur)
            vals.append(value)

    def set(self, key, value):
        self._write(key, value)

    def delete(self, key):
        if key in self.hist and self.hist[key][1][-1] is not None:
            self._write(key, None)

    def snapshot(self):
        self.cur += 1
        return self.cur - 1

    def get(self, key, snap_id):
        if key not in self.hist:
            return None
        ids, vals = self.hist[key]
        i = bisect_right(ids, snap_id) - 1
        return vals[i] if i >= 0 else None
'''},
            {"name": "Copy on snapshot", "slow": True,
             "description": "Keep the current values in a dict, delete from it directly, and copy the whole dict at each snapshot.",
             "time": "O(keys) snapshot, O(1) get", "space": "O(keys · snapshots)",
             "keyPoints": ["Deletes are just dict pops", "Memory grows with every snapshot"],
             "code": '''class ConfigStore:
    def __init__(self):
        self.current = {}
        self.snaps = []

    def set(self, key, value):
        self.current[key] = value

    def delete(self, key):
        self.current.pop(key, None)

    def snapshot(self):
        self.snaps.append(dict(self.current))
        return len(self.snaps) - 1

    def get(self, key, snap_id):
        return self.snaps[snap_id].get(key)
'''},
        ],
        "starter": '''class ConfigStore:
    def __init__(self):
        pass

    def set(self, key, value):
        pass

    def delete(self, key):
        pass

    def snapshot(self):
        pass

    def get(self, key, snap_id):
        pass
''',
    },
]
