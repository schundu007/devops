Source: New

# DC-OBS-06 · Longest Stable Latency Window

## 1. Header
| | |
|---|---|
| Chip ID | DC-OBS-06 |
| Difficulty | Medium |
| Pattern | Sliding window + two monotonic deques |
| Track | Observability & SRE (OBS) |
| Classic pattern | LeetCode 1438 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
You are writing the post-incident review for Tuesday's `checkout-api` slowdown. The graph shows
p99 latency, one sample per minute. Before the database connection pool filled up, latency sat
calmly between 180 and 195 ms. The review template asks: "What was the longest stable period
before the incident, where p99 stayed inside a 15 ms band?" You need that stretch to set the
baseline, and its end marks when things started to drift.

## 3. Why This Is DevOps
**Production reality:** "Stable" means the spread (max minus min) stayed inside a band, not
that the average looked fine. SRE teams look for the longest stable stretch to pick a baseline
for an SLO, to check that a canary really behaved like the old version, and to find the moment
a system started to drift before an incident. You need the max and the min of a moving window
at the same time, and the window grows and shrinks as you scan.

**Where you see it:** PromQL `max_over_time()` and `min_over_time()` over the same range, SLO
reviews in Grafana, canary analysis in Argo Rollouts and Kayenta (both compare metrics against
a baseline), and anomaly detection that watches for sustained drift.

**Reality check:** Tools usually compute max and min over a *fixed* range at each step. This
chip finds the *longest* window that fits the band, which is what you do by hand in a review.
Real series also have gaps and noisy spikes; teams often smooth first or use a percentile band
instead of the raw max and min.

**What breaks if you get it wrong:** Pick the baseline from a window that was not actually
stable and your SLO threshold or canary comparison is too loose. The next regression passes
the check, and you find out from customers.

## 4. Problem Statement
You get a list of latency samples in time order and a band width `limit`.

Find the longest run of **consecutive** samples in which the largest sample minus the
smallest sample is at most `limit`. Return its length. Return 0 for an empty list.

## 5. Input / Output format and Constraints
- `latency_ms: list[int]`, `0 <= len <= 10^5`, each value `0 <= v <= 10^9`.
- `limit: int`, `0 <= limit <= 10^9`.
- Returns `int`.
- A window with `max - min == limit` counts as stable.

## 6. Examples
**Example 1**
```
latency_ms = [120, 125, 118, 300, 310, 305, 122], limit = 10  -> 3
```
`[120, 125, 118]` spreads 7 ms and `[300, 310, 305]` spreads 10 ms. Any longer run mixes both levels.

**Example 2: band edge (edge case)**
```
latency_ms = [100, 110, 100, 111], limit = 10  -> 3
```
The first three spread exactly 10, which still counts. Adding 111 makes the spread 11.

**Example 3: empty and zero-width band (edge case)**
```
latency_ms = [], limit = 5                   -> 0
latency_ms = [40, 40, 41, 41, 41, 40], limit = 0 -> 3
```

## 7. Starter Code
See [`starter.py`](starter.py): `longest_stable_window(latency_ms, limit)` with a docstring,
type hints and a TODO body.

```bash
make try CHIP=01-observability/DC-OBS-06-stable-latency-window
```

## 8. Hints
1. **Nudge:** If a window is stable, every smaller window inside it is stable too. Can you move
   a left and a right edge forward without ever moving back?
2. **Pattern:** A sliding window that needs its max and its min at every step: two monotonic
   deques, one decreasing (max at the front) and one increasing (min at the front).
3. **Near-solution:** For each new right edge, push it onto both deques after popping worse
   values from their backs. While `max - min > limit`, move `left` forward and pop any deque
   front whose index is now `< left`. Record `right - left + 1`.

## 9. Solution
**Approach**
1. Scan with a right edge. Keep `left` as the start of the current window.
2. Max deque: pop smaller values from the back, then push the new index. Its front is the window max.
3. Min deque: pop larger values from the back, then push. Its front is the window min.
4. While `max - min > limit`, move `left` forward and drop deque fronts that fell out.
5. The window `[left, right]` is now the longest stable window ending at `right`. Keep the best length.

**Brute force:** Try every start, extend while the spread fits: O(n²). For a week of per-second
data (604,800 samples) that is about 10¹¹ steps.

**Optimal code:** [`solution.py`](solution.py)

```python
from collections import deque


def longest_stable_window(latency_ms: list[int], limit: int) -> int:
    maxq: deque[int] = deque()  # decreasing values: front = max
    minq: deque[int] = deque()  # increasing values: front = min
    left = best = 0
    for right, x in enumerate(latency_ms):
        while maxq and latency_ms[maxq[-1]] < x:
            maxq.pop()
        maxq.append(right)
        while minq and latency_ms[minq[-1]] > x:
            minq.pop()
        minq.append(right)
        while latency_ms[maxq[0]] - latency_ms[minq[0]] > limit:
            left += 1
            if maxq[0] < left:
                maxq.popleft()
            if minq[0] < left:
                minq.popleft()
        best = max(best, right - left + 1)
    return best
```

**Complexity**
- Time: O(n), because each index is pushed and popped at most once per deque, and `left` only moves forward.
- Space: O(n) in the worst case, for example a steadily rising series fills the min deque.

## 10. Tests
[`test_chip.py`](test_chip.py) has 6 cases: a normal series, empty and single-sample inputs,
a zero-width band, the inclusive band edge, a production-style calm period before an incident
(45 minutes inside 180–195 ms), and 30 random series checked against a brute force, plus a
100,000-sample sanity check.

## 11. Interview Talk Track
"For the incident review I want the longest stretch where p99 stayed inside a band, which
means max minus min at most the limit. Stability shrinks nicely: any piece of a stable window
is stable, so a sliding window works. Left and right only move forward. The hard part is
knowing the max and the min of the current window cheaply. I keep two monotonic deques of
indices: one decreasing, whose front is the max, and one increasing, whose front is the min.
When the spread breaks the limit, I move left forward and drop fronts that fell out. Every
index enters and leaves each deque once, so it's O(n). The same pair of deques is what you'd
use to track both scale-up and scale-down windows in an autoscaler."

## 12. Level Up
1. **"The data is streaming, and I want the current stable streak live."** The same loop works
   online: keep `left`, both deques and `best` as state, and process each sample as it arrives.
   Memory is bounded by the current window, not the history.
2. **"One noisy spike ruins a 6-hour stable window."** Allow up to k outliers: keep a count of
   samples outside a robust band (for example the median ± limit), which turns this into the
   "at most k failures" window of DC-OBS-16. Or smooth first with a short moving median.
3. **"Do this for 20,000 services every minute."** Each service is independent, so shard by
   service. Per service, the deques are small in practice because latency rarely rises or falls
   monotonically for long. Persist only `left`, the deques and `best` between runs.

## 13. Related Chips
- **DC-OBS-03 Rolling Peak CPU**: one monotonic deque, fixed window.
- **DC-OBS-16 Error Budget Window**: the longest window with at most k bad samples.
- Handbook #83 Sliding Window Maximum: the single-deque version.
