Source: New

# DC-PLAT-07 · Round-Robin Load Balancer

## 1. Header
| | |
|---|---|
| Chip ID | DC-PLAT-07 ★ |
| Difficulty | Hard |
| Pattern | Heap + sorted set |
| Track | Platform Engineering, Scheduling & Allocation (PLAT) |
| Classic pattern | LeetCode 1606 |
| Premium | No |
| Time box | 40 min |
| Source | New |

## 2. The Scenario
`upload-gw` spreads requests over `k` backends, `upload-0` to `upload-3`, in round-robin order.
Each backend takes one request at a time. Most requests take a second, but large file uploads take
30. When a request's turn lands on a busy backend, the gateway moves on to the next idle one,
and when every backend is busy it returns `503`. After an hour of traffic, one backend's CPU graph
is always higher than the rest. Replay the request log and find which backends actually served the most.

## 3. Why This Is DevOps
**Production reality:** Plain round robin assumes every request costs the same. Once some
requests are long, the backend that happens to get them is busy on its next turn, and the
skip-to-next-idle rule shifts its traffic onto its neighbours in a fixed pattern. Replaying real
arrival times and durations through the exact balancing rule shows which backends run hot, and
whether you are dropping requests, before you add capacity or change the algorithm.

**Where you see it:** NGINX upstream round robin (it skips servers marked down or failed, and
with `max_conns` it skips servers at their connection limit), HAProxy `balance roundrobin`, Envoy's
round-robin load balancer (which returns `503 no healthy upstream` when nothing is available),
AWS ALB round-robin routing.

**Reality check:** Real balancers track connections rather than exact finish times, and most
queue a request briefly instead of dropping it immediately. They also offer
`least_conn` / `leastconn` / least-request modes precisely because round robin behaves badly with
uneven request costs. The "skip busy, drop if all busy" rule here is a simplified, exact model of
that behaviour.

**What breaks if you get it wrong:** You scale out because "the pool is overloaded", while the
real issue is one hot backend. Or you miss that some requests are dropped with 503s even though
average CPU looks fine.

## 4. Problem Statement
There are `k` backends, numbered `0` to `k - 1`, and each one handles one request at a time.

Request `i` arrives at time `arrival[i]` (arrivals are strictly increasing) and keeps its backend
busy for `load[i]` time units, so that backend is idle again at time `arrival[i] + load[i]`. A
backend that becomes idle at time `t` can take a request that arrives at `t`.

Request `i` tries backend `i % k` first. If that one is busy, it tries `i % k + 1`, `i % k + 2`,
and so on, wrapping from `k - 1` back to `0`, and takes the first idle backend. If all `k`
backends are busy, the request is dropped.

Return the IDs of the backends that served the **most** requests, in increasing order.

## 5. Input / Output format and Constraints
- `busiest_backends(k: int, arrival: list[int], load: list[int]) -> list[int]`
- `1 <= k <= 10^5`, `1 <= len(arrival) == len(load) <= 10^5`
- `1 <= arrival[i], load[i] <= 10^9`, and `arrival` is strictly increasing.
- The output is non-empty and sorted ascending.

## 6. Examples
**Example 1: skip a busy backend**
```
k = 3, arrival = [0, 1, 2, 3], load = [10, 2, 10, 5]  -> [1]
```
r0→b0 (busy to 10), r1→b1 (busy to 3), r2→b2 (busy to 12). r3 prefers b0, which is busy, so it
takes b1, which became idle exactly at 3. b1 served 2 requests.

**Example 2: all busy means dropped (edge case)**
```
k = 2, arrival = [0, 1, 2], load = [100, 100, 1]  -> [0, 1]
```
r2 finds both backends busy and is dropped. Each backend served one request, so both tie.

**Example 3: wrap around**
```
k = 3, arrival = [0, 1, 2, 3, 4, 5], load = [1, 50, 50, 1, 1, 1]  -> [0]
```
b1 and b2 are held by long requests, so r4 and r5 wrap around to b0.

## 7. Starter Code
See [`starter.py`](starter.py): the `busiest_backends` signature, with a docstring and a TODO body.

```bash
make try CHIP=03-platform/DC-PLAT-07-round-robin-lb
```

## 8. Hints
1. **Nudge:** At each arrival you need two answers fast: which backends have finished, and which
   idle backend is the first one at or after `i % k`?
2. **Pattern:** A min-heap of `(free_time, backend)` releases finished backends in time order. A
   sorted collection of idle backend IDs answers "first ID `>= i % k`, else the smallest ID".
3. **Near-solution:** Before request `i`, pop every heap entry with `free_time <= arrival[i]` into
   a sorted list. Then `j = bisect_left(idle, i % k)`, and if `j == len(idle)`, set `j = 0` to wrap.
   Take `idle.pop(j)`, count it, and push `(arrival[i] + load[i], backend)`.

## 9. Solution
**Approach**
1. Keep a sorted list `idle` of free backend IDs (at first, all of them) and a min-heap `busy` of
   `(free_time, backend)`.
2. For each request, move every backend whose `free_time <= arrival` from `busy` back into `idle`.
3. If `idle` is empty, drop the request.
4. Otherwise, binary search `idle` for the first ID `>= i % k`, wrapping to index 0 if there is
   none. Remove it, count it, and push it onto `busy`.
5. Return every backend whose count equals the maximum.

**Brute force:** For each request, check backends `i % k, i % k + 1, …` one by one. That is
O(n · k), or 10^10 steps at the limits.

**Optimal code:** [`solution.py`](solution.py)

```python
import heapq
from bisect import bisect_left, insort


def busiest_backends(k, arrival, load):
    served = [0] * k
    free = list(range(k))                    # sorted idle backend IDs
    busy = []                                # (free_time, backend)
    for i, (t, d) in enumerate(zip(arrival, load)):
        while busy and busy[0][0] <= t:      # finished at t counts as idle
            insort(free, heapq.heappop(busy)[1])
        if not free:
            continue                         # all busy: dropped
        j = bisect_left(free, i % k)
        if j == len(free):
            j = 0                            # wrap around
        backend = free.pop(j)
        served[backend] += 1
        heapq.heappush(busy, (t + d, backend))
    top = max(served)
    return [b for b in range(k) if served[b] == top]
```

**Complexity**
- Time: O(n log n) for the heap and binary searches, plus the cost of inserting into and
  removing from the middle of a Python list, which is O(k) per operation. So the worst case is
  O(n · k), but that cost is one fast memory shift (`memmove`), which is far faster than the
  brute force's Python loop. A balanced tree or a segment tree over backend IDs (see Level Up)
  makes it O(n log k) strictly.
- Space: O(k), for the idle list, the heap and the counters.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: skipping a busy backend, dropping when all are busy,
one backend and one request, an all-idle tie, wraparound to lower IDs, a production-style "long
uploads make one backend hot" replay, and random replays (30 small ones plus one with 500
backends and 20,000 requests) checked against a separate one-by-one brute force.

## 11. Interview Talk Track
"I'm replaying traffic through round robin with 'skip busy, drop if all busy', which is roughly
what NGINX or Envoy do when a backend can't take a request. At each arrival I need two things.
First, which backends have finished: that's a min-heap keyed on finish time, popped until the top
is in the future. Second, the first idle backend at or after `i mod k`, with wraparound: a sorted
set of idle IDs and one binary search, falling back to the smallest ID. Each request is one heap
push, a few pops and one search, so it's O(n log n) with a real sorted set. Python has no sorted
set in the standard library, so a list with `insort` works and is fast in practice, and I'd say
that out loud. The output shows hot backends caused by uneven request cost, which is the
argument for least-connections balancing."

## 12. Level Up
1. **"Make it strictly O(log k) per request without a third-party sorted set."** Build a segment
   tree over backend IDs that stores whether any backend in each range is idle. "First idle ID
   `>= x`" becomes a descent through the tree in O(log k), and marking a backend busy or idle is a
   point update.
2. **"Compare against least-connections."** Replay the same log with a rule that picks the idle
   backend that has served the fewest requests so far (a heap keyed by count). Report the
   difference in the busiest backend's count and in dropped requests. That is a data-driven case
   for changing the balancing algorithm.
3. **"Instead of dropping, the gateway queues up to 100 requests."** Add a FIFO. When a backend
   frees up, hand it the oldest queued request, and drop only when the queue is full. The replay
   then also gives you queue-wait percentiles, which is what users actually notice.

## 13. Related Chips
- **DC-PLAT-08 Weighted Job Dispatcher**: two heaps, choosing by weight instead of rotation.
- **DC-PLAT-09 Runner Pool Allocation**: lowest-free-ID assignment with delays instead of drops.
- **DC-PLAT-10 Weighted Canary Router**: splitting traffic by weight rather than by turn.
