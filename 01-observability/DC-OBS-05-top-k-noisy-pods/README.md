Source: New

# DC-OBS-05 · Top-K Noisy Pods Board

## 1. Header
| | |
|---|---|
| Chip ID | DC-OBS-05 |
| Difficulty | Medium |
| Pattern | Hash map + heap/sort |
| Track | Observability & SRE (OBS) |
| Classic pattern | LeetCode 1244 |
| Premium | Yes (P). Free alternative: LeetCode 692 Top K Frequent Words (Medium): hash map counts, then top K with the same "ties by name" rule. |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
The API gateway in front of `public-api` returns HTTP 429 (rate limited) when an API key goes
over its quota. Each gateway replica streams "key X got N more 429s" events to a small
service that powers the "Noisiest API keys" panel on the on-call dashboard. When the on-call
engineer blocks a key, or the counting window rolls over, that key's total is reset. The panel
asks for the top 10 many times a minute.

## 3. Why This Is DevOps
**Production reality:** "Who is the noisiest?" is one of the first questions in any incident:
the top K pods by memory, the top K clients by 429s, the top K tables by write rate. A board
like this keeps a running total per key (a hash map) and ranks on demand, keeping only K
candidates in a heap. Resetting a key models a deleted pod or a counter window that rolled over.

**Where you see it:** PromQL `topk(10, sum by (api_key) (rate(http_429_total[5m])))`,
`kubectl top pods --sort-by=memory`, Grafana "Top N" tables, Redis Stack's `TOPK` data type.

**Reality check:** At very high cardinality (millions of keys), systems use approximate top-K:
a count-min sketch or a heavy-hitters structure (Redis's `TOPK` uses the HeavyKeeper algorithm)
keeps memory fixed at the cost of small errors. PromQL `topk` is exact, but it only ranks the
series that exist at that step. This chip is the exact, single-node version.

**What breaks if you get it wrong:** If ties or resets are handled wrong, the panel shows a
blocked key as still the "top offender", or hides the real one. The on-call engineer then
blocks the wrong customer while the abuse continues.

## 4. Problem Statement
Build a `NoisyBoard` that keeps a running total per key.

- `add(key, amount)`: add `amount` (≥ 1) to the key's total. A new key starts at 0.
- `reset(key)`: forget the key completely. Resetting an unknown key does nothing.
- `top(k)`: return the `k` largest totals as `(key, total)` pairs, largest first. Break ties
  by key in ascending order. If fewer than `k` keys exist, return all of them.
- `top_total(k)`: return the sum of the totals in `top(k)`. This is the number the classic
  problem asks for.

## 5. Input / Output format and Constraints
- `key`: a non-empty string (a pod name or an API key ID). `amount`: an int, `1 <= amount <= 10^4`.
- `k`: `1 <= k <= 10^4`.
- Up to `10^5` calls in total; up to `10^4` distinct keys alive at once.
- `top` returns `list[tuple[str, int]]`. `top_total` returns `int`.

## 6. Examples
**Example 1: ranking**
```
add("checkout-7d9f4-x2kqp", 900); add("search-5c8b7-q1wzt", 300); add("cart-6f5d2-m8hvn", 600)
top(2)       -> [("checkout-7d9f4-x2kqp", 900), ("cart-6f5d2-m8hvn", 600)]
top_total(2) -> 1500
```

**Example 2: reset**
```
add("api-key-7f3a", 25); add("api-key-91bc", 20)
reset("api-key-7f3a")
top(5) -> [("api-key-91bc", 20)]       # the blocked key is gone
```

**Example 3: ties and an empty board (edge cases)**
```
top(3) on an empty board -> []
add("pod-c", 7); add("pod-a", 7); add("pod-b", 7)
top(2) -> [("pod-a", 7), ("pod-b", 7)] # equal totals: order by key
```

## 7. Starter Code
See [`starter.py`](starter.py): `NoisyBoard` with `add`, `reset`, `top` and `top_total`
signatures, docstrings and type hints. Bodies are TODO.

```bash
make try CHIP=01-observability/DC-OBS-05-top-k-noisy-pods
```

## 8. Hints
1. **Nudge:** `add` and `reset` happen far more often than `top`. Which operations must be O(1)?
2. **Pattern:** A hash map holds the totals. For `top(k)`, you don't need to sort all n keys:
   a heap of size k is enough.
3. **Near-solution:** `heapq.nsmallest(k, counts.items(), key=lambda kv: (-kv[1], kv[0]))`
   gives the largest totals first, ties by key, in O(n log k).

## 9. Solution
**Approach**
1. Keep `dict[key] -> total`.
2. `add` updates the dict. `reset` deletes the key.
3. `top(k)` scans the dict and keeps the best k in a heap, ordered by `(-total, key)`.
4. `top_total(k)` sums the totals from `top(k)`.

**Brute force:** Sort every key on each `top` call: O(n log n) per call. With 10,000 keys that
is fine once, but a dashboard asks many times a minute. A heap of size k does the same job in O(n log k).

**Optimal code:** [`solution.py`](solution.py)

```python
import heapq


class NoisyBoard:
    def __init__(self) -> None:
        self._counts: dict[str, int] = {}

    def add(self, key: str, amount: int) -> None:
        self._counts[key] = self._counts.get(key, 0) + amount

    def reset(self, key: str) -> None:
        self._counts.pop(key, None)

    def top(self, k: int) -> list[tuple[str, int]]:
        # Largest totals first, ties by key; keeps only k items in the heap.
        return heapq.nsmallest(k, self._counts.items(), key=lambda kv: (-kv[1], kv[0]))

    def top_total(self, k: int) -> int:
        return sum(total for _, total in self.top(k))
```

**Complexity**
- Time: `add` and `reset` are O(1) (one dict operation). `top` is O(n log k), because each of
  the n keys is offered to a heap of size k.
- Space: O(n) for the dict of live keys, plus O(k) for the heap.

## 10. Tests
[`test_chip.py`](test_chip.py) has 6 cases: normal ranking, an empty board and k larger than
the number of keys, accumulating adds and resets (including an unknown key), ties broken by
key, a production-style 429 board with a blocked key, and 50,000 random operations checked
against a full sort.

## 11. Interview Talk Track
"This is the 'noisiest clients' panel. Writes are constant: every gateway replica reports 429
counts per key, so `add` must be O(1): a hash map from key to total. Reads are `top(k)`, and
k is small compared with the number of keys, so instead of sorting everything I keep a size-k
heap and get O(n log k). I break ties by key so the panel doesn't reorder itself on every
refresh. `reset` deletes the key, which models a blocked key or a rolled window. If reads were
constant too, I'd keep a sorted structure updated on every write. At millions of keys I'd
switch to an approximate heavy-hitters sketch, like Redis's TOPK, which keeps memory fixed."

## 12. Level Up
1. **"`top` is called 100 times a second, not once a minute."** Keep an ordered index updated
   on every write, for example a sorted list of `(-total, key)` pairs with a key → total map to
   remove the old entry. Each write becomes O(log n), and `top(k)` is O(k).
2. **"50 gateway replicas each count locally."** Exact top-K doesn't merge well: a key that is
   11th everywhere can be 1st overall. Each replica sends its full counts, or a mergeable sketch
   (count-min sketch plus a candidate list), and a central job merges them before ranking.
3. **"10 million keys, fixed memory."** Use a heavy-hitters algorithm such as Space-Saving or
   HeavyKeeper. It tracks about m candidates and guarantees that any key above roughly 1/m of the
   total traffic is kept. The small keys you lose don't matter for an "offenders" panel.

## 13. Related Chips
- **DC-OBS-04 Duplicate Stack Trace Finder**: group events first, then rank the groups here.
- **DC-OBS-02 5-Minute Error Counter**: the time window that decides when a counter resets.
- Handbook #5 Top K Frequent Elements: the related counting-then-top-K problem.
