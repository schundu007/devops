Source: New

# DC-PLAT-08 · Weighted Job Dispatcher

## 1. Header
| | |
|---|---|
| Chip ID | DC-PLAT-08 |
| Difficulty | Medium |
| Pattern | Two min-heaps |
| Track | Platform Engineering, Scheduling & Allocation (PLAT) |
| Classic pattern | LeetCode 1882 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
The `data-pipeline` team's batch queue runs on a mixed fleet: two on-demand workers at $0.90/hour
and two spot workers at $0.30/hour. One job is queued every second, and each job has a known
run time. The dispatcher's rule is simple: send each job to the **cheapest idle** worker, break
ties by the lowest worker ID, and if everyone is busy, hold the job until the first worker frees
up. Finance wants to know which worker ran each job, to check that the cheap workers really take
most of the load.

## 3. Why This Is DevOps
**Production reality:** Worker pools are rarely identical. Some nodes are cheaper (spot), faster,
or closer to the data, and the dispatcher should prefer them whenever they are free. That is two
priority queues: idle workers ordered by preference, and busy workers ordered by finish time. On
each dispatch, move finished workers back to the idle queue and take the best one. If none is
idle, advance the clock to the next finish time instead of polling.

**Where you see it:** Slurm node `Weight` (all else being equal, jobs go to the lowest-weight nodes
first), Buildkite agent `priority` (higher-priority agents are assigned work first), and a
similar idea in the Kubernetes scheduler, which scores the feasible nodes and picks the best score.

**Reality check:** Real dispatchers don't know run times in advance, and they match on labels,
CPU and memory before preference. The Kubernetes scheduler filters nodes and then scores them with
several plugins, rather than using one fixed weight. This chip is the core loop, with one static
preference and known durations.

**What breaks if you get it wrong:** Pick the wrong worker, or let time go backwards when a job
has to wait, and expensive on-demand nodes run jobs while spot nodes sit idle. The bill goes up,
and nobody notices, because every job still finishes.

## 4. Problem Statement
You have `m` workers. Worker `i` has a preference weight `weights[i]`, and lower is better (think
cost per hour).

Job `j` joins the queue at second `j` and needs `durations[j]` seconds of work. Jobs are dispatched
**in queue order**: job `j` cannot start before job `j - 1` was dispatched.

When job `j` is dispatched, it goes to the **idle** worker with the smallest weight, breaking ties
by the smallest index. If no worker is idle at that moment, the job waits until the earliest
moment a worker becomes idle, and starts then. A worker that finishes at time `t` is idle at time `t`.

Return a list where element `j` is the index of the worker that ran job `j`.

## 5. Input / Output format and Constraints
- `assign_jobs(weights: list[int], durations: list[int]) -> list[int]`
- `1 <= len(weights) <= 2 * 10^5`, `1 <= len(durations) <= 2 * 10^5`
- `1 <= weights[i], durations[j] <= 2 * 10^5`
- The output has the same length as `durations`.

## 6. Examples
**Example 1: the cheapest idle worker wins**
```
weights = [3, 1, 2], durations = [2, 2, 1]  -> [1, 2, 1]
```
Job 0 takes worker 1 (weight 1) until second 2. At second 1, worker 1 is busy, so job 1 takes worker
2. At second 2, worker 1 is idle again and wins job 2.

**Example 2: every worker busy (edge case)**
```
weights = [1, 9], durations = [10, 2, 1]  -> [0, 1, 1]
```
At second 2 both workers are busy. Worker 1 finishes first, at second 3, so job 2 waits and runs
there, even though it is the more expensive worker.

**Example 3: a single worker**
```
weights = [7], durations = [3, 1, 4]  -> [0, 0, 0]
```

## 7. Starter Code
See [`starter.py`](starter.py): the `assign_jobs` signature, with a docstring and a TODO body.

```bash
make try CHIP=03-platform/DC-PLAT-08-weighted-job-dispatcher
```

## 8. Hints
1. **Nudge:** At each dispatch you need the best idle worker, and when nobody is idle, the worker
   that finishes first. Those are two different orderings.
2. **Pattern:** Two min-heaps: idle workers keyed by `(weight, index)`, and busy workers keyed by
   `(finish_time, weight, index)`.
3. **Near-solution:** Keep a clock `now = max(now, j)`. If the idle heap is empty, jump to
   `now = busy[0].finish_time`. Move every busy worker with `finish_time <= now` to the idle heap,
   pop the best idle worker, and push it back as busy until `now + duration`.

## 9. Solution
**Approach**
1. Put every worker in an idle min-heap keyed by `(weight, index)`.
2. For job `j`, set the clock to `max(clock, j)`: jobs go in order, and job `j` can't start
   before it is queued.
3. If nobody is idle, move the clock forward to the earliest finish time.
4. Release every busy worker that has finished by the clock into the idle heap.
5. Pop the best idle worker, record it, and push it into the busy heap until `clock + duration`.

**Brute force:** For every job, scan all `m` workers to find the idle ones and the best of them.
That is O(n · m), or 4 · 10^10 steps at the limits.

**Optimal code:** [`solution.py`](solution.py)

```python
import heapq


def assign_jobs(weights, durations):
    free = [(w, i) for i, w in enumerate(weights)]   # (weight, index)
    heapq.heapify(free)
    busy = []                                        # (idle_again_at, weight, index)
    out, now = [], 0
    for j, d in enumerate(durations):
        now = max(now, j)                            # queued at second j, dispatched in order
        if not free:
            now = max(now, busy[0][0])               # wait for the first finisher
        while busy and busy[0][0] <= now:
            _, w, i = heapq.heappop(busy)
            heapq.heappush(free, (w, i))
        w, i = heapq.heappop(free)
        out.append(i)
        heapq.heappush(busy, (now + d, w, i))
    return out
```

**Complexity**
- Time: O((n + m) log m). Each job does one pop and one push on each heap, and each worker moves
  between the heaps at most once per job it runs.
- Space: O(m + n), for the two heaps of workers and the output list.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: the cheapest idle worker, index tie-breaks, a single
worker, a worker idle again at exactly `t`, a waiting job taking the first (expensive) finisher, a
spot versus on-demand fleet, and random runs (40 small ones plus one with 300 workers and 20,000
jobs) checked against a separate scan-every-worker brute force.

## 11. Interview Talk Track
"This is a dispatcher for a mixed fleet: always use the cheapest idle worker, like Slurm's node
weight. I keep two min-heaps. Idle workers are keyed by weight and then index, so the top is the
worker I want. Busy workers are keyed by finish time, so the top is the next one to free up. For
each job I set the clock to its queue time. If nobody is idle, I jump the clock to the next finish
time instead of ticking second by second, and that jump matters when durations are large. Then I
move every finished worker back to idle and pop the best one. Every operation is a heap operation,
so it's O((n + m) log m). The subtle bug to avoid is letting the clock go backwards after a job had
to wait, because jobs must go out in order."

## 12. Level Up
1. **"Jobs need labels: GPU jobs only run on GPU workers."** Keep one idle heap per label, or per
   label set. A job pops from the heap for its label. The busy heap stays shared, and each worker
   returns to its own label's heap when it finishes.
2. **"Spot workers can be taken away mid-job."** When the cloud reclaims a worker, remove it from the
   busy heap. Heaps can't delete from the middle, so mark it dead and skip it when it reaches the top
   (lazy deletion, DC-OBS-12), then requeue its job at the front of the queue.
3. **"Durations are unknown until the job finishes."** Run it as an event loop: a job's completion
   event pushes the worker back to idle, and dispatch happens whenever a job is queued or a worker frees
   up. The same two heaps work. Only the clock now comes from real events instead of arithmetic.

## 13. Related Chips
- **DC-PLAT-09 Runner Pool Allocation**: the same two-heap loop, choosing the lowest ID and counting jobs per runner.
- **DC-PLAT-07 Round-Robin Load Balancer**: rotation instead of weight, and drop instead of wait.
- **DC-PLAT-03 Minimum CI Runners**: how many workers you need in the first place.
