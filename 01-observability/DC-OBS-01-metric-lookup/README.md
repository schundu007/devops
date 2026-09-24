Source: New

# DC-OBS-01 · Metric Point-in-Time Lookup

## 1. Header
| | |
|---|---|
| Chip ID | DC-OBS-01 |
| Difficulty | Medium |
| Pattern | Hash map + binary search |
| Track | Observability & SRE (OBS) |
| Classic pattern | LeetCode 981 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
It is 10:20 and you are on call for `checkout-api`. At 10:05:00 the p99 latency alert fired,
and the incident channel asks: "What was `cpu_usage` on `checkout-api-7d9f4-x2kqp` at
exactly 10:05:00?" The scraper collects a sample every 15 seconds, so no sample sits exactly
on 10:05:00. The dashboard has to show the latest sample at or before that moment:
the one from 10:04:52.

## 3. Why This Is DevOps
**Production reality:** A time-series database stores each metric as a list of samples
sorted by time. A dashboard asks "what was the value at time T?", and the database answers
with the newest sample at or before T. Samples arrive in time order, so the list is always
sorted and the lookup is a binary search, not a scan. Prometheus runs this lookup for every
series in an instant query, many times per second.

**Where you see it:** Prometheus instant queries (`/api/v1/query?time=…`), Grafana panels
and "Explore" at a point in time, Thanos and Mimir queriers, VictoriaMetrics.

**Reality check:** Prometheus only looks back 5 minutes by default (`--query.lookback-delta`).
If the newest sample is older than that, the series returns nothing. Real TSDBs also keep
samples in compressed chunks: they first find the chunk that covers T, then read inside it.
This chip is the simple, uncompressed version of the same lookup.

**What breaks if you get it wrong:** An off-by-one returns the sample *after* T. During
incident review you then blame the CPU spike that came after the alert, not the cause
before it. The team fixes the wrong thing, and the outage repeats.

## 4. Problem Statement
Build a `MetricStore` that keeps samples for many metrics.

- `record(metric, value, timestamp)`: save one sample. For each metric, timestamps arrive
  in strictly increasing order, because a scraper never goes back in time.
- `value_at(metric, timestamp)`: return the value of the newest sample of `metric` whose time
  is **at or before** `timestamp`. If the metric is unknown, or all its samples are later
  than `timestamp`, return `None`.

A value of `0.0` is a real reading, not "no data".

## 5. Input / Output format and Constraints
- `metric`: a non-empty string, e.g. `cpu_usage` or `node_cpu{instance="10.0.3.17"}`.
- `value`: a float. `timestamp`: an integer epoch second, `1 <= timestamp <= 2 * 10^9`.
- `value_at` returns `float | None`.
- Up to `2 * 10^5` calls in total, across up to `10^4` metrics.
- For one metric, the timestamps passed to `record` are strictly increasing.

## 6. Examples
**Example 1: between samples**
```
record("cpu_usage", 0.42, 1000)
record("cpu_usage", 0.87, 1015)
value_at("cpu_usage", 1010)  -> 0.42   # newest sample at or before 1010 is the one at 1000
value_at("cpu_usage", 1015)  -> 0.87   # an exact match counts
```

**Example 2: too early (edge case)**
```
record("cpu_usage", 0.5, 1000)
value_at("cpu_usage", 999)   -> None   # no sample that early
value_at("mem_bytes", 1000)  -> None   # metric never recorded
```

**Example 3: zero is data**
```
record("queue_depth", 0.0, 1000)
value_at("queue_depth", 1005) -> 0.0   # not None: the queue really was empty
```

## 7. Starter Code
See [`starter.py`](starter.py): the `MetricStore` class with `record` and `value_at`
signatures, docstrings and type hints. Bodies are TODO.

```bash
make try CHIP=01-observability/DC-OBS-01-metric-lookup
```

## 8. Hints
1. **Nudge:** Look at one metric at a time. What is special about the order its timestamps arrive in?
2. **Pattern:** Each metric's times form a sorted list, so a question about time T is a search
   in a sorted list: binary search.
3. **Near-solution:** Keep `dict[metric] -> (times, values)`. On `record`, append to both lists.
   On `value_at`, `i = bisect_right(times, T) - 1`, then return `values[i]` if `i >= 0`, else `None`.

## 9. Solution
**Approach**
1. Map each metric name to two parallel lists: sample times and values.
2. `record` appends. Arrival order is time order, so the lists stay sorted without extra work.
3. `value_at` binary searches the times for the last one `<= T`.
4. If there is no such time, or no such metric, return `None`.

**Brute force:** Scan all samples of the metric, keeping the newest one `<= T`. That costs
O(n) per query, and a dashboard panel asks thousands of times per refresh.

**Optimal code:** [`solution.py`](solution.py)

```python
from bisect import bisect_right


class MetricStore:
    def __init__(self) -> None:
        self._series: dict[str, tuple[list[int], list[float]]] = {}

    def record(self, metric: str, value: float, timestamp: int) -> None:
        times, values = self._series.setdefault(metric, ([], []))
        times.append(timestamp)   # time order == arrival order, so still sorted
        values.append(value)

    def value_at(self, metric: str, timestamp: int) -> float | None:
        series = self._series.get(metric)
        if series is None:
            return None
        times, values = series
        i = bisect_right(times, timestamp) - 1   # last index with time <= timestamp
        return values[i] if i >= 0 else None
```

**Complexity**
- Time: `record` is O(1) amortised, because it only appends. `value_at` is O(log n) per
  query, because it is a binary search over one metric's n samples.
- Space: O(total samples), because every sample is stored once.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: a normal lookup between samples, an unknown
metric or empty store, before the first sample, a `0.0` value, independent metrics, a
production-style scrape gap after a node reboot, and a large-input check (100,000 samples,
5,000 queries) against an independent linear sweep.

## 11. Interview Talk Track
"This is a point-in-time lookup, the most common query a metrics database answers. Each
metric is a list of samples, and because a scraper only moves forward in time, the list is
already sorted as it arrives. So I store a hash map from metric name to two parallel
arrays, times and values. A write is an append, O(1). A read is a binary search for the
last time at or before the query, O(log n). The edge cases are a query before the first
sample, which returns None, and an exact match, which counts. Prometheus adds a 5-minute
lookback limit, so a series that stopped reporting disappears instead of showing a stale
value forever. At scale I'd move to compressed chunks, find the chunk first, then search inside it."

## 12. Level Up
1. **"Return None if the newest sample is more than 5 minutes old."** Take a `max_age`
   parameter. After finding index `i`, check `timestamp - times[i] <= max_age`. This is
   Prometheus's lookback delta, and it is why a dead target's line stops on a graph instead
   of going flat.
2. **"10 million series, and memory is the limit."** Two plain Python lists cost roughly 70 bytes
   per sample (an int object, a float object and two list pointers). Store samples in fixed-size chunks with delta-of-delta time encoding and XOR
   float encoding (the Gorilla paper), which brings a sample down to roughly 1–2 bytes.
   Keep a small index of each chunk's min and max time, and move old chunks to disk.
3. **"Samples can arrive out of order."** `insort` into a Python list costs O(n) per write.
   Accept late samples only inside a bounded window, buffer them, and merge-sort them in
   when the chunk is sealed. Prometheus's out-of-order support works in a similar way.
   DC-OBS-12 covers corrections.

## 13. Related Chips
- **DC-OBS-12 Late & Corrected Samples**: the same store, but samples can be late or rewritten.
- **DC-REL-08 Versioned Config Store**: binary search per key over snapshot IDs instead of times.
- **DC-OBS-10 Log Time-Range Query**: a range (start–end) instead of a single point.
