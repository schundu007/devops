Source: New

# DC-SEC-10 · Allow-List Range Tracker

## 1. Header
| | |
|---|---|
| Chip ID | DC-SEC-10 |
| Difficulty | Hard |
| Pattern | Sorted intervals |
| Track | Cloud Security & IAM (SEC) |
| Classic pattern | LeetCode 715 |
| Premium | No |
| Time box | 40 min |
| Source | New |

## 2. The Scenario
The ingress controller in front of `internal-tools` keeps a live allow-list of ports and
source addresses, changed by API calls from three teams all day. At 09:10 the platform team
allows ports 8000–8100. At 11:30 security closes the debug ports 8080–8081 after a pen-test
finding. At 11:31 a deploy pipeline asks "are ports 8079–8080 open?" before it routes traffic.
Removing 8080–8081 from the middle of 8000–8100 has to split it into two ranges, not delete
the whole thing and not leave the debug ports open.

## 3. Why This Is DevOps
**Production reality:** Allow-lists for ports, IP ranges (as integers) and ID ranges change all
the time: rules are added, revoked and queried. Keeping them as sorted, merged ranges gives fast
answers to "is this whole range allowed?", and makes the stored state readable for audits.
The tricky part is removal: taking a range out of the middle of a bigger one must leave two
pieces. Binary search finds the few ranges affected, so each update touches only its neighbours.

**Where you see it:** Linux `ipset` (`hash:net` and `bitmap:port` sets updated at runtime),
nftables interval sets, Envoy and cloud firewall rule APIs, and IPAM tools that track free and
used address ranges.

**Reality check:** Kernel packet filters answer "is this *one* address allowed?" per packet,
using hash sets or radix trees, while this chip answers range questions for the control plane.
Python's list slicing makes each update O(n) in the worst case. A balanced tree or skip list
gets O(log n + k) per update, which matters with millions of ranges.

**What breaks if you get it wrong:** A remove that drops the whole containing range cuts off
every service on ports 8000–8100 (an outage). A remove that doesn't split correctly leaves the
debug ports open after security signed off the fix (an exposure).

## 4. Problem Statement
Build an `AllowList` over integers (ports, or IPv4 addresses as numbers). All ranges are
half-open, `[lo, hi)`: `lo` is included and `hi` is not.

- `add(lo, hi)`: allow every value in `[lo, hi)`.
- `remove(lo, hi)`: stop allowing every value in `[lo, hi)`. A range can split into two.
- `covers(lo, hi)`: `True` only if **every** value in `[lo, hi)` is allowed right now.
- `ranges()`: the allowed values as sorted `(lo, hi)` pairs, merged so that no two pairs overlap
  or touch (`(10, 20)` and `(20, 30)` are reported as `(10, 30)`).

## 5. Input / Output format and Constraints
- `add(lo: int, hi: int) -> None`, `remove(lo: int, hi: int) -> None`,
  `covers(lo: int, hi: int) -> bool`, `ranges() -> list[tuple[int, int]]`.
- `0 <= lo < hi <= 2^32`.
- Up to `10^4` calls in total.

## 6. Examples
**Example 1: split on remove**
```
add(8000, 8101)          # ports 8000-8100
remove(8080, 8082)       # close 8080-8081
ranges()          -> [(8000, 8080), (8082, 8101)]
covers(8079, 8081) -> False    # 8080 is closed
covers(8000, 8080) -> True
```

**Example 2: touching ranges merge (edge case)**
```
add(10, 20); add(20, 30)
ranges()        -> [(10, 30)]
covers(29, 30)  -> True
covers(30, 31)  -> False   # hi is not included
```

**Example 3: empty**
```
ranges()        -> []
covers(0, 1)    -> False
remove(0, 100)  # no error
```

## 7. Starter Code
See [`starter.py`](starter.py): the `AllowList` class with `add`, `remove`, `covers` and
`ranges`, with docstrings and type hints. Bodies are TODO.

```bash
make try CHIP=02-security/DC-SEC-10-allow-list-range-tracker
```

## 8. Hints
1. **Nudge:** If you keep the ranges sorted and never touching, how many of them can one `add` or `remove` affect?
2. **Pattern:** Sorted, disjoint intervals with binary search. The affected ranges are always one consecutive block.
3. **Near-solution:** Keep parallel `starts` and `ends` lists. `add`: `i = bisect_left(ends, lo)`, `j = bisect_right(starts, hi)`,
   and replace `[i:j]` with one merged range. `remove`: `i = bisect_right(ends, lo)`, `j = bisect_left(starts, hi)`,
   and replace `[i:j]` with the left and right leftovers. `covers`: find the last range starting at or before `lo` and check its end.

## 9. Solution
**Approach**
1. Keep ranges sorted by start, never overlapping and never touching, in two parallel lists.
2. **add:** find the block of ranges that overlap or touch `[lo, hi)`, and replace it with one range that spans them all.
3. **remove:** find the block of ranges that overlap `[lo, hi)`. Keep only the part of the first
   range left of `lo` and the part of the last range right of `hi`.
4. **covers:** because ranges never touch, `[lo, hi)` is covered only if one range holds all of
   it, the last range starting at or before `lo`.

**Brute force:** Keep a set of every allowed value. That's simple, but ports 0–65535 is fine
while an IPv4 range like `10.0.0.0/8` is 16 million entries, and `covers` scans the whole range.

**Optimal code:** [`solution.py`](solution.py)

```python
from bisect import bisect_left, bisect_right


class AllowList:
    def __init__(self) -> None:
        self._starts: list[int] = []     # range k is [starts[k], ends[k])
        self._ends: list[int] = []

    def add(self, lo: int, hi: int) -> None:
        i = bisect_left(self._ends, lo)      # first range with end >= lo (touching counts)
        j = bisect_right(self._starts, hi)   # ranges before j start at or before hi
        if i < j:
            lo = min(lo, self._starts[i])
            hi = max(hi, self._ends[j - 1])
        self._starts[i:j] = [lo]
        self._ends[i:j] = [hi]

    def remove(self, lo: int, hi: int) -> None:
        i = bisect_right(self._ends, lo)     # first range with end > lo
        j = bisect_left(self._starts, hi)    # ranges before j start before hi
        if i >= j:
            return
        new_starts, new_ends = [], []
        if self._starts[i] < lo:             # left leftover
            new_starts.append(self._starts[i]); new_ends.append(lo)
        if self._ends[j - 1] > hi:           # right leftover
            new_starts.append(hi); new_ends.append(self._ends[j - 1])
        self._starts[i:j] = new_starts
        self._ends[i:j] = new_ends

    def covers(self, lo: int, hi: int) -> bool:
        k = bisect_right(self._starts, lo) - 1   # last range starting at or before lo
        return k >= 0 and self._ends[k] >= hi

    def ranges(self) -> list[tuple[int, int]]:
        return list(zip(self._starts, self._ends))
```

**Complexity**
- Time: `covers` is O(log n) (one binary search). `add` and `remove` are O(log n) to find the
  block plus O(n) for the list slice in the worst case. With a balanced tree, O(log n + k), where
  k is the number of ranges merged or cut.
- Space: O(n) for n stored ranges. The number of ranges only grows by 1 per `remove` (a split).

## 10. Tests
[`test_chip.py`](test_chip.py) has 6 cases: a split on remove plus queries, the empty list and a
single value, half-open boundaries and touching ranges, one add that swallows many ranges, a
production case (debug ports closed and a revoked `/26` inside a `/24`), and a large random check
(4,000 random operations against a set of values, including the "sorted, non-touching" invariant).

## 11. Interview Talk Track
"The allow-list changes all day, so I keep it as sorted ranges that never overlap or touch, and
use half-open intervals so ports 8000 to 8100 is `[8000, 8101)` and adjacent ranges merge
cleanly. Because they're sorted and disjoint, any add or remove affects one consecutive block of
ranges, which I find with two binary searches. Add replaces that block with one merged range.
Remove keeps only the leftover piece on each side, which is how taking 8080 out of the middle
splits the range in two. Covers is one binary search: find the last range starting at or before
lo and check that it reaches hi. Queries are O(log n), and updates are O(log n) plus the slice.
The security point is that remove must split, not drop: dropping is an outage, and not splitting leaves ports open."

## 12. Level Up
1. **"Millions of ranges, updated thousands of times a second."** List slicing becomes the
   bottleneck. Use a balanced tree or skip list keyed by start (for example `sortedcontainers` in
   Python, or a B-tree in the service), so each update is O(log n + k). Batch updates and apply
   them atomically so the data path never sees a half-applied change.
2. **"Also answer: *which* rule allowed this value?"** Store an owner or rule ID with each range.
   Merging then only joins ranges with the same owner, so the structure keeps more, smaller ranges,
   but every allow decision can be traced to a change ticket.
3. **"Push this to 500 proxies without restarting them."** Send diffs (add and remove operations)
   with a version number, and have each proxy apply them in order. A proxy that misses a version
   fetches a full snapshot. This is similar to how Envoy's xDS delivers config updates.

## 13. Related Chips
- **DC-SEC-05 Firewall Range Merger**: the one-shot version: sort once and merge.
- **DC-SEC-09 IP Range to CIDR Blocks**: turn each stored integer range into CIDR rules.
- **DC-PLAT-11 Lowest Free ID Allocator**: another allocator over integer ranges.
