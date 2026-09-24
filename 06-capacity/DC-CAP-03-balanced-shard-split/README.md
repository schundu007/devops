Source: New

# DC-CAP-03 · Balanced Shard Split

## 1. Header
| | |
|---|---|
| Chip ID | DC-CAP-03 |
| Difficulty | Hard |
| Pattern | Binary search on the answer / DP |
| Track | Capacity & Cost (CAP) |
| Classic pattern | LeetCode 410 |
| Premium | No |
| Time box | 40 min |
| Source | New |

## 2. The Scenario
The `users` table is range-partitioned by user ID into 8 key ranges. Their current write rates
are 120, 90, 1,400, 60, 300, 250, 80 and 700 writes/sec. You have 3 consumer workers. To keep
scans and ordering simple, each worker must own one **contiguous** block of key ranges. How do
you split the ranges so that the busiest worker carries the least load, and what is that load?

## 3. Why This Is DevOps
**Production reality:** Range-partitioned systems keep neighbouring keys together, so that range
scans hit one node. When you assign ranges to nodes, the busiest node sets the latency and
the size you need, so you want to minimise the maximum. The shape is the same as DC-CAP-02: "can
every worker stay under load L?" is a greedy pass, and it gets easier as L grows, so you binary
search L. Rebalancers answer this question whenever load shifts.

**Where you see it:** range-sharded databases that split and move key ranges between nodes
(CockroachDB ranges, HBase regions, TiKV regions, a similar idea), assigning partitions to
workers in stream processing, splitting a sorted backfill job across k workers.

**Reality check:** Real rebalancers move ranges one at a time, limit how much data moves
at once, and use load measured over time, not a single number. They also split hot ranges in
two, which this chip does not allow. Here the hot range (1,400) sets the floor.

**What breaks if you get it wrong:** Give each worker the same *number* of ranges instead of the
same *load*. One worker gets the 1,400 hot range plus neighbours, hits its limit and lags, while
the others sit idle. Consumer lag grows only on that worker's keys, which is hard to diagnose.

## 4. Problem Statement
`loads[i]` is the load of key range `i`, and the ranges are in key order. Assign the ranges to at
most `workers` workers so that each worker takes one **contiguous** block of ranges, and every range
is assigned.

Return the smallest possible load on the busiest worker. A worker's load is the sum of its ranges.

## 5. Input / Output format and Constraints
- Returns an integer.
- `1 <= len(loads) <= 10^5`.
- `0 <= loads[i] <= 10^6`.
- `1 <= workers <= 50`. Using fewer workers than allowed is fine.

## 6. Examples
**Example 1: five ranges, two workers**
```
loads = [7,2,5,10,8], workers = 2  ->  18
```
[7,2,5] = 14 and [10,8] = 18. Every other split has a busier worker.

**Example 2: one worker per range**
```
loads = [1,4,4], workers = 3  ->  4
```
The hottest single range sets the floor.

**Example 3: a single range (edge case)**
```
loads = [42], workers = 3  ->  42
```

## 7. Starter Code
See [`starter.py`](starter.py): the `min_busiest_worker_load(loads, workers)` signature, docstring
and type hints. The body is TODO.

```bash
make try CHIP=06-capacity/DC-CAP-03-balanced-shard-split
```

## 8. Hints
1. **Nudge:** Instead of searching for the split, guess the answer L. Can you check quickly
   whether every worker can stay at or below L?
2. **Pattern:** Binary search on the answer. The check is greedy: fill a worker until the next
   range would exceed L, then start the next worker.
3. **Near-solution:** `lo = max(loads)`, `hi = sum(loads)`. `fits(L)` counts workers greedily and fails if
   more than `workers` are needed. Find the smallest L with `fits(L)`.

## 9. Solution
**Approach**
1. The answer lies between the hottest range (no range can be split) and the total (one worker takes all).
2. `fits(L)`: walk the ranges, adding to the current worker; start a new worker when the next range
   would push it past L. It is feasible if you use at most `workers`.
3. Greedy is optimal for a fixed L: packing each worker as full as possible never uses more workers.
4. Binary search for the smallest feasible L.

**Brute force / DP:** `best(i, k)` = the best busiest-worker load for ranges `i..n-1` with `k`
workers, trying every end point for the first block. That is O(n² · k), which is fine for 100
ranges but not for 10^5. The tests use it as the independent reference.

**Optimal code:** [`solution.py`](solution.py)

```python
def min_busiest_worker_load(loads, workers):
    def fits(limit):
        runs, current = 1, 0
        for load in loads:
            if current + load > limit:
                runs += 1
                current = 0
                if runs > workers:
                    return False
            current += load
        return True

    lo, hi = max(loads), sum(loads)
    while lo < hi:
        mid = (lo + hi) // 2
        if fits(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo
```

**Complexity**
- Time: O(n · log(sum − max)). There are about 37 binary-search steps for sums up to 10^11, each
  one greedy O(n) pass.
- Space: O(1) extra.

## 10. Tests
[`test_chip.py`](test_chip.py) has 8 cases: five ranges over two workers, a single range, one
worker, one worker per range, zero-load ranges, the hot-tenant table (checked against DP, and at
least 1,400), 200 random inputs checked against the O(n²k) DP, and 100,000 ranges over 50 workers
checked for tightness (L fits and L − 1 does not).

## 11. Interview Talk Track
"We split ordered key ranges across k workers and want the busiest worker as light as possible.
Searching splits directly is a DP: n² times k. The faster trick is to guess the answer. If every
worker can stay under L, then it can stay under anything bigger, so feasibility is monotonic and I
binary search L between the hottest range and the total. The check is greedy: fill a worker until
the next range would overflow, then start a new one, and fail if I need more than k workers.
That's O(n log sum). The hottest range is a hard floor unless you can split it, which is exactly
why real systems like CockroachDB split hot ranges before they rebalance."

## 12. Level Up
1. **"Return the actual assignment, not just the load."** Run the greedy `fits(L)` once more at the
   final L and record where each worker's block starts. Those split points are the assignment to
   apply.
2. **"Hot ranges can be split in two."** Now the floor disappears. With fully divisible load the
   answer tends toward `ceil(sum / k)`. In practice, split any range above `sum / k`, then run
   the same search again. Rebalancers use a similar split-then-place loop.
3. **"Moving a range is expensive: minimise moves while staying under L."** This becomes a
   different optimisation: keep today's boundaries where possible and shift only the ones next
   to overloaded workers. Many production rebalancers use greedy moves, one range at a time,
   rather than a global re-split, because each move has a cost.

## 13. Related Chips
- **DC-CAP-02 Backup Window Bandwidth**: the same greedy feasibility check, over nights.
- **DC-CAP-01 Backlog Drain Rate**: binary search on a rate.
- **DC-PLAT-09 Runner Pool Allocation**: assigning work to workers without the contiguity rule.
