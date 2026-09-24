Source: New

# DC-SEC-06 · Tenant Quota Guardrail

## 1. Header
| | |
|---|---|
| Chip ID | DC-SEC-06 |
| Difficulty | Medium |
| Pattern | Difference array / prefix sum |
| Track | Cloud Security & IAM (SEC) |
| Classic pattern | LeetCode 1094 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
The `analytics` tenant on your shared batch platform has a hard quota of 96 vCPUs. Their
nightly schedule has `etl-orders` (32 vCPU, 01:00–03:00), `etl-clickstream` (32 vCPU,
02:00–04:00), `reindex-search` (16 vCPU, 02:30–02:50), and a new `ml-features` job (24 vCPU,
02:45–03:20). The merge request adds `ml-features`. Before it merges, a CI check must answer:
does this schedule ever go over quota at any moment? (It does: 104 vCPUs at 02:45.)

## 3. Why This Is DevOps
**Production reality:** Shared platforms give each tenant or team a hard limit on CPU, memory or
concurrent jobs. A schedule of jobs is a set of time ranges with a load each, and the question
is the peak total load. The trick is to record only the changes: +load when a job starts and
−load when it ends. Then walk the change points in time order with a running sum. The highest
running sum is the peak. This is a guardrail: it catches the problem at review time, not at
02:45 when jobs start failing.

**Where you see it:** Kubernetes `ResourceQuota` (a hard per-namespace limit), AWS service
quotas such as the per-Region vCPU limits for EC2 On-Demand instances, AWS Batch compute
environments with a maximum vCPU count, and capacity reservations.

**Reality check:** Kubernetes `ResourceQuota` checks requests at admission time, one pod at a
time. It does not look ahead at a schedule. This chip is the planning-time version. Real
schedulers also queue jobs that don't fit instead of failing them, so the peak you compute
becomes a delay, not an error.

**What breaks if you get it wrong:** Counting a job as still running at its end time rejects a
valid back-to-back schedule. Missing the overlap lets the schedule through, and at 02:45 the
quota admission check rejects `ml-features`, so the morning dashboards have no fresh data.

## 4. Problem Statement
Each job is `(vcpus, start, end)`. It holds `vcpus` from `start` up to, but not including,
`end`, so a job that ends at 60 and a job that starts at 60 never overlap. A job with
`start == end` never runs.

- `peak_usage(jobs)` returns the highest total vCPU in use at any moment (0 if there are no jobs).
- `fits_quota(jobs, quota)` returns `True` if that peak is at most `quota`.

## 5. Input / Output format and Constraints
- `peak_usage(jobs: list[tuple[int, int, int]]) -> int`,
  `fits_quota(jobs: list[tuple[int, int, int]], quota: int) -> bool`.
- `0 <= len(jobs) <= 10^5`. `1 <= vcpus <= 10^4`. `0 <= start <= end <= 10^9` (minutes or seconds).
- `0 <= quota <= 10^9`.

## 6. Examples
**Example 1: overlap**
```
peak_usage([(8, 0, 60), (16, 30, 90), (4, 45, 120)])  -> 28     # all three run during 45-60
fits_quota(same, 27)                                  -> False
```

**Example 2: back to back (edge case)**
```
peak_usage([(32, 0, 60), (32, 60, 120)])  -> 32     # the first ends exactly as the second starts
```

**Example 3: empty and zero-length**
```
peak_usage([])                        -> 0
peak_usage([(100, 5, 5), (3, 0, 10)]) -> 3      # the zero-length job never runs
```

## 7. Starter Code
See [`starter.py`](starter.py): `peak_usage` and `fits_quota` with docstrings and type hints.
Bodies are TODO.

```bash
make try CHIP=02-security/DC-SEC-06-tenant-quota-guardrail
```

## 8. Hints
1. **Nudge:** The total load only changes when a job starts or ends. How many moments do you actually need to check?
2. **Pattern:** A difference array: +vcpus at the start, −vcpus at the end, then a running (prefix) sum over time.
3. **Near-solution:** Build a dict `delta[time] += change`, so ends and starts at the same time cancel out
   first. Walk `sorted(delta)` with a running total, and track the maximum.

## 9. Solution
**Approach**
1. For each job with `start < end`, add `+vcpus` at `start` and `-vcpus` at `end` in a dict.
2. Sort the change times.
3. Walk them with a running total: that is the load right after time `t`. Keep the maximum.
4. `fits_quota` compares the peak with the quota.

**Brute force:** For each job's start time, add up every job running at that moment. That is
O(n²), about 10^10 steps for 10^5 jobs.

**Optimal code:** [`solution.py`](solution.py)

```python
def peak_usage(jobs: list[tuple[int, int, int]]) -> int:
    delta: dict[int, int] = {}              # dict, not array: times go up to 10^9
    for vcpus, start, end in jobs:
        if start >= end:
            continue                        # zero-length job never runs
        delta[start] = delta.get(start, 0) + vcpus
        delta[end] = delta.get(end, 0) - vcpus
    peak = running = 0
    for t in sorted(delta):
        running += delta[t]                 # ends and starts at t are already netted
        peak = max(peak, running)
    return peak


def fits_quota(jobs: list[tuple[int, int, int]], quota: int) -> bool:
    return peak_usage(jobs) <= quota
```

**Complexity**
- Time: O(n log n): at most 2n change points, sorted once, then one linear pass.
- Space: O(n): the dict of change points.

(When times are small integers, for example minutes in one day, use a plain array of 1,441
slots instead of the dict and skip the sort: O(n + T).)

## 10. Tests
[`test_chip.py`](test_chip.py) has 6 cases: a normal overlap, empty and single jobs,
back-to-back jobs at the boundary, a zero-length job, the production nightly batch window
(including the fix: moving one job five minutes), and a large random check (200 random
schedules against an O(n²) reference, plus 100,000 overlapping jobs).

## 11. Interview Talk Track
"The tenant has a hard vCPU quota, and I need to know if their schedule ever breaks it. Load
only changes when a job starts or stops, so I record just those changes: plus vCPUs at the
start, minus at the end. That's a difference array. Then I walk the change points in time order
with a running sum, and the highest value is the peak. It's O(n log n) because of the sort, or
linear if time fits in a small array, like minutes in a day. The subtle bit is the boundary:
jobs hold resources until, but not including, their end, so a job ending at 60 and one starting
at 60 can share capacity. Adding the changes into one bucket per time handles that for free. I'd
run this as a CI check on the schedule, because Kubernetes ResourceQuota only rejects pods one at
a time when they arrive, too late to plan around."

## 12. Level Up
1. **"Tell me *when* it goes over, and which jobs are responsible."** Record every interval where
   the running sum is above quota (start of the excess to the next change point). For the
   blame list, collect the jobs active in each such interval; at most n, and usually few.
2. **"Several resources: vCPU, memory, GPU."** Keep one running sum per resource over the same
   sorted change points, and check each against its own quota. One sort serves all resources.
3. **"1,000 tenants, and schedules change all day."** Keep a sorted change-point structure per
   tenant and update it on each add or remove. To answer "max load in a time range" after every
   change, use a segment tree with range add and range max: O(log T) per update and query.

## 13. Related Chips
- **DC-PLAT-03 Minimum CI Runners**: the same peak-overlap question, with a heap.
- **DC-PLAT-10 Weighted Canary Router**: prefix sums, used for routing instead of load.
- **DC-SEC-05 Firewall Range Merger**: sort by start and sweep, on ranges instead of loads.
