Source: New

# DC-OBS-12 · Late & Corrected Samples

## 1. Header
| | |
|---|---|
| Chip ID | DC-OBS-12 |
| Difficulty | Medium |
| Pattern | Hash map + heaps with lazy deletion |
| Track | Observability & SRE (OBS) |
| Classic pattern | LeetCode 2034 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
The Prometheus agent on `edge-proxy-3` lost its network for 10 minutes. When the link
came back, its remote-write queue started sending live samples and backfilling the gap at
the same time, so older timestamps now arrive after newer ones. One backfilled reading shows
`cpu_usage = 9999` at 10:02:30, caused by a counter-reset bug. The exporter sends a
corrected value for that exact timestamp a minute later. The "peak CPU" stat on the incident
dashboard must drop back as soon as the correction lands.

## 3. Why This Is DevOps
**Production reality:** Samples do not always arrive in order. Agents buffer and replay
after network loss, batch jobs backfill history, and exporters sometimes re-send a
corrected value for a timestamp. The store must still answer three things: the latest
value, the peak and the low, using only the corrected data. A correction must *remove* the
old value's effect, and that is the hard part. A heap cannot delete from its middle cheaply,
so you skip stale entries only when they reach the top.

**Where you see it:** Prometheus remote-write and out-of-order ingestion, Mimir and Cortex
ingesters, InfluxDB (a write to an existing timestamp overwrites it), CloudWatch
`PutMetricData` with past timestamps.

**Reality check:** TSDBs limit how late a sample may arrive. Prometheus rejects
out-of-order samples by default, and accepts them only inside the configured
`out_of_order_time_window`. Many TSDBs treat a second write to the same timestamp as a
duplicate, not a correction. This chip assumes corrections are allowed, and keeps unlimited history.

**What breaks if you get it wrong:** If a corrected spike stays in the max, the "peak CPU"
stat still shows 9999 after the fix. Capacity planning then sizes the fleet for a spike that
never happened, and someone buys 30% more nodes.

## 4. Problem Statement
Build a `SampleTracker` for one metric.

- `update(timestamp, value)`: record a sample. Timestamps may arrive in any order. If a
  timestamp was already recorded, this is a **correction**: the new value replaces the old one.
- `current()`: the value at the **newest timestamp** seen so far.
- `maximum()`: the highest value across all timestamps, after corrections.
- `minimum()`: the lowest value across all timestamps, after corrections.

`current`, `maximum` and `minimum` are only called after at least one `update`.

## 5. Input / Output format and Constraints
- `timestamp`: an integer, `1 <= timestamp <= 10^9`. `value`: a float, `-10^9 <= value <= 10^9`.
- `current`, `maximum` and `minimum` return floats.
- Up to `10^5` calls in total.

## 6. Examples
**Example 1: a correction lowers the peak**
```
update(1, 10.0); update(2, 5.0)
current() -> 5.0      # newest timestamp is 2
maximum() -> 10.0
update(1, 3.0)        # correction at t=1
maximum() -> 5.0      # the 10 is gone
```

**Example 2: a late sample (edge case)**
```
update(100, 1.0); update(50, 99.0)
current() -> 1.0      # 50 is older than 100, so current does not change
maximum() -> 99.0
```

**Example 3: correcting the newest timestamp**
```
update(5, 1.0); update(5, 8.0)
current() -> 8.0; minimum() -> 8.0
```

## 7. Starter Code
See [`starter.py`](starter.py): `SampleTracker` with `update`, `current`, `maximum` and
`minimum`. Bodies are TODO.

```bash
make try CHIP=01-observability/DC-OBS-12-late-corrected-samples
```

## 8. Hints
1. **Nudge:** `current` only needs the newest timestamp and a way to look up its value. What is hard is the max and min after a correction.
2. **Pattern:** Keep a max-heap and a min-heap of `(value, timestamp)`. Don't delete old values on a correction: push the new pair and treat old pairs as stale.
3. **Near-solution:** A heap top is stale if `value_at[top.timestamp] != top.value`. Pop
   while the top is stale, then return it. Keep `value_at` in a dict and `latest` as the max timestamp seen.

## 9. Solution
**Approach**
1. `value_at`: a dict from timestamp to its current value. Corrections overwrite it.
2. `latest`: the largest timestamp seen. `current()` is `value_at[latest]`.
3. On every update, push `(value, ts)` into a min-heap and `(-value, ts)` into a max-heap.
4. On a max or min query, pop tops whose value no longer matches `value_at[ts]` (stale), then read the top.

**Brute force:** Scan `value_at.values()` for the max and min on each query: O(n) per
query, too slow when a dashboard polls often.

**Optimal code:** [`solution.py`](solution.py)

```python
import heapq


class SampleTracker:
    def __init__(self) -> None:
        self._value_at: dict[int, float] = {}
        self._latest = -1
        self._max_heap: list[tuple[float, int]] = []   # (-value, ts)
        self._min_heap: list[tuple[float, int]] = []   # (value, ts)

    def update(self, timestamp: int, value: float) -> None:
        self._value_at[timestamp] = value
        self._latest = max(self._latest, timestamp)
        heapq.heappush(self._max_heap, (-value, timestamp))   # stale pairs stay, skipped later
        heapq.heappush(self._min_heap, (value, timestamp))

    def current(self) -> float:
        return self._value_at[self._latest]

    def maximum(self) -> float:
        while self._value_at[self._max_heap[0][1]] != -self._max_heap[0][0]:
            heapq.heappop(self._max_heap)                     # lazy deletion
        return -self._max_heap[0][0]

    def minimum(self) -> float:
        while self._value_at[self._min_heap[0][1]] != self._min_heap[0][0]:
            heapq.heappop(self._min_heap)
        return self._min_heap[0][0]
```

**Complexity**
- Time: `update` is O(log n), for two heap pushes. `maximum` and `minimum` are O(log n)
  amortised, because each pushed pair is popped at most once. `current` is O(1).
- Space: O(number of updates), because stale pairs stay in the heaps until they surface.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: a normal update and correction sequence, a
single sample, a late sample that must not change `current`, correcting the newest
timestamp, a value corrected away and then back, a production-style remote-write backfill
with a corrected spike, and a 20,000-update random check against a brute-force dict scan.

## 11. Interview Talk Track
"Samples can arrive late or be corrected, so I separate the truth from the indexes. The
truth is a dict from timestamp to its latest value, plus the newest timestamp seen, which
makes `current` O(1). For the max and min I keep two heaps of value and timestamp pairs.
The trick is lazy deletion: on a correction I don't search the heap. I push the new pair and
leave the old one. When I read the max, I pop any top whose value no longer matches the dict,
because it's stale, and each pair is popped at most once, so it's O(log n) amortised. The
cost is memory for stale pairs. If corrections are frequent, I'd switch to a sorted
container with real deletes, or rebuild the heaps when stale entries pass half the size.
Real TSDBs avoid most of this by capping how late a sample may arrive."

## 12. Level Up
1. **"90% of updates are corrections, and the heaps grow without bound."** Count stale
   entries. When they pass half the heap, rebuild both heaps from `value_at` in O(n).
   Or use a balanced tree or sorted multiset with real deletion, which is O(log n) per
   correction with no garbage.
2. **"Only keep the last 1 hour, and the max is over that window."** Now old timestamps
   expire too. Treat "older than now − 3600" as stale in the same lazy check, and drop
   those `value_at` entries. This is DC-OBS-03's window, combined with this chip's corrections.
3. **"Reject samples more than 10 minutes late."** Compare `timestamp` with `latest - 600`
   in `update` and reject (or count) anything older. This bounds both memory and the work a
   late sample can cause, a similar idea to Prometheus's `out_of_order_time_window`.

## 13. Related Chips
- **DC-OBS-01 Metric Point-in-Time Lookup**: the same data, but always in order and never corrected.
- **DC-OBS-08 Live Latency Percentiles**: two heaps for a streaming statistic.
- **DC-OBS-03 Rolling Peak CPU**: the max over a sliding window, with a different way to expire old values.
