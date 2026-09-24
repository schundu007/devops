Source: Handbook #102 Design Hit Counter — `apps/camora/src/data/capra/top100/102.json` (copied unchanged as `handbook.json`)

# DC-OBS-02 · 5-Minute Error Counter

## 1. Header `DevOps layer`
| | |
|---|---|
| Chip ID | DC-OBS-02 |
| Difficulty | Medium |
| Pattern | Queue / sliding window |
| Track | Observability & SRE (OBS) |
| Classic pattern | LeetCode 362 |
| Premium | Yes (P). Free alternative: LeetCode 933 Number of Recent Calls (Easy), the same queue-and-expire idea. |
| Time box | 25 min |
| Source | Handbook #102 Design Hit Counter |

## 2. The Scenario `DevOps layer`
02:14 on a Saturday. `checkout-api` sits behind an ingress at 10.20.0.0/16, and every 5xx it
returns is one event with an epoch-second timestamp. The alert rule says: "Page if more than
150 5xx responses landed in the last 5 minutes." A bad deploy at 02:09 causes a 60-second burst of
three 5xx per second, followed by a trickle. The alert engine asks "how many in the last 300 seconds?"
at every evaluation tick, and has to keep answering correctly while old errors age out.

**Mapping: DevOps term → handbook name**

| DevOps term | Handbook name |
|---|---|
| one 5xx response | one `hit` |
| response time (epoch second) | `timestamp` |
| alert rule evaluation at time T | `getHits(T)` |
| errors in the last 5 minutes | the return value of `getHits`, window `(T - 300, T]` |
| alert engine state | `HitCounter` |

## 3. Why This Is DevOps `DevOps layer`
**Production reality:** Your checkout service must stay under 1% errors. Every 5xx response
is an event with a timestamp. The alerting system keeps only the events from the last 300
seconds and drops older ones as time moves on. When the count crosses the limit, it pages the
on-call engineer. Error-rate alerts and SLO burn-rate alerts are all built on this "count in the
last N seconds" question.

**Where you see it:** Prometheus `increase()` / `rate()` over a `[5m]` range, Alertmanager,
Datadog monitors, PagerDuty.

**Reality check:** Prometheus does not keep a list of every error. It stores a counter and
computes the change over the window. The queue in this chip is the simple, exact version of
the same idea. The 300-bucket version is close to how fixed-window rate limiters count per second.

**What breaks if you get it wrong:** Count the wrong window and you either page someone at
3 a.m. for nothing or miss a real outage. Here, an off-by-one at the window edge means the
alert resolves one second late, or it keeps flapping between firing and resolved.

## 4. Problem Statement `From handbook`
Count how many hits arrived in the **past five minutes** (300 seconds).

- `hit(timestamp)` — record one hit at that second
- `getHits(timestamp)` — how many hits landed in the window `(timestamp - 300, timestamp]`

Timestamps arrive in non-decreasing order, and several hits may share a second.

## 5. Input / Output format and Constraints
**Input / Output format `(added)`:** a design problem. `HitCounter()` builds the counter;
`hit(timestamp: int) -> None`; `getHits(timestamp: int) -> int`.

**Constraints `From handbook`**
- 1 <= timestamp <= 2 * 10^9
- Timestamps are non-decreasing across calls
- Up to 300 calls per second

## 6. Examples `From handbook`
**Example 1 — Window edge**
```
Input:  ops = ["HitCounter", "hit", "hit", "hit", "getHits", "hit", "getHits", "getHits"], vals = [[], [1], [2], [3], [4], [300], [300], [301]]
Output: [null, null, null, null, 3, null, 4, 3]
```
At t=301 the window is (1, 301], so the hit at second 1 has just fallen out.

**Example 2 — Same second**
```
Input:  ops = ["HitCounter", "hit", "hit", "hit", "getHits", "getHits"], vals = [[], [10], [10], [10], [10], [310]]
Output: [null, null, null, null, 3, 0]
```
Three hits share second 10; by t=310 all of them are outside the window.

## 7. Starter Code `(added)`
The handbook builds its starter from the problem's function signature and stores no starter file. See
[`starter.py`](starter.py): the same `HitCounter` signatures, with TODO bodies.

```bash
make try CHIP=01-observability/DC-OBS-02-error-counter
```

## 8. Hints
**From handbook**
1. Hits older than 300 seconds can never matter again, so they can be dropped rather than counted around.
2. The window is a fixed 300 seconds. That bound means you can keep one bucket per second and reuse them in a ring, which makes both operations O(1) regardless of traffic.

**`(added)` Near-solution:** Keep a deque of hit timestamps. In `getHits(t)`, pop from the
front while the front is `<= t - 300`, then return the deque's length. For fixed memory,
use 300 buckets indexed by `t % 300` that each store `(second, count)`.

## 9. Solution `From handbook`
**Ways to solve**

| Way | Idea | Time | Space | Use when |
|---|---|---|---|---|
| Queue of timestamps | Append each hit; on getHits drop timestamps at or before t − 300 from the front, then return the size. | O(1) amortised | O(hits in window) | Low or moderate traffic; simplest to explain. |
| 300 per-second buckets | Bucket t % 300 stores the second it holds and its count; reset it when a newer second lands there, and sum the buckets still inside the window. | O(1) hit, O(300) getHits | O(300) | Heavy traffic: memory stays fixed however many hits arrive. |

#### Queue of Timestamps
Keep every hit's timestamp in arrival order. Timestamps never go backwards, so expired hits are always at the front: pop them on each getHits and the queue's size is the answer.

- Expired hits sit at the front
- Each hit is removed at most once
- Memory grows with traffic

Time: O(1) amortised · Space: O(hits in the last 300 s)

```python
from collections import deque


class HitCounter:
    def __init__(self):
        self.hits = deque()

    def hit(self, timestamp: int) -> None:
        self.hits.append(timestamp)

    def getHits(self, timestamp: int) -> int:
        while self.hits and self.hits[0] <= timestamp - 300:
            self.hits.popleft()  # outside the window for good
        return len(self.hits)
```

#### Circular Buffer of 300 Buckets (Optimal)
One bucket per second of the window, indexed by `timestamp % 300`. Each bucket remembers which second it holds; when a hit lands on a bucket holding an older second, reset it first. getHits adds up the buckets whose second is still within 300 of now.

- Fixed memory regardless of traffic
- Store the second with each bucket to detect stale data
- Needs integer seconds to index by

Time: O(1) hit, O(300) getHits · Space: O(300)

```python
class HitCounter:
    def __init__(self):
        self.times = [0] * 300   # which second each bucket currently holds
        self.counts = [0] * 300

    def hit(self, timestamp: int) -> None:
        i = timestamp % 300
        if self.times[i] != timestamp:   # bucket holds an older second: reuse it
            self.times[i] = timestamp
            self.counts[i] = 0
        self.counts[i] += 1

    def getHits(self, timestamp: int) -> int:
        return sum(c for t, c in zip(self.times, self.counts) if timestamp - t < 300)
```

**Brute-force idea `(added)`:** Store every hit forever and count the ones inside the
window on each `getHits`. That is O(total hits) per query, and memory never shrinks.

**Follow-up (from handbook):** What if hits arrive at a million per second, or timestamps come as fractions of a second? A queue grows with traffic; per-second buckets do not, but they need an integer second to index by.

`solution.py` is the handbook's optimal Python solution, copied unchanged. The handbook's
Java, C++, Go and JavaScript versions are in `handbook.json` → `solutions[].code`.

## 10. Tests
**From handbook:** 30 cases in `handbook.json` → `tests`, run unchanged by `test_chip.py`.

**`(added)`** [`test_chip.py`](test_chip.py) wraps those cases in pytest. It also runs
**every** Python solution from the handbook against them (the Step 3 check), and adds two
DevOps-layer cases: the `checkout-api` burst from the scenario (window edges at +300, +358
and +359 s, and the alert resolving), and a 5,000-operation random cross-check against the definition.

## 11. Interview Talk Track `DevOps layer`
"This is the counter behind an error-rate alert: how many 5xx in the last five minutes.
Timestamps only move forward, so expired events are always at the front. I keep a queue,
append on every error, and on each query pop from the front anything at or before now minus
300, then return the size. Each event is added once and removed once, so it's O(1) amortised.
The catch is memory: at 10,000 errors a second the queue holds 3 million entries. So the
production version uses 300 per-second buckets in a ring: fixed memory, O(1) writes, and a
300-step sum on read. That is close to what Prometheus does: it doesn't store events, it
stores a counter and takes the difference over the window with `increase()`."

## 12. Level Up `DevOps layer`
1. **"1 million errors per second?"** The queue now needs 300 million entries. Use the
   300-bucket ring instead: memory is fixed at 300 counters whatever the traffic. To make `getHits`
   O(1) amortised too, keep a running total and a cursor at the last second seen. On each
   call, advance the cursor to now and subtract and zero every bucket it passes.
2. **"The service runs on 40 pods. How do you count across all of them?"** Don't ship raw
   events. Each pod exposes a monotonic counter, and the alert query sums the per-pod
   `increase()` values (`sum(increase(http_5xx_total[5m]))`). Sums of per-second buckets merge cleanly;
   exact per-event queues do not.
3. **"Sub-second timestamps, and a 5-minute window with 1-second accuracy is too coarse."**
   Use finer buckets (for example 3,000 buckets of 100 ms), or a two-level ring: seconds inside
   minutes. Memory goes up linearly with resolution. The handbook's follow-up covers why
   buckets need an integer index.

## 13. Related Chips `DevOps layer`
- **DC-OBS-09 Log Flood Suppressor**: the same timestamp-window check, per message.
- **DC-SEC-16 Brute-Force Burst Alert**: a sliding window per user or key instead of one global counter.
- **DC-OBS-11 Metric Bucket Counter**: buckets per minute, hour or day, the ring idea generalised.
