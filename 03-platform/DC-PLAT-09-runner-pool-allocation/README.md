Source: New

# DC-PLAT-09 · Runner Pool Allocation

## 1. Header
| | |
|---|---|
| Chip ID | DC-PLAT-09 |
| Difficulty | Hard |
| Pattern | Two min-heaps |
| Track | Platform Engineering, Scheduling & Allocation (PLAT) |
| Classic pattern | LeetCode 2402 |
| Premium | No |
| Time box | 40 min |
| Source | New |

## 2. The Scenario
Your team runs a pool of self-hosted CI runners, `ci-runner-0` to `ci-runner-2`, for the
`payments` monorepo. Every night at 01:00 a scheduled workflow queues 12 builds, one minute
apart, each about 10 minutes long. Developers complain that runner 0 always seems to be
busy while the others sit idle. Before you buy more runners, you replay the queue log to
find which runner really does the most work, and how the waiting pattern looks.

## 3. Why This Is DevOps
**Production reality:** CI systems keep a fixed or slowly scaling pool of runners. When a
job is queued, the scheduler hands it to an idle runner. If none is idle, the job waits in
the queue and starts on whichever runner frees up first, so it finishes later than planned.
Replaying this rule over a day of queue events tells you how busy each runner really was
and how long jobs waited. That is the data you need to size the pool or spot a runner that
gets more than its share of work.

**Where you see it:** GitHub Actions self-hosted runners and Actions Runner Controller,
GitLab Runner, Jenkins agents with a fixed executor count, Buildkite agent pools.

**Reality check:** Real schedulers do not always pick the lowest-numbered idle runner. They
match labels or tags, and the choice between idle runners is up to the implementation. The
"lowest number first" rule here is a fixed tie-breaker that makes the replay deterministic.
Real pools also autoscale, which this chip leaves out.

**What breaks if you get it wrong:** If the replay ignores the "wait, then run for the full
duration" rule, it shows no queueing at all. You conclude three runners are plenty, and the
next release night every build sits in the queue for 30 minutes.

## 4. Problem Statement
You have `n` runners numbered `0` to `n - 1`. Each job is `[queued_at, planned_end]`, and no
two jobs are queued at the same moment. Process jobs in order of `queued_at`:

- If one or more runners are idle, the job goes to the **lowest-numbered** idle runner and
  runs until `planned_end`.
- If no runner is idle, the job waits for the runner that becomes free **first** (the lowest
  number if several free up at the same moment). It then runs for its full duration,
  `planned_end - queued_at`, starting from that moment.
- A runner that frees up at time `t` is idle for a job queued at `t`.

Return the number of the runner that ran the most jobs. If several are tied, return the
lowest number. With no jobs, return `0`.

## 5. Input / Output format and Constraints
- `n`: an integer, `1 <= n <= 100`.
- `jobs`: a list of `[queued_at, planned_end]` pairs, `0 <= len(jobs) <= 10^5`.
- `0 <= queued_at < planned_end <= 5 * 10^5`, and all `queued_at` values are distinct.
- Jobs may be given in any order.
- Returns an `int` in `0..n-1`.

## 6. Examples
**Example 1: one runner does the short work**
```
n = 3, jobs = [[0,5],[1,2],[2,4],[3,9],[4,6],[6,7]]   -> 1
```
Runner 0 takes the job at 0 (busy until 5). Runner 1 takes 1–2, then 2–4 (it is free again
at 2), then 4–6. Runner 2 takes 3–9, and runner 0 takes 6–7. Runner 1 ran 3 jobs.

**Example 2: a job has to wait (edge case)**
```
n = 2, jobs = [[0,10],[1,11],[2,4]]   -> 0
```
At time 2 both runners are busy. Runner 0 frees first (at 10), so the 2-minute job runs
10–12 on runner 0. Runner 0 ran 2 jobs.

**Example 3: no jobs**
```
n = 4, jobs = []   -> 0
```

## 7. Starter Code
See [`starter.py`](starter.py): `busiest_runner(n, jobs)` with the full rules in the
docstring. The body is TODO.

```bash
make try CHIP=03-platform/DC-PLAT-09-runner-pool-allocation
```

## 8. Hints
1. **Nudge:** At each job you ask two questions: "which idle runner has the lowest number?"
   and "which busy runner frees up first?". Which structure answers "smallest" fast?
2. **Pattern:** Two min-heaps: one of idle runner numbers, and one of `(free_at, runner)`
   for busy runners. Before placing a job, move every busy runner with `free_at <= queued_at`
   back to the idle heap.
3. **Near-solution:** If the idle heap is not empty, pop the lowest runner and push
   `(planned_end, runner)`. Otherwise pop the busy top `(free_at, runner)` and push
   `(free_at + duration, runner)`. Count jobs per runner.

## 9. Solution
**Approach**
1. Sort the jobs by `queued_at`.
2. Keep `idle`, a min-heap of runner numbers (all runners at the start), and `busy`, a
   min-heap of `(free_at, runner)`. The tuple order breaks ties by runner number for free.
3. For each job, first move every busy runner with `free_at <= queued_at` into `idle`.
4. If a runner is idle, give it the job, ending at `planned_end`. Otherwise take the busy
   runner that frees first and extend it by the job's duration.
5. Count jobs per runner and return the one with the most, lowest number on a tie.

**Brute force:** For every job, scan all `n` runners to find idle ones or the earliest to
free up. That is O(m·n). It is fine for 100 runners, but it becomes the bottleneck when a
fleet has thousands of runners and millions of queue events.

**Optimal code:** [`solution.py`](solution.py)

```python
import heapq


def busiest_runner(n: int, jobs: list[list[int]]) -> int:
    idle = list(range(n))             # min-heap of idle runner numbers
    busy: list[tuple[int, int]] = []  # min-heap of (free_at, runner)
    ran = [0] * n
    for start, end in sorted(jobs):
        while busy and busy[0][0] <= start:           # runners done by now are idle
            _, runner = heapq.heappop(busy)
            heapq.heappush(idle, runner)
        if idle:
            runner = heapq.heappop(idle)
            heapq.heappush(busy, (end, runner))
        else:                                         # wait for the first to free up
            free_at, runner = heapq.heappop(busy)
            heapq.heappush(busy, (free_at + (end - start), runner))
        ran[runner] += 1
    return max(range(n), key=lambda r: (ran[r], -r))
```

**Complexity**
- Time: O(m log m + m log n), for sorting the m jobs plus a constant number of heap
  operations per job on heaps of size at most n.
- Space: O(n + m), for the two heaps and counters plus the sorted copy of the jobs.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: a normal three-runner replay, empty and
single-job inputs, a delayed job, a runner that frees up exactly when a job is queued (the
boundary), a tie, a production-style nightly burst on three runners, and a large random
check (20 rounds of 1,500 jobs) against an O(m·n) brute force.

## 11. Interview Talk Track
"This is a replay of a CI runner pool. Each job needs to know two things: the
lowest-numbered idle runner, and, if nobody is idle, the busy runner that frees up first.
Both are 'give me the smallest' questions, so I keep two min-heaps: idle runner numbers, and
busy runners keyed by free time and then runner number. For each job in time order, I first
move every runner that has finished by now back to idle. Then I either take the lowest idle
runner, or I pop the earliest busy one and push it back with its free time plus the job's
duration, because the job waited. Each job costs a few heap operations, so it's O(m log n)
after sorting. In a real system I'd also record the wait time per job, because the queue
delay is the number that tells you when to grow the pool."

## 12. Level Up
1. **"Also report the average and p95 queue wait."** In the no-idle branch the wait is
   `free_at - queued_at`. Record it per job (zero when a runner was idle) and compute the
   statistics at the end. p95 wait is a far better sizing signal than jobs per runner.
2. **"Runners have labels (`linux-x64`, `gpu`) and jobs require labels."** Keep one pair
   of heaps per label set, and route each job to the heaps that match its labels. For
   overlapping labels, check each candidate pool's top and take the earliest.
3. **"The pool autoscales: a new runner starts 90 seconds after the queue gets deeper than 5."**
   Add runner-start events to the timeline. Process events in time order with one more heap
   of pending starts, and push each new runner into `idle` when its start time arrives.
   This is a small discrete-event simulation.

## 13. Related Chips
- **DC-PLAT-08 Weighted Job Dispatcher**: the same two-heap pattern, with weights instead of runner numbers.
- **DC-PLAT-03 Minimum CI Runners**: how many runners you need so nobody ever waits.
- **DC-PLAT-07 Round-Robin Load Balancer**: busy-server tracking with dropped requests instead of waiting ones.
