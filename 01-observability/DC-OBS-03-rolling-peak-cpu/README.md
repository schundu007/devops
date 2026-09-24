Source: Handbook #83 Sliding Window Maximum — `apps/camora/src/data/capra/top100/83.json` (copied unchanged as `handbook.json`)

# DC-OBS-03 · Rolling Peak CPU

## 1. Header `DevOps layer`
| | |
|---|---|
| Chip ID | DC-OBS-03 |
| Difficulty | Hard |
| Pattern | Monotonic deque |
| Track | Observability & SRE (OBS) |
| Classic pattern | LeetCode 239 |
| Premium | No |
| Time box | 40 min |
| Source | Handbook #83 Sliding Window Maximum |

## 2. The Scenario `DevOps layer`
The `search-api` Deployment runs 12 replicas. Every 15 seconds the Horizontal Pod
Autoscaler (HPA) computes a desired replica count from CPU. At 14:02 traffic dips for 45
seconds, and the recommendation drops to 4, then jumps back to 12. If the HPA acted on that
dip, it would kill 8 pods and recreate them a minute later. Instead it scales down only to the
**highest** recommendation seen in the last 300 seconds: a rolling peak over the last 20 values.

**Mapping: DevOps term → handbook name**

| DevOps term | Handbook name |
|---|---|
| replica recommendation (or CPU sample) at each tick | `nums[i]` |
| stabilization window, counted in ticks (300 s ÷ 15 s = 20) | `k` |
| the value the autoscaler may act on at each tick | the output element for that window |
| recommendations that can never be the peak again | indices popped from the deque |

## 3. Why This Is DevOps `DevOps layer`
**Production reality:** Autoscalers should react to sustained load, not 1-second spikes or
dips. The Kubernetes HPA keeps its recent recommendations, and for scale-down it uses the
**highest** one inside `behavior.scaleDown.stabilizationWindowSeconds` (300 seconds by default).
That is a sliding-window maximum. The same "rolling peak" appears when you size capacity from
the worst minute of each hour, or smooth a noisy CPU graph without hiding its spikes.

**Where you see it:** the Kubernetes HPA (`behavior.scaleDown.stabilizationWindowSeconds`), KEDA
(it creates an HPA and passes the same `behavior` settings through), PromQL `max_over_time(cpu[5m])`.

**Reality check:** The HPA's window holds only about 20 recommendations, so it simply scans
them. The deque pays off when the window is large, for example a 1-hour peak over per-second
samples (3,600 values), where rescanning every tick costs 3,600 times more. The HPA's window is
also measured in time, not in a count of samples.

**What breaks if you get it wrong:** Use the latest value instead of the window peak and the
Deployment flaps: pods are terminated during a brief dip, then cold-start under the returning
load, and p99 latency spikes every few minutes.

## 4. Problem Statement `From handbook`
You are given an integer array `nums` and a window size `k`. A window of exactly `k` consecutive elements starts at the left edge and slides right one position at a time until it reaches the right edge.

Return an array containing the **maximum value inside each window**, in the order the windows occur. There are `nums.length - k + 1` windows.

## 5. Input / Output format and Constraints
**Input / Output format `(added)`:** `Solution().maxSlidingWindow(nums: List[int], k: int) -> List[int]`.

**Constraints `From handbook`**
- 1 ≤ nums.length ≤ 10⁵
- -10⁴ ≤ nums[i] ≤ 10⁴
- 1 ≤ k ≤ nums.length

## 6. Examples `From handbook`
**Example 1 — Negative numbers · Duplicates**
```
Input:  nums = [1, 3, -1, -3, 5, 3, 6, 7], k = 3
Output: [3, 3, 5, 5, 6, 7]
```
Windows: `[1,3,-1]`→3, `[3,-1,-3]`→3, `[-1,-3,5]`→5, `[-3,5,3]`→5, `[5,3,6]`→6, `[3,6,7]`→7.

**Example 2 — Single element**
```
Input:  nums = [1], k = 1
Output: [1]
```

## 7. Starter Code `(added)`
The handbook builds its starter from the problem's function signature and stores no starter file. See
[`starter.py`](starter.py): the same `maxSlidingWindow` signature, with a TODO body.

```bash
make try CHIP=01-observability/DC-OBS-03-rolling-peak-cpu
```

## 8. Hints `From handbook`
1. Recomputing each window's maximum costs O(n·k). Observe that an element is useless once a larger element appears to its right inside the window.
2. Maintain a deque of indices whose values are strictly decreasing from front to back.
3. For each new index, pop smaller values off the back, push the index, drop the front if it has left the window (`front ≤ i - k`), and once `i ≥ k - 1` record `nums[front]`.

## 9. Solution `From handbook`
#### Brute Force
Slide the window one step at a time and scan all k elements inside it to find the maximum.

- n - k + 1 windows
- Rescan each window fully
- Fine for small k

Time: O(n·k) · Space: O(1) extra

```python
class Solution:
    def maxSlidingWindow(self, nums, k):
        return [max(nums[i:i + k]) for i in range(len(nums) - k + 1)]
```

#### Monotonic Deque (Optimal)
Keep a deque of indices whose values are decreasing; the front is always the window's maximum, and indices that slide out are dropped from the front.

- Pop smaller values from the back
- Pop expired indices from the front
- Front holds the current maximum

Time: O(n) · Space: O(k)

```python
from collections import deque

class Solution:
    def maxSlidingWindow(self, nums, k):
        dq = deque()
        res = []
        for i, x in enumerate(nums):
            while dq and nums[dq[-1]] <= x:
                dq.pop()
            dq.append(i)
            if dq[0] <= i - k:
                dq.popleft()
            if i >= k - 1:
                res.append(nums[dq[0]])
        return res
```

`solution.py` is the handbook's optimal Python solution (Monotonic Deque), copied unchanged.
The handbook's Java, C++, Go, JavaScript and Bash versions are in `handbook.json` → `solutions[].code`.

## 10. Tests
**From handbook:** 30 cases in `handbook.json` → `tests`, run unchanged by `test_chip.py`.

**`(added)`** [`test_chip.py`](test_chip.py) wraps those cases in pytest. It also runs
**every** Python solution from the handbook against them (the Step 3 check), and adds two
DevOps-layer cases: the HPA scale-down scenario above (the 45-second dip never shows, and
scale-down starts at the first window with no 12), and a 20,000-sample random check against a brute force.

## 11. Interview Talk Track `DevOps layer`
"The HPA should scale down only if load has stayed low for the whole stabilization window, so
at each tick I need the maximum of the last k recommendations. Recomputing the max every tick
is O(n·k). Instead I keep a deque of indices whose values are decreasing. When a new value
arrives, anything smaller at the back can never be the peak again, because the new value is
both larger and newer, so I pop it. When the front index slides out of the window I drop it
too. The front is always the current peak. Each index is pushed and popped at most once, so
it's O(n) total and O(k) memory. The real HPA window holds only about 20 values and just scans
them, but the same idea matters for an hourly peak over per-second samples."

## 12. Level Up `DevOps layer`
1. **"Samples arrive at irregular times, and the window is 300 seconds, not k samples."**
   Store `(timestamp, value)` in the deque and expire from the front by time
   (`front.ts <= now - 300`) instead of by index. This is how the HPA's own window is defined.
2. **"You need this for 50,000 pods at once."** Keep one deque per series: memory is
   O(k) per series and every update is O(1) amortised. Shard series across workers by a
   hash of the series ID, because windows never cross series.
3. **"Scale-up should use the lowest value in its window, scale-down the highest."** Keep two
   deques: one decreasing (max) and one increasing (min). DC-OBS-06 uses exactly this pair
   to find stable latency windows.

## 13. Related Chips `DevOps layer`
- **DC-OBS-06 Longest Stable Latency Window**: two monotonic deques, max and min together.
- **DC-OBS-02 5-Minute Error Counter**: a time window that expires from the front.
- **DC-OBS-08 Live Latency Percentiles**: another streaming statistic, the median, kept with two heaps.
