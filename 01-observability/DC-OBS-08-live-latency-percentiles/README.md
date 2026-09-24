Source: Handbook #39 Find Median from Data Stream — `apps/camora/src/data/capra/top100/39.json` (copied unchanged as `handbook.json`)

# DC-OBS-08 · Live Latency Percentiles ★

## 1. Header `DevOps layer`
| | |
|---|---|
| Chip ID | DC-OBS-08 ★ Start here |
| Difficulty | Hard |
| Pattern | Two heaps |
| Track | Observability & SRE (OBS) |
| Classic pattern | LeetCode 295 |
| Premium | No |
| Time box | 40 min |
| Source | Handbook #39 Find Median from Data Stream |

## 2. The Scenario `DevOps layer`
You are building the live latency panel for a load test of `orders-api` running against
`10.40.0.0/16`. Every finished request reports its latency in milliseconds, and the panel
must show the current p50 after each request, not once a minute. Most requests take 30–50 ms,
but about 5% hit a cold cache and take 800–2,000 ms. Sorting every sample on each refresh
is already too slow after the first few thousand requests.

**Mapping: DevOps term → handbook name**

| DevOps term | Handbook name |
|---|---|
| one request's latency in ms | `num` passed to `addNum` |
| the live latency tracker | `MedianFinder` |
| current p50 latency | `findMedian()` |
| the faster half of requests | the max-heap `lo` |
| the slower half of requests | the min-heap `hi` |

## 3. Why This Is DevOps `DevOps layer`
**Production reality:** Latency SLOs are written in percentiles ("p99 under 300 ms"), because
averages hide the slow tail. To keep a running p50, split the samples into a low half and a
high half: a max-heap holds the faster half and a min-heap the slower half, so the median is
always at the top of one or both heaps. Changing the split ratio, for example 90% low and 10%
high, gives p90 at the top of the low heap in the same way.

**Where you see it:** Prometheus histograms and `histogram_quantile()`, Prometheus summaries
(quantiles computed in the client), Elasticsearch's `percentiles` aggregation (t-digest),
Datadog's distribution metrics (DDSketch), and load-test tools that print live p50/p99.

**Reality check:** Production systems do not keep every sample. Prometheus histograms count
samples in fixed buckets and estimate the percentile by interpolating inside a bucket. t-digest
and DDSketch are sketches that estimate percentiles in small, fixed memory, and they can be
merged across servers. The two heaps in this chip give the **exact** answer, and they keep all n samples.

**What breaks if you get it wrong:** Report the mean instead of a percentile and a 5% slow tail
disappears into a comfortable average. Report a percentile from badly chosen histogram buckets
and p99 can be off by hundreds of ms, so the SLO looks met while users wait.

## 4. Problem Statement `From handbook`
The median of a sorted list of numbers is its middle value; when the list has an even length, it is the average of the two middle values. Implement the `MedianFinder` class, which receives numbers one at a time:

- `MedianFinder()` creates an empty object.
- `addNum(num)` adds the integer `num` to the collection.
- `findMedian()` returns the median of all numbers added so far as a floating-point value. Answers within `10⁻⁵` of the true median are accepted.

Input is given as parallel lists `ops` and `vals`. The output lists each call's return value, with `null` for the constructor and for `addNum`. `findMedian` is only called after at least one number has been added.

## 5. Input / Output format and Constraints
**Input / Output format `(added)`:** a design problem. `MedianFinder()`;
`addNum(num: int) -> None`; `findMedian() -> float`. Answers are compared as floats within `10⁻⁵`.

**Constraints `From handbook`**
- -10⁵ ≤ num ≤ 10⁵
- There will be at least one element in the data structure before calling findMedian.
- At most 5 * 10⁴ calls will be made to addNum and findMedian.

## 6. Examples
**From handbook**

**Example 1 — 5 operations**
```
Input:  ops = ["MedianFinder", "addNum", "addNum", "findMedian", "addNum", "findMedian"], vals = [[], [1], [2], [], [3], []]
Output: [null, null, null, 1.5, null, 2.0]
```
After adding 1 and 2 the median is (1 + 2) / 2 = 1.5; after adding 3 it is the middle value 2.

**Example 2 — Even count `(added)`**
```
Input:  ops = ["MedianFinder", "addNum", "addNum", "addNum", "addNum", "findMedian"], vals = [[], [120], [80], [300], [95], []]
Output: [null, null, null, null, null, 107.5]
```
Sorted, the four samples are 80, 95, 120, 300. With an even count the median is the average of
the two middle values: (95 + 120) / 2 = 107.5. The 300 ms outlier does not move it.

## 7. Starter Code `(added)`
The handbook builds its starter from the problem's function signature and stores no starter file. See
[`starter.py`](starter.py): the same `MedianFinder` signatures, with TODO bodies.

```bash
make try CHIP=01-observability/DC-OBS-08-live-latency-percentiles
```

## 8. Hints `From handbook`
1. You only ever need the one or two values in the middle, never the fully sorted order.
2. Keep two heaps: a max-heap for the smaller half of the numbers and a min-heap for the larger half.
3. On each add, push into one heap, move its top to the other so every value in the lower half ≤ every value in the upper half, then rebalance so the sizes differ by at most one. The median is the top of the larger heap, or the average of both tops.

## 9. Solution `From handbook`
#### Sort and Find Middle
Store all numbers in an array. Sort the array each time findMedian is called and return the middle element(s).

- Sort on every findMedian call
- Simple but inefficient for frequent queries
- O(1) addNum but costly findMedian

Time: O(n log n) per findMedian · Space: O(n)

```python
class MedianFinder:
    def __init__(self):
        self.data = []

    def addNum(self, num):
        self.data.append(num)

    def findMedian(self):
        self.data.sort()
        n = len(self.data)
        if n % 2 == 1:
            return self.data[n // 2]
        return (self.data[n // 2 - 1] + self.data[n // 2]) / 2
```

#### Two Heaps (Optimal)
Maintain a max-heap for the lower half and a min-heap for the upper half. Balance sizes so median is at the tops.

- Max-heap holds smaller half, min-heap holds larger half
- Balance heaps so sizes differ by at most 1
- Median is always at heap tops
- Python uses negation to simulate max-heap

Time: O(log n) addNum, O(1) findMedian · Space: O(n)

```python
import heapq

class MedianFinder:
    def __init__(self):
        self.lo = []  # max-heap (negate values)
        self.hi = []  # min-heap

    def addNum(self, num):
        heapq.heappush(self.lo, -num)
        heapq.heappush(self.hi, -heapq.heappop(self.lo))
        if len(self.hi) > len(self.lo):
            heapq.heappush(self.lo, -heapq.heappop(self.hi))

    def findMedian(self):
        if len(self.lo) > len(self.hi):
            return -self.lo[0]
        return (-self.lo[0] + self.hi[0]) / 2
```

**Follow-up (from handbook):** If every number in the stream lies in [0, 100], how would you optimize it? What if 99% of the numbers lie in [0, 100]?

`solution.py` is the handbook's optimal Python solution (Two Heaps), copied unchanged. The
handbook's Java, C++, Go and JavaScript versions are in `handbook.json` → `solutions[].code`.

## 10. Tests
**From handbook:** 29 cases in `handbook.json` → `tests`, run unchanged by `test_chip.py`.

**`(added)`** [`test_chip.py`](test_chip.py) wraps those cases in pytest, comparing floats
within `10⁻⁵` as the handbook's `cmp: "float"` specifies. It also runs **every** Python solution
from the handbook against them (the Step 3 check), checks the added Example 2, and adds a
DevOps-layer case: a 3,000-request stream with a 5% slow tail, checked against
`statistics.median` every 100 requests.

## 11. Interview Talk Track `DevOps layer`
"The load-test panel needs the live p50 after every request. Sorting on each read is
O(n log n), which is too slow. I only ever need the middle, so I keep two heaps: a max-heap for the
faster half and a min-heap for the slower half. Each new sample goes into the low heap, its
largest value moves to the high heap, and then I rebalance so the low heap has the same size or
one more. The median is the low heap's top, or the average of the two tops. That's O(log n)
per sample and O(1) per read. For p99 I'd split 99 to 1 instead of 50 to 50. In production,
though, I wouldn't keep every sample: Prometheus uses histogram buckets, and t-digest or
DDSketch give an approximate percentile in fixed memory that can be merged across servers."

## 12. Level Up `DevOps layer`
1. **"Give me p99, not p50."** Keep the low heap at `ceil(0.99 · n)` samples and the high heap
   at the rest. After each insert, move one top across if the sizes drift. p99 is the low
   heap's top. The high heap stays small (1% of n), but the low heap still holds 99% of samples.
2. **"Only the last 5 minutes count."** Samples must now leave as well as arrive. Heaps can't
   remove from the middle cheaply, so use lazy deletion: mark expired samples, adjust the
   size counts, and pop marked items only when they reach a top (see DC-OBS-12). Or use a
   sorted container with O(log n) removal.
3. **"200 servers each see part of the traffic."** You can't combine 200 medians into the true
   median. Each server keeps a mergeable sketch (a histogram with fixed buckets, a t-digest or a
   DDSketch). A central job merges the sketches and reads the percentile from the merged one.
   The handbook's follow-up hints at the bucket idea for values in a known range.

## 13. Related Chips `DevOps layer`
- **DC-OBS-12 Late & Corrected Samples**: heaps with lazy deletion when values change.
- **DC-OBS-03 Rolling Peak CPU**: another streaming statistic, over a sliding window.
- **DC-OBS-14 Multi-Node Log Timeline Merge**: a heap-based streaming merge.
