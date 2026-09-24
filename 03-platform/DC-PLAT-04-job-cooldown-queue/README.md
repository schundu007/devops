Source: Handbook #73 Task Scheduler — `apps/camora/src/data/capra/top100/73.json` (copied unchanged as `handbook.json`)

# DC-PLAT-04 · Job Queue with Cooldown

## 1. Header `DevOps layer`
| | |
|---|---|
| Chip ID | DC-PLAT-04 |
| Difficulty | Medium |
| Pattern | Greedy + max-heap (the handbook's optimal is the counting formula) |
| Track | Platform Engineering, Scheduling & Allocation (PLAT) |
| Classic pattern | LeetCode 621 |
| Premium | No |
| Time box | 25 min |
| Source | Handbook #73 Task Scheduler |

## 2. The Scenario `DevOps layer`
The nightly maintenance worker for `acct-prod-01` has a backlog: four `rotate-keys` jobs, three
`snapshot` jobs and one `cert-renew` job. Each job takes one slot. The cloud API behind each job
type is rate-limited, so two jobs of the same type need at least 2 slots between them, or the
second one is throttled and retried. Jobs of different types can run back to back. What is the
shortest schedule, counting slots where the worker sits idle waiting out a cooldown?

**Mapping: DevOps term → handbook name**

| DevOps term | Handbook name |
|---|---|
| one queued job, labelled by its type | `tasks[i]` (a letter A–Z) |
| slots that must pass between two jobs of the same type | `n` |
| one worker slot (runs one job or waits) | one time unit |
| shortest schedule, including idle slots | the return value |

## 3. Why This Is DevOps `DevOps layer`
**Production reality:** Many operations can't be repeated back to back: cloud APIs throttle
repeated calls, and scaling actions and alert notifications have cooldowns. A worker that
drains a mixed queue should fill each cooldown gap with a different job type instead of
sleeping. The job type with the most copies decides the length: it needs `n` slots between
each copy, and everything else fits into those gaps, unless there are so many other jobs that
no gap is left and the answer is just the number of jobs.

**Where you see it:** AWS EC2 Auto Scaling cooldown periods, Alertmanager `repeat_interval`
per alert group, cloud API rate limits (per-API throttling in AWS, GCP and Azure).

**Reality check:** Real workers don't know the whole backlog up front. Jobs keep arriving, so
they schedule online: a priority queue of ready job types plus a "cooling" queue. The formula
here answers the offline question, the minimum possible makespan (total time from the first job
to the last), which is a useful lower bound when you set SLAs for the nightly window.

**What breaks if you get it wrong:** A worker that runs the same job type back to back gets
throttled, retries with backoff, and the "30-minute" maintenance window runs into business
hours, while it could have run the other job types in those same slots.

## 4. Problem Statement `From handbook`
You are given an array `tasks` of CPU tasks, each labelled with an uppercase letter from `A` to `Z`, and a non-negative integer `n`. Each time unit the CPU either finishes one task or stays idle, and tasks may be done in any order.

There is a **cooling period**: two tasks with the same label must be separated by at least `n` time units.

Return the **minimum number of time units** needed to complete all tasks.

## 5. Input / Output format and Constraints
**Input / Output format `(added)`:** `leastInterval(tasks: List[str], n: int) -> int`, a
module-level function in the handbook.

**Constraints `From handbook`**
- 1 ≤ tasks.length ≤ 10⁴
- tasks[i] is an uppercase English letter
- 0 ≤ n ≤ 100

## 6. Examples `From handbook`
**Example 1 — Repeated words**
```
Input:  tasks = ["A", "A", "A", "B", "B", "B"], n = 2
Output: 8
```
One schedule is `A → B → idle → A → B → idle → A → B`.

**Example 2 — Repeated words**
```
Input:  tasks = ["A", "C", "A", "B", "D", "B"], n = 1
Output: 6
```
`A → B → C → D → A → B` needs no idle time.

**Example 3 — Repeated words**
```
Input:  tasks = ["A", "A", "A", "B", "B", "B"], n = 3
Output: 10
```
`A → B → idle → idle → A → B → idle → idle → A → B`.

## 7. Starter Code `(added)`
The handbook builds its starter from the problem's function signature and stores no starter file. See
[`starter.py`](starter.py): the same `leastInterval` function, with a TODO body.

```bash
make try CHIP=03-platform/DC-PLAT-04-job-cooldown-queue
```

## 8. Hints `From handbook`
1. The most frequent task dictates the shape of the schedule: its copies must be spaced `n` units apart, creating gaps that other tasks can fill.
2. Count frequencies. Let `maxFreq` be the highest count and `maxCount` the number of letters that reach it. (A max-heap simulation also works but is slower to write.)
3. The frame built around the most frequent tasks takes `(maxFreq - 1) * (n + 1) + maxCount` units. If there are more tasks than that, no idles are needed, so return `max(tasks.length, frame)`.

## 9. Solution `From handbook`
#### Sorting by Frequency
Sort tasks by frequency and simulate the scheduling process, placing tasks in order of frequency with cooldown gaps.

- Use max-heap to always pick most frequent
- Process tasks in cycles of n+1
- Re-insert tasks with decremented count
- Idle time fills unused cycle slots

Time: O(n * m) · Space: O(26)

```python
def leastInterval(tasks, n):
    from collections import Counter
    import heapq
    heap = [-c for c in Counter(tasks).values()]
    heapq.heapify(heap)
    time = 0
    while heap:
        # each cycle runs up to n + 1 tasks, most frequent first
        cycle = []
        for _ in range(n + 1):
            if heap:
                cycle.append(heapq.heappop(heap))
        for cnt in cycle:
            if cnt + 1 < 0:
                heapq.heappush(heap, cnt + 1)
        # a full cycle (idles included) unless this was the last one
        time += n + 1 if heap else len(cycle)
    return time

```

#### Math Formula (Optimal)
The minimum time is determined by the most frequent task. Calculate idle slots and fill them with other tasks.

- Formula: (maxFreq-1) * (n+1) + maxCount
- maxCount = number of tasks with max frequency
- Result is at least total number of tasks
- Idle slots are filled by less frequent tasks

Time: O(n) · Space: O(1)

```python
def leastInterval(tasks, n):
    from collections import Counter
    count = Counter(tasks)
    max_freq = max(count.values())
    max_count = sum(1 for v in count.values() if v == max_freq)
    result = (max_freq - 1) * (n + 1) + max_count
    return max(result, len(tasks))
```

`solution.py` is the handbook's optimal Python solution (Math Formula), copied unchanged. The
catalog lists this chip as "Greedy + max-heap". That tick-by-tick simulation gives the same
answer, and the tests use it as an independent check. The handbook's Java, C++, Go, JavaScript
and Bash versions are in `handbook.json` → `solutions[].code`.

## 10. Tests
**From handbook:** 30 cases in `handbook.json` → `tests`, run unchanged by `test_chip.py`.

**`(added)`** [`test_chip.py`](test_chip.py) wraps those cases in pytest (calling the
module-level `leastInterval`). It runs **every** Python solution from the handbook (the Step 3
check). It adds DevOps-layer cases: the rate-limited rotation backlog, `n = 0`, 26 job types
with no idle slots, and 300 random backlogs plus one 10,000-job backlog, all checked against
a separate max-heap simulation.

## 11. Interview Talk Track `DevOps layer`
"The job type with the most copies sets the length. If `rotate-keys` has 4 copies and needs 2
slots between runs, I get 3 full frames of 3 slots each, plus a final slot for the last copy.
If two types tie for the most copies, the last frame holds both. Every other job slides into
the gaps. The answer is the larger of that frame count and the total job count, because once
the gaps are full, nothing ever idles. That's O(n) to count. In a live system I'd simulate it
instead: a max-heap of ready types by remaining count, and a queue of types still cooling
down, so new jobs can arrive while it runs."

## 12. Level Up `DevOps layer`
1. **"Jobs keep arriving during the night."** Switch to the online simulation: a max-heap of
   ready types keyed by remaining count, and a FIFO of `(ready_at, type)` for cooling types.
   Each tick, move ready types back, then run the top of the heap. It is O(log k) per job, where k is the number of types.
2. **"Different job types have different cooldowns."** The formula breaks, because it assumes
   one `n`. Keep the simulation, with `ready_at = now + n_type + 1` for each type. Greedy by
   remaining count is a heuristic now, not guaranteed optimal. Say so if asked.
3. **"Jobs must run in the order they were queued."** Then there is no reordering to fill the
   gaps. Walk the list and track each type's last run, so each job starts at
   `max(now, last[type] + n + 1)`. The handbook's "Tasks in fixed order" variant is exactly this.

## 13. Related Chips `DevOps layer`
- **DC-OBS-09 Log Flood Suppressor**: a per-message cooldown decided one event at a time.
- **DC-PLAT-08 Weighted Job Dispatcher**: heaps that choose which worker runs the next job.
- **DC-SEC-18 Session Token Manager**: time-based expiry per key.
