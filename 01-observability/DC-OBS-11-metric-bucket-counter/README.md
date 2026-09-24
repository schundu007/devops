Source: New

# DC-OBS-11 · Metric Bucket Counter

## 1. Header
| | |
|---|---|
| Chip ID | DC-OBS-11 |
| Difficulty | Medium |
| Pattern | Hash map + bucketing |
| Track | Observability & SRE (OBS) |
| Classic pattern | LeetCode 1348 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
The platform team's "Pod restarts" panel shows `kube_pod_restarts` for `api-6c9f8-lq2xz`.
At the 1-hour zoom level each bar is one minute. The SRE lead zooms out to 24 hours and
the panel must redraw with one bar per hour, then per day at the 7-day zoom. Each redraw asks:
"How many restart events fell in each bucket between `start` and `end`?" The buckets start at
the left edge of the selected range, not at the top of the clock hour.

## 3. Why This Is DevOps
**Production reality:** Dashboards never plot every raw event. They split the selected range
into equal steps and show one number per step. This is downsampling. When you zoom out, the
step grows from 1 minute to 1 hour to 1 day, so the same events land in fewer, bigger
buckets. Getting the bucket edges right (which bucket does second 60 belong to?) decides
whether two graphs of the same data agree.

**Where you see it:** the Prometheus range query `step` parameter, Grafana's `$__interval`
and "Min interval", Elasticsearch/OpenSearch `date_histogram`, Loki `count_over_time` in range queries.

**Reality check:** Real systems usually align buckets to the clock or to multiples of the
step, so dashboards on different screens agree. Prometheus, for example, evaluates at
`start`, `start+step`, and so on, and each point looks back over a window rather than
counting a closed bucket. This chip aligns buckets to `start` and uses exact counts, the
simplest version of the same idea.

**What breaks if you get it wrong:** An off-by-one at bucket edges counts an event twice,
or not at all, when you zoom. The per-hour total then differs from the per-minute total,
and in a postmortem nobody trusts the graph.

## 4. Problem Statement
Build an `EventCounter`.

- `record(name, time)`: store one event called `name` at second `time`. Events may arrive in
  any time order, and several can share a second.
- `counts(step, name, start, end)`: split `[start, end]` (both ends inclusive) into buckets of
  `step` size, where `"minute"` = 60 s, `"hour"` = 3600 s and `"day"` = 86400 s. The first
  bucket is `[start, start + size - 1]`, the next begins at `start + size`, and the last
  bucket is cut short at `end`. Return the number of `name` events in each bucket, in order.

An unknown `name` returns all zeros.

## 5. Input / Output format and Constraints
- `name`: a non-empty string. `time`, `start`, `end`: integers, `0 <= time, start, end <= 10^9`, `start <= end`.
- `step` is one of `"minute"`, `"hour"`, `"day"`.
- `counts` returns `list[int]` of length `(end - start) // size + 1`.
- Up to `10^4` calls in total. Each `counts` call returns at most `10^4` buckets.

## 6. Examples
**Example 1: an edge second starts a new bucket**
```
record("deploy", 0); record("deploy", 60); record("deploy", 10)
counts("minute", "deploy", 0, 59)  -> [2]      # 0 and 10
counts("minute", "deploy", 0, 60)  -> [2, 1]   # second bucket is only second 60
```

**Example 2: buckets move with `start`**
```
events at 100, 159, 160, 219, 220
counts("minute", "5xx", 100, 220) -> [2, 2, 1]   # [100,159] [160,219] [220,220]
counts("minute", "5xx", 101, 218) -> [2, 0]      # [101,160] [161,218]
```

**Example 3: unknown name (edge case)**
```
counts("minute", "oom_kill", 0, 179) -> [0, 0, 0]
```

## 7. Starter Code
See [`starter.py`](starter.py): `EventCounter` with `record` and `counts`, plus the
`BUCKET_SECONDS` table. Bodies are TODO.

```bash
make try CHIP=01-observability/DC-OBS-11-metric-bucket-counter
```

## 8. Hints
1. **Nudge:** Which bucket does time `t` fall in? Write that as one arithmetic expression using `start` and the size.
2. **Pattern:** Group events by name in a hash map. The bucket index is `(t - start) // size`.
3. **Near-solution:** Keep each name's times sorted (`insort`). In `counts`, binary search for
   the slice inside `[start, end]`, then add 1 to `buckets[(t - start) // size]` for each time in it.

## 9. Solution
**Approach**
1. Map each name to a sorted list of its event times.
2. `record` inserts in sorted position, because events can arrive out of order.
3. `counts` makes `(end - start) // size + 1` zeroed buckets.
4. Two binary searches find the events inside `[start, end]`, and each one adds 1 to bucket `(t - start) // size`.

**Brute force:** Keep an unsorted list per name and check every event on every query:
O(total events) per redraw, even when the range covers a tiny part of the history.

**Optimal code:** [`solution.py`](solution.py)

```python
from bisect import bisect_left, bisect_right, insort

BUCKET_SECONDS = {"minute": 60, "hour": 3600, "day": 86400}


class EventCounter:
    def __init__(self) -> None:
        self._times: dict[str, list[int]] = {}

    def record(self, name: str, time: int) -> None:
        insort(self._times.setdefault(name, []), time)

    def counts(self, step: str, name: str, start: int, end: int) -> list[int]:
        size = BUCKET_SECONDS[step]
        buckets = [0] * ((end - start) // size + 1)
        times = self._times.get(name, [])
        lo, hi = bisect_left(times, start), bisect_right(times, end)
        for t in times[lo:hi]:
            buckets[(t - start) // size] += 1   # aligned to the query's start
        return buckets
```

**Complexity**
- Time: `record` is O(n) worst case, because `insort` shifts the list. It is close to
  O(log n) when events arrive almost in order. `counts` is O(log n + m + B): two binary
  searches, m events in range, and B buckets.
- Space: O(total events), with each one stored once.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: minute and hour buckets, an unknown name, a
single-second range, bucket alignment and inclusive ends, out-of-order and duplicate times, a
production-style zoom-out from hourly to daily restarts, and a 20,000-event random check
against a brute-force count.

## 11. Interview Talk Track
"This is what a dashboard does when you zoom out: the same events regrouped into bigger
steps. I store each event name's timestamps in a sorted list in a hash map. For a query I
build `(end - start) / size + 1` zeroed buckets, binary search the slice of events inside
the range, and add each event to bucket `(t - start) // size`. The details that bite are the
inclusive end, and the last bucket being shorter. Query cost depends on the events in range plus
the number of buckets, not on total history. In production you wouldn't keep raw events.
You'd keep pre-aggregated counts at a fine step, say per minute, and sum them up to hours and
days, which is how TSDB downsampling and recording rules keep zoom-outs cheap."

## 12. Level Up
1. **"A billion events a day."** Don't store raw times. Keep per-minute counters (a
   hash map from minute to count, or a ring for recent data) and build hours and days by
   summing minutes. Storage goes from O(events) to O(minutes), which is 1,440 per day per series.
2. **"Buckets must line up across every dashboard."** Align to the clock: bucket =
   `floor(t / size) * size`, and trim the first and last buckets to the range. Then two
   users who pick slightly different ranges still see identical interior bars.
3. **"Events arrive late, up to 10 minutes after the fact."** Keep recent minute buckets
   open for writes, and seal (and downsample) a minute only after the lateness window has
   passed. Late samples beyond that are dropped or counted separately, a similar idea to a
   TSDB's out-of-order window.

## 13. Related Chips
- **DC-OBS-02 5-Minute Error Counter**: fixed per-second buckets in a ring.
- **DC-OBS-10 Log Time-Range Query**: range scans over timestamps at year/day/hour/minute detail.
- **DC-OBS-01 Metric Point-in-Time Lookup**: binary search over one metric's sorted times.
