Source: New

# DC-REL-08 · Versioned Config Store

## 1. Header
| | |
|---|---|
| Chip ID | DC-REL-08 |
| Difficulty | Medium |
| Pattern | Binary search per key |
| Track | Release & CI/CD (REL) |
| Classic pattern | LeetCode 1146 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
At 16:05 the new checkout flow goes live by flipping `flag.new_checkout=on`. At 16:20 someone
lowers `checkout.timeout_ms` from 800 to 300 to "fail fast". By 16:30 checkout errors are at 9%.
The config service snapshots its state on every release, and you need to roll back to the config
exactly as it was at revision 0, the last known-good one. The service holds 40,000 keys and
keeps thousands of snapshots, so it cannot afford a full copy per snapshot.

## 3. Why This Is DevOps
**Production reality:** Config and state stores keep history so you can read the past: "what
was this key at revision N?" Storing a full copy per revision wastes memory, because most keys
don't change between revisions. Instead each key keeps a short list of (revision, value)
changes, sorted by revision. To read a key at revision N, binary search that key's list for
the last change at or before N. Rollbacks, audits and "what changed?" diffs all use this lookup.

**Where you see it:** etcd, which keeps a revision number for the whole store and can read a
key at a past revision (`etcdctl get --rev=N`) until compaction removes it. Also Terraform
state versions (with S3 bucket versioning or Terraform Cloud), S3 object versioning, and
Consul KV `ModifyIndex`.

**Reality check:** etcd increases its revision on every write, not only on explicit snapshots,
and it drops old revisions when compaction runs, so reading an old revision can fail. This
chip bumps the revision only on `snapshot()` and keeps history forever.

**What breaks if you get it wrong:** Read the value *after* revision N instead of at N, and
the "rollback" re-applies the bad timeout. Checkout stays broken while everyone believes the
rollback is done.

## 4. Problem Statement
Build a `ConfigStore` with a working copy and numbered snapshots.

- `set(key, value)`: change a key in the working copy.
- `snapshot()`: freeze the working copy and return its id. The first call returns `0`, the
  next `1`, and so on. Later `set` calls do not change frozen snapshots.
- `get(key, snap_id)`: return the value `key` had in snapshot `snap_id`, or `None` if the key
  had not been set by then.

If a key is set several times before one snapshot, the snapshot keeps the last value.

## 5. Input / Output format and Constraints
- `ConfigStore()`, `set(key: str, value: str) -> None`, `snapshot() -> int`, `get(key: str, snap_id: int) -> str | None`.
- Up to `10^5` calls in total, with up to `5 * 10^4` distinct keys.
- `get` is only called with an id that `snapshot()` has already returned.
- Keys and values are non-empty strings of at most 256 characters.

## 6. Examples
**Example 1**
```
set("replicas", "3");  snapshot() -> 0
set("replicas", "5");  snapshot() -> 1
get("replicas", 0) -> "3"
get("replicas", 1) -> "5"
```

**Example 2: set after the snapshot (edge case)**
```
snapshot() -> 0
set("log_level", "debug");  snapshot() -> 1
get("log_level", 0) -> None     # it did not exist yet when snapshot 0 was taken
get("log_level", 1) -> "debug"
```

**Example 3: last write wins**
```
set("image", "api:1.4.0");  set("image", "api:1.4.1");  snapshot() -> 0
get("image", 0) -> "api:1.4.1"
```

## 7. Starter Code
See [`starter.py`](starter.py): the `ConfigStore` class with `set`, `snapshot` and `get`
signatures, docstrings and type hints.

```bash
make try CHIP=04-release/DC-REL-08-versioned-config
```

## 8. Hints
1. **Nudge:** Copying all keys on each snapshot is easy but costs memory. What actually changes between snapshots?
2. **Pattern:** Store only the changes: for each key, a list of (snapshot id, value) sorted by
   id. A read at snapshot N is "the last change at or before N": binary search.
3. **Near-solution:** Keep the current snapshot id `cur`. `set` appends `(cur, value)`, or
   overwrites the last entry if it is already for `cur`. `get` does
   `i = bisect_right(ids, snap_id) - 1` and returns `values[i]` if `i >= 0`, else `None`.

## 9. Solution
**Approach**
1. Keep `cur`, the id the next snapshot will get. Writes go into snapshot `cur`.
2. `set` adds `(cur, value)` to that key's history. If the last entry is already for `cur`,
   overwrite it instead, because only the last write before a snapshot counts.
3. `snapshot` returns `cur` and increases it by one.
4. `get` binary searches the key's history for the last change at or before `snap_id`.

**Brute force:** Copy the whole dictionary on every `snapshot()`. Reads are O(1), but memory
is O(snapshots × keys): 40,000 keys × 5,000 snapshots is 200 million entries.

**Optimal code:** [`solution.py`](solution.py)

```python
class ConfigStore:
    def __init__(self) -> None:
        self._history: dict[str, tuple[list[int], list[str]]] = {}
        self._current = 0

    def set(self, key: str, value: str) -> None:
        ids, values = self._history.setdefault(key, ([], []))
        if ids and ids[-1] == self._current:   # changed twice before one snapshot
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
        i = bisect_right(ids, snap_id) - 1     # last change at or before snap_id
        return values[i] if i >= 0 else None
```

**Complexity**
- Time: `set` and `snapshot` are O(1). `get` is O(log c), where c is the number of changes to that key.
- Space: O(total `set` calls), because only changes are stored, never full copies.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 tests: a normal history, an unknown key and an empty
snapshot, a key set after a snapshot, last write wins, an unchanged key carried across
snapshots, a feature-flag rollback to the last good revision, and 50,000 random operations
checked against a full-copy-per-snapshot store.

## 11. Interview Talk Track
"This is how you read config as of a past revision, which is what a rollback needs. Copying
all keys on every snapshot is simple, but most keys don't change between snapshots, so it
wastes memory. Instead each key keeps a list of (snapshot id, value) for the snapshots where
it changed. Ids only grow, so the list stays sorted. A read at snapshot N is a binary search
for the last change at or before N. Writes are O(1), reads are O(log c), and memory is
proportional to the number of changes. etcd works in a similar way: every write gets a
revision, you can read at a past revision, and compaction eventually throws old revisions
away, so you have to handle reads of compacted history."

## 12. Level Up
1. **"Memory keeps growing: add compaction."** Choose a revision R that no one will read
   below. For each key, drop all changes before its last change at or before R. Reads below R
   must then fail with a clear error, as etcd's compacted-revision error does.
2. **"Show a diff between snapshot 12 and snapshot 40."** Keep a per-snapshot list of changed
   keys as you write. The diff is the union of those lists for snapshots 13–40, each looked up
   at both ends. That touches only changed keys, not all 40,000.
3. **"Support delete."** Store a tombstone value (a special marker) as the change. `get`
   returns `None` when the found entry is a tombstone. Compaction may drop a tombstone only
   once nothing below it can be read.

## 13. Related Chips
- **DC-OBS-01 Metric Point-in-Time Lookup**: the same binary search per key, over time instead of snapshot ids.
- **DC-REL-01 Find the Breaking Commit**: binary search over history to find where things broke.
- **DC-OBS-12 Late & Corrected Samples**: history where old points can be rewritten.
