Source: Handbook #64 Meeting Rooms II — `apps/camora/src/data/capra/top100/64.json` (copied unchanged as `handbook.json`)

# DC-PLAT-03 · Minimum CI Runners

## 1. Header `DevOps layer`
| | |
|---|---|
| Chip ID | DC-PLAT-03 |
| Difficulty | Medium |
| Pattern | Sort + min-heap (the handbook's optimal is a sweep line) |
| Track | Platform Engineering, Scheduling & Allocation (PLAT) |
| Classic pattern | LeetCode 253 |
| Premium | Yes (P). Free alternative: LeetCode 2406 Divide Intervals Into Minimum Number of Groups (Medium). It is the same question, except its intervals include both ends, so `[1,5]` and `[5,8]` *do* clash there. |
| Time box | 25 min |
| Source | Handbook #64 Meeting Rooms II |

## 2. The Scenario `DevOps layer`
The platform team runs a self-hosted pool of GitHub Actions runners for the `monorepo`. Every
morning from 09:00, merges trigger lint, unit, integration and e2e jobs, and each job has a known
start minute and end minute from yesterday's logs. Runners are expensive (8 vCPU, 32 GiB each),
but a job that waits in the queue blocks the merge train. How many runners must exist at the
busiest moment so no job ever waits?

**Mapping: DevOps term → handbook name**

| DevOps term | Handbook name |
|---|---|
| one CI job `[start, end)` in minutes | `intervals[i] = [startᵢ, endᵢ]` |
| one runner | one conference room |
| a runner freed at minute t takes a job starting at t | a room freed at `t` is reused at `t` |
| runners needed at the peak | the return value |

## 3. Why This Is DevOps `DevOps layer`
**Production reality:** Every runner pool, build farm and batch cluster has to answer "how
many workers do we need at the peak?" The answer is the maximum number of jobs running at
the same moment. Sort the start and end events and sweep through time, +1 on a start and −1
on an end, and the highest count reached is the pool size. The same number sizes database
connection pools, license seats and NAT port ranges.

**Where you see it:** GitHub Actions self-hosted runner pools and Actions Runner Controller
(ARC) scale sets, GitLab runner `concurrent` limits, Jenkins agent pools, Buildkite agent fleets.

**Reality check:** This sizes the pool from known start and end times. Real autoscalers
don't know the future: they react to queue depth, and they must also cover runner startup
time. It is also not full bin packing. Jobs with different CPU and memory needs go through a
real scheduler (the Kubernetes scheduler uses filter and score plugins), and one runner here
runs exactly one job.

**What breaks if you get it wrong:** Size one runner below the peak and the merge queue
stalls every morning: jobs sit in "Queued" for 20 minutes and engineers re-run pipelines,
which adds even more load.

## 4. Problem Statement `From handbook`
You are given an array of meeting time intervals `intervals`, where `intervals[i] = [startᵢ, endᵢ]`. Return the **minimum number of conference rooms** needed so that every meeting can be held.

A room freed at time `t` can be reused by a meeting that starts at time `t`.

## 5. Input / Output format and Constraints
**Input / Output format `(added)`:** `minMeetingRooms(intervals: List[List[int]]) -> int`, a
module-level function in the handbook.

**Constraints `From handbook`**
- 1 ≤ intervals.length ≤ 10⁴
- 0 ≤ startᵢ < endᵢ ≤ 10⁶

## 6. Examples `From handbook`
**Example 1 — 3 intervals**
```
Input:  intervals = [[0, 30], [5, 10], [15, 20]]
Output: 2
```
`[0,30]` needs its own room; `[5,10]` and `[15,20]` can share a second one.

**Example 2 — 2 intervals**
```
Input:  intervals = [[7, 10], [2, 4]]
Output: 1
```
The meetings never overlap.

## 7. Starter Code `(added)`
The handbook builds its starter from the problem's function signature and stores no starter file. See
[`starter.py`](starter.py): the same `minMeetingRooms` function, with a TODO body.

```bash
make try CHIP=03-platform/DC-PLAT-03-min-ci-runners
```

## 8. Hints `From handbook`
1. The answer equals the largest number of meetings that are running at the same moment.
2. Sort by start time and keep a min-heap of end times for the rooms currently in use (or sort all starts and all ends separately and sweep with two pointers).
3. For each meeting, if the earliest-ending room ends at or before this start, pop it; then push this meeting's end. The maximum heap size reached is the answer.

## 9. Solution `From handbook`
#### Sort + Check All Active
Sort by start time. Track all ongoing meetings. For each new meeting, count how many overlap.

- For each meeting, count overlapping meetings
- Maximum overlap at any point = rooms needed
- Simple but slow

Time: O(n²) · Space: O(1)

```python
def minMeetingRooms(intervals):
    intervals.sort(key=lambda x: (x[0], x[1]))
    max_rooms = 0
    for i in range(len(intervals)):
        start = intervals[i][0]
        # meeting i needs its own room, plus one for every earlier
        # meeting still running when it starts (a room freed at `start` is reusable)
        rooms = 1
        for j in range(i):
            if intervals[j][1] > start:
                rooms += 1
        max_rooms = max(max_rooms, rooms)
    return max_rooms

```

#### Sweep Line (Optimal)
Separate start and end times, sort them, and sweep through events. Track concurrent meetings.

- Sweep line: process starts and ends as events
- Start event: +1 room, End event: -1 room
- Maximum concurrent meetings = answer
- Two pointer approach on sorted start/end arrays

Time: O(n log n) · Space: O(n)

```python
def minMeetingRooms(intervals):
    # At equal times: endings free their rooms first, then zero-length
    # meetings briefly take a room, then new meetings start.
    END, INSTANT, START = 0, 1, 2
    events = []
    for s, e in intervals:
        if s == e:
            events.append((s, INSTANT))
        else:
            events.append((s, START))
            events.append((e, END))
    events.sort()
    rooms = max_rooms = 0
    for _, kind in events:
        if kind == END:
            rooms -= 1
        elif kind == INSTANT:
            max_rooms = max(max_rooms, rooms + 1)
        else:
            rooms += 1
            max_rooms = max(max_rooms, rooms)
    return max_rooms

```

`solution.py` is the handbook's optimal Python solution (Sweep Line), copied unchanged. The
catalog lists this chip as "Sort + min-heap". The heap version (sort by start, keep a min-heap
of end times, reuse the runner whose job ends first) gives the same answer in the same
O(n log n), and the sweep line is the handbook's choice. The handbook's Java, C++, Go and
JavaScript versions are in `handbook.json` → `solutions[].code`.

## 10. Tests
**From handbook:** 29 cases in `handbook.json` → `tests`, run unchanged by `test_chip.py`.

**`(added)`** [`test_chip.py`](test_chip.py) wraps those cases in pytest (calling the
module-level `minMeetingRooms`). It runs **every** Python solution from the handbook (the Step 3
check). It adds DevOps-layer cases: the 09:00 merge-queue morning, back-to-back jobs sharing
one runner, 25 jobs at once, and 2,000 random jobs checked against a separate brute force.

## 11. Interview Talk Track `DevOps layer`
"I need the peak number of jobs running at the same time, because that's how many runners
the pool needs so nothing queues. I turn each job into two events, a start and an end, sort
them by time, and sweep: +1 on a start, −1 on an end, tracking the maximum. The tie-break
matters: at the same minute I process ends before starts, because a runner freed at 10:00
can pick up a job starting at 10:00. That's O(n log n) for the sort. The equivalent heap
version keeps a min-heap of end times and reuses the runner that frees up first. In
production I'd size from a high percentile of daily peaks, plus runner boot time, rather than
one day's exact maximum."

## 12. Level Up `DevOps layer`
1. **"Each runner needs 3 minutes to boot and 1 minute of cleanup after a job."** Stretch
   each job to `[start − 3, end + 1)` before the sweep. The handbook's "Rooms need cleanup
   time" variant is this change. The peak grows, and that growth is the real cost of slow runners.
2. **"Jobs need different sizes: some want 2 vCPU, some 16."** The peak count is no longer
   enough. Sweep with +vCPU and −vCPU to get peak CPU demand (DC-SEC-06 is that
   difference-array check), then pack jobs onto machine sizes. That is bin packing, which is
   NP-hard, so real schedulers use scoring heuristics.
3. **"Scale the pool automatically instead of fixing its size."** Use the sweep offline to
   set a floor (the typical 09:00 peak) and a ceiling (the budget), and let a controller such
   as ARC scale between them based on the live queue depth.

## 13. Related Chips `DevOps layer`
- **DC-SEC-06 Tenant Quota Guardrail**: the same sweep, weighted by vCPU and checked against a quota.
- **DC-PLAT-09 Runner Pool Allocation**: which specific runner each job gets, and which one is busiest.
- **DC-PLAT-15 On-Call Coverage Gaps**: sweeping intervals to find where the count is zero.
