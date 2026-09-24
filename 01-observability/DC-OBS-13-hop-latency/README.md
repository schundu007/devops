Source: New

# DC-OBS-13 · Hop-to-Hop Average Latency

## 1. Header
| | |
|---|---|
| Chip ID | DC-OBS-13 |
| Difficulty | Medium |
| Pattern | Hash maps |
| Track | Observability & SRE (OBS) |
| Classic pattern | LeetCode 1396 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
Checkout p99 went from 180 ms to 900 ms after a deploy. The trace view shows requests
passing `checkout → inventory → payments`, and you need to know which hop got slow. The
tracing agent sends two events per hop: "request `t-03` entered at `checkout` at 1010 ms" and
"request `t-03` exited at `inventory` at 1290 ms". Hops finish out of order, and some requests
never finish at all. You need the average time per `(from, to)` pair, updated live.

## 3. Why This Is DevOps
**Production reality:** Distributed tracing records start and end events for each piece of
work, and the latency between two points is end minus start. Averages per route
(`checkout → inventory`) show which hop regressed. A collector has to match each end event to
its start event by an ID, keep only the requests still in flight, and fold finished ones into
running totals. Keeping every finished request would never fit in memory.

**Where you see it:** OpenTelemetry spans (start and end time per span, matched by span and
trace IDs), Jaeger and Zipkin, Grafana Tempo's service graph, and service-mesh metrics like
Istio's request duration between workloads.

**Reality check:** Real tracing systems report percentiles (p50, p99), not only the mean,
because one slow request can hide behind a good average. They also sample traces instead of
keeping all of them. And a span normally starts and ends in the *same* service. This chip
treats "enter at A, exit at B" as one hop, which is closer to measuring a path between two services.

**What breaks if you get it wrong:** If exits are matched to the wrong entries, for example by
service name instead of request ID, the averages blend unrelated requests. The slow hop then
looks healthy, and the team rolls back the wrong service.

## 4. Problem Statement
Build a `HopLatency` tracker.

- `enter(request_id, service, t)`: the request starts a hop at `service` at time `t`. A request
  has at most one open hop at a time.
- `exit(request_id, service, t)`: the request's open hop ends at `service` at time `t`, which
  is later than its entry time. The hop is now complete, and the ID may be reused.
- `average(from_service, to_service)`: the mean duration of all completed hops that entered at
  `from_service` and exited at `to_service`. Direction matters: A→B and B→A are different routes.

Hops that are still open do not count. `average` is only called for routes with at least
one completed hop.

## 5. Input / Output format and Constraints
- `request_id` and `service`: non-empty strings. `t`: an integer, `0 <= t <= 10^9`.
- `average` returns a float. Answers within `10^-5` of the true mean are accepted.
- Up to `2 * 10^4` calls in total.

## 6. Examples
**Example 1: a running average**
```
enter("r1", "gateway", 3); enter("r2", "gateway", 8)
exit("r1", "orders", 15); exit("r2", "orders", 20)
average("gateway", "orders") -> 12.0          # (12 + 12) / 2
enter("r3", "gateway", 21); exit("r3", "orders", 39)
average("gateway", "orders") -> 14.0          # (12 + 12 + 18) / 3
```

**Example 2: direction matters (edge case)**
```
enter("a", "x", 0); exit("a", "y", 10)
enter("b", "y", 0); exit("b", "x", 30)
average("x", "y") -> 10.0
average("y", "x") -> 30.0
```

**Example 3: an open hop is ignored**
```
enter("done", "api", 0); exit("done", "db", 7)
enter("stuck", "api", 1)                      # never exits
average("api", "db") -> 7.0
```

## 7. Starter Code
See [`starter.py`](starter.py): `HopLatency` with `enter`, `exit` and `average`. Bodies are TODO.

```bash
make try CHIP=01-observability/DC-OBS-13-hop-latency
```

## 8. Hints
1. **Nudge:** On `exit`, you need to know where and when that exact request entered. Key that lookup by ID.
2. **Pattern:** Two hash maps: one for open requests (`id → (service, t)`), and one for finished routes (`(from, to) → running totals`).
3. **Near-solution:** On `exit`, pop the open entry, add `t - start_t` to `totals[(start_service, service)]`, and add 1 to its count. `average` is total divided by count.

## 9. Solution
**Approach**
1. `open`: request ID → (entry service, entry time). Add on `enter`, remove on `exit`.
2. `stats`: (from, to) → [sum of durations, number of hops].
3. `exit` pops the open entry and adds the duration to its route's totals.
4. `average` divides the sum by the count.

**Brute force:** Store every completed hop in a list and average the matching ones on each
query. That is O(completed hops) per query, and memory grows forever.

**Optimal code:** [`solution.py`](solution.py)

```python
class HopLatency:
    def __init__(self) -> None:
        self._open: dict[str, tuple[str, int]] = {}             # id -> (service, t)
        self._stats: dict[tuple[str, str], list[int]] = {}      # (from, to) -> [sum, count]

    def enter(self, request_id: str, service: str, t: int) -> None:
        self._open[request_id] = (service, t)

    def exit(self, request_id: str, service: str, t: int) -> None:
        start_service, start_t = self._open.pop(request_id)     # frees the id for reuse
        stat = self._stats.setdefault((start_service, service), [0, 0])
        stat[0] += t - start_t
        stat[1] += 1

    def average(self, from_service: str, to_service: str) -> float:
        total, count = self._stats[(from_service, to_service)]
        return total / count
```

**Complexity**
- Time: O(1) for every call, because each one is a constant number of hash map operations.
- Space: O(R + P), for R requests in flight and P distinct (from, to) routes. Finished
  requests are folded into totals and not kept.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: a normal running average, a single hop, direction
mattering, a request ID reused after exit, an open hop being ignored, production-style trace
spans that finish out of order, and a 30,000-event random check against a brute-force record of every hop.

## 11. Interview Talk Track
"This is span latency, the way a tracing collector computes it. Every hop has a start
event and an end event with the same request ID, so I keep a hash map of requests in flight,
ID to entry service and time. On exit I pop that entry, compute the duration, and add it to
running totals keyed by the (from, to) pair. The average is total over count. Every call is
O(1), and memory is only in-flight requests plus one entry per route, not per request. Two
things I'd raise in a real system: averages hide tail latency, so I'd keep a histogram per
route to get p99. And requests that never exit leak memory, so open entries need a timeout that
drops them and counts them as errors."

## 12. Level Up
1. **"p99, not the mean."** Replace `[sum, count]` with a fixed-bucket histogram per route
   (for example exponential buckets from 1 ms to 60 s). p99 is the bucket where the
   cumulative count passes 99%. This is the same trade-off Prometheus histograms make:
   fixed memory for an approximate percentile.
2. **"Requests that never exit fill memory."** Keep a min-heap of `(entry time, id)`. Every
   second, pop entries older than a timeout (say 30 s), remove them from `open`, and count them
   in a `timeouts[(from, ?)]` metric. Old heap entries whose ID has already exited are skipped lazily.
3. **"100 collectors, each seeing part of the traffic."** Sums and counts merge exactly: add
   them up across collectors and divide once. That only works if both events of a request
   reach the same collector, so route by a hash of the trace ID. Many tracing pipelines use
   a similar trace-ID-based load-balancing step before tail sampling.

## 13. Related Chips
- **DC-OBS-08 Live Latency Percentiles**: exact percentiles over a stream, the "p99 not mean" follow-up.
- **DC-SEC-18 Session Token Manager**: open entries with expiry, like the timeout follow-up.
- **DC-OBS-14 Multi-Node Log Timeline Merge**: combining events from many sources in time order.
