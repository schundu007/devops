Source: New

# DC-PLAT-12 · Hot-Object Cache (LFU)

## 1. Header
| | |
|---|---|
| Chip ID | DC-PLAT-12 |
| Difficulty | Hard |
| Pattern | Hash maps + frequency lists |
| Track | Platform Engineering, Scheduling & Allocation (PLAT) |
| Classic pattern | LeetCode 460 |
| Premium | No |
| Time box | 40 min |
| Source | New |

## 2. The Scenario
An edge cache node in front of `shop.example.com` has room for a few thousand objects. Most
traffic hits the same assets: `/static/app.js`, `/static/app.css`, the logo. Every night a
crawler walks thousands of old blog URLs exactly once. With a recency-only (LRU) policy that
scan pushes the popular assets out, and the morning traffic misses the cache and hammers the
origin. You want a policy that keeps objects people ask for **often**, not just recently.

## 3. Why This Is DevOps
**Production reality:** Caches in front of origins and databases decide what to keep when
they are full. LRU keeps what was used recently, so a one-time scan flushes it. LFU keeps what
is used often: it counts uses per key, evicts the lowest count, and breaks ties by recency.
Doing that in O(1) per request needs a map from key to value and count, plus one ordered list
per count, so the victim is always the oldest key in the lowest-count list.

**Where you see it:** Redis `maxmemory-policy allkeys-lfu` and `volatile-lfu`, the Caffeine
Java cache (W-TinyLFU), and CDN or edge caches that use frequency as an admission or eviction signal.

**Reality check:** Production LFU is approximate. Redis keeps an 8-bit logarithmic counter per
key that decays over time (`lfu-log-factor`, `lfu-decay-time`), and it evicts by sampling
a few keys, not by keeping exact lists. Pure LFU has a known flaw that the decay fixes: an
object that was hot last week keeps a high count and never leaves. Many real caches mix
recency and frequency.

**What breaks if you get it wrong:** A wrong tie-break or a stale "minimum frequency" evicts a
hot object. The cache hit ratio drops from 95% to 60%, origin traffic goes up 8 times, and the
origin falls over during the next traffic peak.

## 4. Problem Statement
Build an `LFUCache` that holds at most `capacity` objects.

- `get(key)` returns the cached value and counts one use of `key`, or returns `None` on a miss.
- `put(key, value)` inserts or updates. An update also counts as one use.
- When a **new** key is inserted into a full cache, first evict the key with the **fewest
  uses**. If several keys tie, evict the one whose last use is the **oldest**.
- A newly inserted key starts with 1 use. With `capacity == 0`, nothing is ever stored.

Both operations must run in O(1) average time.

## 5. Input / Output format and Constraints
- `capacity`: `0 <= capacity <= 10^4`.
- Keys and values are strings, such as `"/static/app.js"` and an ETag or body reference.
- `get(key) -> str | None`. `put(key, value) -> None`.
- Up to `2 * 10^5` calls in total.

## 6. Examples
**Example 1: evict the least used**
```
c = LFUCache(2)
put("/img/logo.png", "v1"); put("/js/app.js", "v1")
get("/img/logo.png")          -> "v1"   # logo: 2 uses, app.js: 1
put("/css/site.css", "v1")              # full -> evicts app.js
get("/js/app.js")             -> None
```

**Example 2: a tie goes to the oldest use**
```
c = LFUCache(2)
put("a","1"); put("b","2")              # both have 1 use; a is older
put("c","3")                            # evicts a
get("a") -> None
```

**Example 3: capacity 0 (edge case)**
```
c = LFUCache(0); put("k","v"); get("k") -> None
```

## 7. Starter Code
See [`starter.py`](starter.py): `LFUCache(capacity)` with `get` and `put`, docstrings and
type hints. Bodies are TODO.

```bash
make try CHIP=03-platform/DC-PLAT-12-lfu-hot-object-cache
```

## 8. Hints
1. **Nudge:** Finding the minimum count by scanning is O(n). What if keys were already grouped by their count?
2. **Pattern:** Keep one ordered set per count (`count -> keys, oldest first`), plus the
   smallest count that has any keys. A use moves a key from list `f` to the end of list `f+1`.
3. **Near-solution:** Track `min_freq`. When list `min_freq` empties during a move, `min_freq`
   becomes `f+1`. On insert, evict the first key of list `min_freq`, then set `min_freq = 1`,
   because the new key is always the least used.

## 9. Solution
**Approach**
1. `value[key]` and `freq[key]` hold the data. `buckets[f]` is an `OrderedDict` used as an
   ordered set of keys with `f` uses, oldest use first.
2. `_touch(key)` moves a key from `buckets[f]` to the end of `buckets[f+1]`. If that empties
   `buckets[min_freq]`, then `min_freq` goes up by one.
3. `get` touches and returns the value, or returns `None` on a miss.
4. `put` on an existing key updates and touches it. On a new key when full, pop the oldest key
   from `buckets[min_freq]`, then insert the new key into `buckets[1]` and set `min_freq = 1`.

**Brute force:** Store counts and last-use times, and scan every key for the victim on each
eviction. That is O(n) per insert, and with 10,000 objects and heavy churn the cache itself
becomes the bottleneck.

**Optimal code:** [`solution.py`](solution.py)

```python
from collections import OrderedDict, defaultdict


class LFUCache:
    def __init__(self, capacity: int) -> None:
        self._capacity = capacity
        self._value: dict[str, str] = {}
        self._freq: dict[str, int] = {}
        self._buckets: defaultdict[int, OrderedDict[str, None]] = defaultdict(OrderedDict)
        self._min_freq = 0

    def _touch(self, key: str) -> None:
        f = self._freq[key]
        bucket = self._buckets[f]
        del bucket[key]
        if not bucket:
            del self._buckets[f]
            if self._min_freq == f:
                self._min_freq = f + 1          # the key moved up; so did the minimum
        self._freq[key] = f + 1
        self._buckets[f + 1][key] = None        # newest in its new bucket

    def get(self, key: str) -> str | None:
        if key not in self._value:
            return None
        self._touch(key)
        return self._value[key]

    def put(self, key: str, value: str) -> None:
        if self._capacity <= 0:
            return
        if key in self._value:
            self._value[key] = value
            self._touch(key)
            return
        if len(self._value) >= self._capacity:
            coldest = self._buckets[self._min_freq]
            victim, _ = coldest.popitem(last=False)   # oldest in the lowest bucket
            if not coldest:
                del self._buckets[self._min_freq]
            del self._value[victim]
            del self._freq[victim]
        self._value[key] = value
        self._freq[key] = 1
        self._buckets[1][key] = None
        self._min_freq = 1
```

**Complexity**
- Time: O(1) average for `get` and `put`, because each is a fixed number of dict and
  `OrderedDict` operations. `min_freq` only moves by one step or resets to 1, so it never needs a scan.
- Space: O(capacity), for one entry per cached key in each structure.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: least-frequent eviction, the tie-break by oldest
use, capacity 0 and 1 (the boundaries), an update counting as a use, a new key resetting the
minimum frequency, a production-style crawler scan that must not flush hot assets, and a
random check (4 capacities × 8,000 operations) against a brute-force scan.

## 11. Interview Talk Track
"LFU keeps the objects that are used most often, which protects an edge cache from one-off
scans that would flush an LRU. The trick is O(1) eviction. I keep a map from key to value and
use count, and for each count an ordered set of keys, oldest use first. A hit moves the key
from list f to the end of list f plus one. I also track the smallest count that has keys:
when that list empties because its key moved up, the minimum becomes f plus one, and a new
insert always resets it to 1. Eviction pops the front of the minimum list. Everything is
constant time. In production, Redis approximates this with a decaying 8-bit counter and
sampling. Pure LFU never forgets old popularity, so real caches add decay or mix in recency."

## 12. Level Up
1. **"Last week's viral image still has count 50,000 and never leaves."** Add aging: halve
   every count on a schedule, or keep counts over a sliding window. Redis decays its counter
   by `lfu-decay-time`. W-TinyLFU goes further and uses a small admission window plus a
   frequency sketch that is reset periodically.
2. **"100 million keys: per-key lists cost too much memory."** Use an approximate
   count-min sketch (4 bits per counter) for frequency, and sampled eviction: look at 5 random
   keys and evict the least frequent. You give up exactness for fixed memory, as Redis does.
3. **"Objects have very different sizes (1 KB favicon, 50 MB video)."** Count cost as well as
   frequency: evict by `frequency / size`, or run size-class pools. Otherwise one large object
   evicts thousands of small hot ones.

## 13. Related Chips
- **DC-PLAT-06 Image Cache with LRU Eviction**: the recency-only version, and the one to compare against.
- **DC-OBS-05 Top-K Noisy Pods Board**: counting frequency to rank keys.
- **DC-PLAT-11 Lowest Free ID Allocator**: another O(1)/O(log n) pool bookkeeping structure.
