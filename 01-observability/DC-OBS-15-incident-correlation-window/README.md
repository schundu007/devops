Source: New

# DC-OBS-15 · Incident Correlation Window

## 1. Header
| | |
|---|---|
| Chip ID | DC-OBS-15 |
| Difficulty | Hard |
| Pattern | Min-heap + sliding window |
| Track | Observability & SRE (OBS) |
| Classic pattern | LeetCode 632 |
| Premium | No |
| Time box | 40 min |
| Source | New |

## 2. The Scenario
At 03:40 the `orders-db` primary failed over. Over the next 10 minutes, `orders`, `payments`
and `search` all logged errors, but each service also has its usual background errors. For
each service you have a sorted list of error times, in seconds after 03:40:00. You want the
**narrowest** window that contains at least one error from every service. If all three
failed together, that window is tiny, and it points at the moment the shared dependency broke.

## 3. Why This Is DevOps
**Production reality:** When several services fail because they share a dependency (a
database, DNS, a network link), their errors cluster in time. Background noise is spread out.
So the tightest window that touches every affected service is a strong hint of a common cause,
and its start is a good guess at when the shared dependency broke. Finding it takes one pointer
per service: a min-heap of the current error from each service, moving the earliest pointer forward.

**Where you see it:** incident correlation in AIOps tools (grouping alerts from different
services that fire close together), Alertmanager's `group_wait` and `group_interval` (grouping
alerts that arrive together), and manual postmortem timelines built in Grafana or Kibana.

**Reality check:** Real correlation engines use fixed or learned time windows plus
topology (which services depend on what), not an exact "smallest window" search. This chip is
the exact version, which is useful in a postmortem when you already know which services were involved.

**What breaks if you get it wrong:** If you pick a wide window, the three services look
unrelated and the team investigates three separate incidents, while the one shared database
failover goes unnoticed for another hour.

## 4. Problem Statement
You get `error_times`, one list per service. Each list holds that service's error times,
sorted ascending and never empty.

Return `[start, end]`: the narrowest window (both ends inclusive) that contains at least one
error time from **every** service. The width is `end - start`. If several windows are
equally narrow, return the one with the smallest `start`.

## 5. Input / Output format and Constraints
- `error_times: list[list[int]]`, with `1 <= len(error_times) <= 3500`.
- `1 <= len(error_times[s]) <= 50`, with each list sorted ascending.
- `-10^5 <= error_times[s][i] <= 10^5`.
- Returns `list[int]` of length 2.

## 6. Examples
**Example 1: three services**
```
tightest_window([[4, 10, 15, 24, 26], [0, 9, 12, 20], [5, 18, 22, 30]]) -> [20, 24]
# 24 from service 0, 20 from service 1, 22 from service 2
```

**Example 2: a tie (edge case)**
```
tightest_window([[1, 10], [3, 12]]) -> [1, 3]   # [10, 12] is as narrow, but starts later
```

**Example 3: one service**
```
tightest_window([[7, 9, 40]]) -> [7, 7]   # one error covers every (the only) service
```

## 7. Starter Code
See [`starter.py`](starter.py): `tightest_window(error_times)` with a docstring and type
hints. The body is TODO.

```bash
make try CHIP=01-observability/DC-OBS-15-incident-correlation-window
```

## 8. Hints
1. **Nudge:** Pick one error from each service. The window they form runs from the smallest to the largest of those picks.
2. **Pattern:** Start with the first error of every service, which is k pointers. The only way to shrink the window is to move the pointer at the **smallest** time forward. A min-heap finds it quickly.
3. **Near-solution:** Push `(first time, service, 0)` for each service and track `hi`, the
   largest time in the heap. Repeatedly pop the min `lo`, record `[lo, hi]` if it is narrower,
   then push that service's next time and update `hi`. Stop when the popped service has no next time.

## 9. Solution
**Approach**
1. Put the first error of every service into a min-heap, and track `hi` = the largest of them.
2. The heap's top is `lo`, so `[lo, hi]` holds one error from every service. Record it if it is the narrowest so far.
3. Pop `lo` and replace it with the next error from the same service, updating `hi`.
4. When the popped service has no more errors, stop. Any later window would have to leave that service out.

**Brute force:** For every error time as a start, take each service's first error at or
after it, and the window ends at the largest. That is O(n · k log m). With every pair of
start and end, it is even slower.

**Optimal code:** [`solution.py`](solution.py)

```python
import heapq


def tightest_window(error_times: list[list[int]]) -> list[int]:
    heap = [(times[0], s, 0) for s, times in enumerate(error_times)]
    heapq.heapify(heap)
    hi = max(times[0] for times in error_times)      # window end = largest head
    best = [heap[0][0], hi]
    while True:
        lo, s, i = heapq.heappop(heap)                # window start = smallest head
        if hi - lo < best[1] - best[0] or (hi - lo == best[1] - best[0] and lo < best[0]):
            best = [lo, hi]
        if i + 1 == len(error_times[s]):
            return best                                # service s has no later error
        nxt = error_times[s][i + 1]
        hi = max(hi, nxt)
        heapq.heappush(heap, (nxt, s, i + 1))
```

**Complexity**
- Time: O(n log k), for n error times across k services. Each time is pushed and popped
  once, and each heap operation costs O(log k).
- Space: O(k), because the heap holds exactly one pointer per service.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: the three-service example, a single service,
all services failing in the same second, a tie on width, one error per service, a
production-style database failover, and 40 random inputs checked against a brute-force search.

## 11. Interview Talk Track
"I want the tightest moment where every affected service was erroring, because that's
where a shared dependency most likely broke. I keep one pointer per service, starting at
its first error, in a min-heap, plus the largest current value. The heap's top and that
max form a window that touches every service. To make it narrower, the only move that can
help is to advance the earliest pointer, so I pop it and push that service's next error.
I record the best window as I go, and stop when some service runs out. That's O(n log k).
It's the same k-heads-in-a-heap idea as merging k sorted logs. In production I'd pair it with
the dependency graph: services that cluster in time *and* share a dependency are the real signal."

## 12. Level Up
1. **"50 services, but only 'most of them' need to be in the window."** Require at least m
   of k services. Keep a sliding window over the merged, sorted timeline with a count per
   service and a count of distinct services, and shrink from the left while distinct >= m.
   That is O(n log k) for the merge plus O(n) for the window.
2. **"Errors stream in live."** Keep a bounded recent window per service (the last 15 minutes)
   and rerun the search every minute, or keep the heap and advance it incrementally. Alert when
   the best width drops below a threshold such as 30 seconds.
3. **"Clocks disagree by up to 2 seconds."** A true common cause can then look up to 2
   seconds wider. Treat widths within the skew bound as equal, and prefer the window that also
   matches known dependencies.

## 13. Related Chips
- **DC-OBS-14 Multi-Node Log Timeline Merge**: the same heap of k stream heads, used to merge.
- **DC-OBS-16 Error Budget Window**: a sliding window over one stream.
- **DC-SEC-15 Impossible Travel Detector**: events close in time that should not be.
