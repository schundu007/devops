Source: Handbook #85 Koko Eating Bananas — `apps/camora/src/data/capra/top100/85.json` (copied unchanged as `handbook.json`)

# DC-CAP-01 · Backlog Drain Rate ★

## 1. Header `DevOps layer`
| | |
|---|---|
| Chip ID | DC-CAP-01 |
| Difficulty | Medium |
| Start here | ★ |
| Pattern | Binary search on the answer |
| Track | Capacity & Cost (CAP) |
| Classic pattern | LeetCode 875 |
| Premium | No |
| Time box | 25 min |
| Source | Handbook #85 Koko Eating Bananas |

## 2. The Scenario `DevOps layer`
The `orders-consumer` group was down for 40 minutes. Its topic has 6 partitions, and each
one now holds a backlog (in thousands of messages): 1,200, 300, 4,800, 950, 2,100 and 60.
Downstream billing needs every message processed within 8 hours. A consumer works on one
partition at a time and processes up to `rate` thousand messages per hour. If a partition
finishes mid-hour, that consumer sits idle until the hour ends, because rebalancing is
hourly. What is the smallest rate you must provision?

**Mapping: DevOps term → handbook name**

| DevOps term | Handbook name |
|---|---|
| partition backlog | `piles[i]` |
| drain deadline in hours | `h` |
| consumer processing rate per hour | speed `k` |
| hours to drain one partition at rate k | `ceil(piles[i] / k)` |
| minimum rate to provision | the returned `k` |

## 3. Why This Is DevOps `DevOps layer`
**Production reality:** After an outage, queues hold a backlog. The question is not "how fast
are we?" but "what is the smallest capacity that drains everything before the deadline?" As the
rate grows, the hours needed only go down, so a yes/no check ("does rate r meet the deadline?")
flips from no to yes exactly once. Binary search that flip point instead of trying every rate.
The same shape sizes consumer fleets, worker counts and throughput limits.

**Where you see it:** Kafka consumer-group sizing from consumer lag, Amazon SQS worker sizing
from `ApproximateNumberOfMessagesVisible`, KEDA scalers that scale on queue length, batch
re-processing after an incident.

**Reality check:** In Kafka, one partition is read by only one consumer in a group at a time,
so parallelism is capped by the partition count. Real consumers also do not idle for the rest
of the hour after finishing a partition. The "ceil per partition" rule is a simple stand-in for
per-partition overhead. The chip keeps the handbook's exact rounding.

**What breaks if you get it wrong:** Guess the rate from the total backlog divided by the
hours (9,410 ÷ 8 ≈ 1,177) and you miss the SLA: the 4,800 partition alone needs 5 hours at
that rate. Over-provision instead and you pay for idle consumers all night.

## 4. Problem Statement `From handbook`
There are `n` piles of bananas, where pile `i` holds `piles[i]` bananas, and the guards return in `h` hours. Koko picks an eating speed of `k` bananas per hour. Each hour she chooses one pile and eats `k` bananas from it; if that pile has fewer than `k` left, she finishes it and waits out the rest of that hour without starting another pile.

Return the **minimum integer speed `k`** that lets her finish every pile within `h` hours. It is guaranteed that `h ≥ piles.length`, so an answer always exists.

## 5. Input / Output format and Constraints
**Input / Output format `(added)`:** `Solution().minEatingSpeed(piles: List[int], h: int) -> int`.

**Constraints `From handbook`**
- 1 ≤ piles.length ≤ 10⁴
- piles.length ≤ h ≤ 10⁹
- 1 ≤ piles[i] ≤ 10⁹

## 6. Examples `From handbook`
**Example 1 — Sorted input**
```
Input:  piles = [3, 6, 7, 11], h = 8
Output: 4
```
At speed `4` the piles take `1 + 2 + 2 + 3 = 8` hours; speed `3` would need `10`.

**Example 2 — Typical input · 5 elements**
```
Input:  piles = [30, 11, 23, 4, 20], h = 5
Output: 30
```
With one hour per pile she must clear the largest pile in an hour.

**Example 3 — Typical input · 5 elements**
```
Input:  piles = [30, 11, 23, 4, 20], h = 6
Output: 23
```

## 7. Starter Code `(added)`
The handbook builds its starter from the problem's function signature and stores no starter file. See
[`starter.py`](starter.py): the same `minEatingSpeed` signature, with a TODO body.

```bash
make try CHIP=06-capacity/DC-CAP-01-backlog-drain-rate
```

## 8. Hints `From handbook`
1. The total hours needed only goes down (or stays the same) as the speed increases — the feasibility check is monotonic in `k`.
2. Binary search on the answer: the speed lies somewhere between `1` and `max(piles)`.
3. For a candidate `k`, hours needed is `sum(ceil(p / k))`. If that is `≤ h`, try smaller speeds (`hi = k`); otherwise `lo = k + 1`.

## 9. Solution `From handbook`
#### Linear Scan from Lower Bound
No speed below ceil(sum / h) can finish in time, so start there and try each speed upward until the total hours (sum of ceil(pile / speed)) fit within h.

- Hours at speed k = Σ ceil(p / k)
- ceil(sum / h) is a hard lower bound
- Still linear in the speed range

Time: O(n · max(piles)) · Space: O(1)

```python
class Solution:
    def minEatingSpeed(self, piles, h):
        speed = max(1, (sum(piles) + h - 1) // h)
        while True:
            hours = sum((p + speed - 1) // speed for p in piles)
            if hours <= h:
                return speed
            speed += 1
```

#### Binary Search on Speed (Optimal)
Feasibility is monotonic in speed, so binary search the smallest speed in [1, max(piles)] whose total hours fit within h.

- Faster speed never needs more hours
- Search space is 1..max(piles)
- Keep the lowest feasible speed

Time: O(n · log max(piles)) · Space: O(1)

```python
class Solution:
    def minEatingSpeed(self, piles, h):
        lo, hi = 1, max(piles)
        while lo < hi:
            mid = (lo + hi) // 2
            hours = sum((p + mid - 1) // mid for p in piles)
            if hours <= h:
                hi = mid
            else:
                lo = mid + 1
        return lo
```

`solution.py` is the handbook's optimal Python solution (Binary Search on Speed), copied unchanged.
The handbook's Java, C++, Go, JavaScript and Bash versions are in `handbook.json` → `solutions[].code`.

## 10. Tests
**From handbook:** 29 cases in `handbook.json` → `tests`, run unchanged by `test_chip.py`.

**`(added)`** [`test_chip.py`](test_chip.py) wraps those cases in pytest. It also runs
**every** Python solution from the handbook against them (the Step 3 check), and adds two
DevOps-layer cases: the `orders` topic scenario (the answer is 2,100, and 2,099 misses the
deadline), and 200 random inputs, each checked for "meets the deadline, and rate − 1 does not".

## 11. Interview Talk Track `DevOps layer`
"After an outage I have a backlog per partition and a deadline, and I need the minimum
processing rate. The key observation is monotonicity: if rate r drains everything in time, any
faster rate does too. So I binary search the rate between 1 and the largest backlog. For each
candidate I compute the hours as the sum of ceil(backlog over rate) and compare to the
deadline. That's O(n log max) instead of trying every rate. The trap is dividing the total
backlog by the hours: that ignores that one partition is processed by one consumer at a time,
so the biggest partition sets the floor. In Kafka that cap is real, because partitions
limit a group's parallelism."

## 12. Level Up `DevOps layer`
1. **"Messages keep arriving at 50k/hour per partition while you drain."** The rate must
   exceed the arrival rate. Drain time for a partition becomes `backlog / (rate − arrival)`.
   The check is still monotonic in the rate, so the same binary search works with the new check.
2. **"You can add consumers, but at most one per partition."** Now there are two things to
   choose: consumers and per-consumer rate. Fix the consumer count at the partition count
   (the most useful), then binary search the rate. Alternatively, binary search the number of
   consumers with a fixed rate.
3. **"10,000 partitions, and the check has to run every minute for autoscaling."** Each check
   is O(partitions), and there are about 30 binary-search steps. That's 300,000 operations per
   minute, which is cheap. To go further, sort the backlogs once and group equal ceilings.

## 13. Related Chips `DevOps layer`
- **DC-CAP-02 Backup Window Bandwidth**: the same binary search, but files are copied in order.
- **DC-CAP-03 Balanced Shard Split**: binary search on the busiest worker's load.
- **DC-OBS-02 5-Minute Error Counter**: how lag is measured before you size for it.
