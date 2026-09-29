"""Capra Playground export for DC-OBS-06 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "longest_stable_window", "params": ["latency_ms", "limit"], "types": {}, "ret": "value", "cmp": "exact"}

EXAMPLES = [
    {"args": {"latency_ms": [120, 125, 118, 300, 310, 305, 122], "limit": 10},
     "explanation": "[120, 125, 118] spreads 7 ms and [300, 310, 305] spreads 10 ms. Any longer run mixes both levels.",
     "why": {"t": "Two levels", "d": "Two calm stretches at different latency levels."}},
    {"args": {"latency_ms": [100, 110, 100, 111], "limit": 10},
     "explanation": "The first three spread exactly 10, which still counts. Adding 111 makes the spread 11.",
     "why": {"t": "Band edge", "d": "max - min equal to the limit is inside the band."}},
    {"args": {"latency_ms": [40, 40, 41, 41, 41, 40], "limit": 0},
     "explanation": "With a zero-width band only equal values fit: the three 41s.",
     "why": {"t": "Zero-width band", "d": "limit = 0 means every sample in the window must be equal."}},
]

_rng = random.Random(1438)
_large = [_rng.randint(80, 140) for _ in range(3000)]

TESTS = [
    {"args": {"latency_ms": [], "limit": 5},
     "why": {"t": "Empty", "d": "No samples: the longest window is 0."}},
    {"args": {"latency_ms": [250], "limit": 0},
     "why": {"t": "Single sample", "d": "One sample is always a stable window of length 1."}},
    {"args": {"latency_ms": [5, 5, 5, 5], "limit": 0},
     "why": {"t": "All equal", "d": "Every sample matches: the whole series."}},
    {"args": {"latency_ms": [1, 2, 3, 4, 5, 6, 7, 8], "limit": 3},
     "why": {"t": "Rising", "d": "A steady climb: any 4 consecutive samples fit a band of 3."}},
    {"args": {"latency_ms": [9, 1, 9, 1, 9], "limit": 7},
     "why": {"t": "Alternating spikes", "d": "Neighbors differ by 8, so no window longer than 1 fits."}},
    {"args": {"latency_ms": [50, 1000, 1000, 1000], "limit": 10**6},
     "why": {"t": "Huge limit", "d": "A limit wider than any spread accepts the whole series."}},
    {"args": {"latency_ms": [180, 182, 179, 181, 180, 900, 1200, 181, 183, 180, 182, 179, 181], "limit": 5},
     "why": {"t": "Pre-incident calm", "d": "A deploy spike splits two calm stretches; the later one is longer."}},
    {"args": {"latency_ms": _large, "limit": 25},
     "why": {"t": "Large input", "d": "3,000 random latency samples."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Sliding window + two monotonic deques (Optimal)",
     "description": "Grow the window to the right. A decreasing deque keeps the window max at its front and an increasing one keeps the min. While max - min exceeds the limit, move the left edge and drop expired indices.",
     "time": "O(n)", "space": "O(n)",
     "keyPoints": ["Max deque decreasing, min deque increasing", "Shrink from the left only while the band is broken", "Each index enters and leaves each deque at most once"]},
    {"name": "Try every start", "slow": True,
     "description": "For each start, extend right while tracking max and min, and stop when the spread breaks the limit.",
     "time": "O(n²)", "space": "O(1)",
     "keyPoints": ["Easy to get right", "Quadratic on a week of per-second samples"],
     "code": '''from __future__ import annotations


def longest_stable_window(latency_ms: list[int], limit: int) -> int:
    best = 0
    for i in range(len(latency_ms)):
        hi = lo = latency_ms[i]
        for j in range(i, len(latency_ms)):
            hi = max(hi, latency_ms[j])
            lo = min(lo, latency_ms[j])
            if hi - lo > limit:
                break
            best = max(best, j - i + 1)
    return best
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Try every start", "idea": "Extend from each start while tracking max and min.",
     "time": "O(n²)", "space": "O(1)", "use": "Short series; a quick baseline."},
    {"name": "Two monotonic deques", "idea": "Window max and min in O(1) each, with a left edge that only moves forward.",
     "time": "O(n)", "space": "O(n)", "use": "Long per-second series in SLO reviews."},
]

VARIANT_TITLE = "Longest stable window"
VARIANT_APPROACH = "Sliding window + two monotonic deques · O(n) · O(n)"

_v = random.Random(239)
_V_SERIES = [200]
for _ in range(2999):
    _V_SERIES.append(max(0, _V_SERIES[-1] + _v.randint(-12, 12)))

VARIANTS = [
    {
        "key": "rolling-peak",
        "title": "Rolling peak latency",
        "approach": "Monotonic decreasing deque · O(n) · O(k)",
        "spec": {"kind": "fn", "fn": "rolling_peak", "params": ["latency_ms", "k"]},
        "statement": (
            "A dashboard plots the **peak** latency over the last `k` samples, updated on every sample once `k` "
            "samples have arrived.\n\n"
            "Given `latency_ms` in time order and a window size `k`, return a list with the maximum of every "
            "window of `k` consecutive samples, from left to right. Return an empty list if there are fewer than `k` samples."
        ),
        "examples": [
            {"args": {"latency_ms": [120, 310, 140, 90, 95, 400, 130], "k": 3},
             "explanation": "Windows: [120,310,140] 310, [310,140,90] 310, [140,90,95] 140, [90,95,400] 400, [95,400,130] 400.",
             "why": {"t": "Classic", "d": "A spike dominates every window it sits in."}},
        ],
        "constraints": [
            "0 ≤ latency_ms.length ≤ 10⁵",
            "0 ≤ latency_ms[i] ≤ 10⁹",
            "1 ≤ k ≤ 10⁵",
        ],
        "hints": [
            "A sample that is smaller than a newer sample can never be the peak again: drop it.",
            "Keep indices in a deque with decreasing values. The front is the peak; pop it once it leaves the window.",
        ],
        "tests": [
            {"args": {"latency_ms": [], "k": 3}, "why": {"t": "Empty", "d": "No samples, no windows."}},
            {"args": {"latency_ms": [50, 60], "k": 3}, "why": {"t": "Shorter than k", "d": "Fewer samples than the window: empty."}},
            {"args": {"latency_ms": [7, 3, 9], "k": 1}, "why": {"t": "k = 1", "d": "Each sample is its own peak."}},
            {"args": {"latency_ms": [5, 5, 5, 5], "k": 2}, "why": {"t": "Ties", "d": "Equal values must not be dropped too early."}},
            {"args": {"latency_ms": [9, 8, 7, 6, 5], "k": 2}, "why": {"t": "Falling", "d": "The peak expires from the front every step."}},
            {"args": {"latency_ms": [1, 2, 3, 4, 5], "k": 5}, "why": {"t": "k = n", "d": "One window covers the whole series."}},
            {"args": {"latency_ms": _V_SERIES, "k": 60}, "why": {"t": "Large input", "d": "3,000 random-walk samples with a 60-sample window."}},
        ],
        "solutions": [
            {"name": "Monotonic deque (Optimal)",
             "description": "Push each index after popping smaller values from the back. Drop the front when it falls out of the window; the front is the peak.",
             "time": "O(n)", "space": "O(k)",
             "keyPoints": ["Values in the deque are decreasing", "Each index is pushed and popped once", "Front index expires after k steps"],
             "code": '''from collections import deque


def rolling_peak(latency_ms, k):
    dq = deque()
    out = []
    for i, v in enumerate(latency_ms):
        while dq and latency_ms[dq[-1]] <= v:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - k:
            dq.popleft()
        if i >= k - 1:
            out.append(latency_ms[dq[0]])
    return out
'''},
            {"name": "Max of every window", "slow": True,
             "description": "Slice each window and take its max.",
             "time": "O(n · k)", "space": "O(k)",
             "keyPoints": ["Obviously correct", "Re-reads k samples per step"],
             "code": '''def rolling_peak(latency_ms, k):
    return [max(latency_ms[i:i + k]) for i in range(len(latency_ms) - k + 1)]
'''},
        ],
        "starter": '''def rolling_peak(latency_ms: list[int], k: int) -> list[int]:
    """Maximum of every window of k consecutive samples."""
    raise NotImplementedError
''',
    },
    {
        "key": "fastest-ramp",
        "title": "Fastest latency ramp",
        "approach": "Shrinking window + two monotonic deques · O(n) · O(n)",
        "spec": {"kind": "fn", "fn": "fastest_ramp", "params": ["latency_ms", "swing"]},
        "statement": (
            "During a postmortem you want to know how quickly latency can swing. Given samples `latency_ms` in "
            "time order and a threshold `swing`, find the **shortest** run of consecutive samples whose "
            "`max − min` is at least `swing`.\n\n"
            "Return its length, or `0` if no run swings that much. A short run means a sharp jump or drop "
            "that an alert with a long evaluation window would smooth over."
        ),
        "examples": [
            {"args": {"latency_ms": [100, 104, 180, 176, 110, 300], "swing": 150},
             "explanation": "[110, 300] swings 190 in two samples. No single sample swings at all.",
             "why": {"t": "Sharp jump", "d": "The shortest run is two neighbors."}},
            {"args": {"latency_ms": [100, 120, 140, 160], "swing": 50},
             "explanation": "A steady climb of 20 per sample: any three samples swing 40, so it takes all four (swing 60).",
             "why": {"t": "Gradual ramp", "d": "Only a long run reaches the swing."}},
        ],
        "constraints": [
            "0 ≤ latency_ms.length ≤ 10⁵",
            "0 ≤ latency_ms[i] ≤ 10⁹",
            "1 ≤ swing ≤ 10⁹",
        ],
        "hints": [
            "Adding samples never lowers `max − min`. So for a fixed right edge, the valid left edges are a prefix.",
            "Move the right edge; while the window still swings enough, record its length and move the left edge.",
            "Two monotonic deques give the window max and min in O(1), just like the stable-window problem.",
        ],
        "tests": [
            {"args": {"latency_ms": [], "swing": 1}, "why": {"t": "Empty", "d": "No samples: 0."}},
            {"args": {"latency_ms": [500], "swing": 1}, "why": {"t": "Single sample", "d": "One sample never swings."}},
            {"args": {"latency_ms": [10, 10, 10], "swing": 1}, "why": {"t": "Flat", "d": "No swing at all: 0."}},
            {"args": {"latency_ms": [10, 20], "swing": 10}, "why": {"t": "Exactly the swing", "d": "max − min equal to the threshold counts."}},
            {"args": {"latency_ms": [300, 250, 200, 150, 100], "swing": 120}, "why": {"t": "Drop", "d": "A falling series counts as a swing too."}},
            {"args": {"latency_ms": [1, 50, 2, 51, 3, 100], "swing": 99}, "why": {"t": "Late spike", "d": "Only the last sample reaches the swing, far from the low."}},
            {"args": {"latency_ms": _V_SERIES, "swing": 60}, "why": {"t": "Large input", "d": "3,000 samples of a random walk."}},
        ],
        "solutions": [
            {"name": "Two deques, shrinking window (Optimal)",
             "description": "Grow the right edge, keeping max and min deques. While the window swings at least `swing`, record its length and advance the left edge, expiring deque fronts.",
             "time": "O(n)", "space": "O(n)",
             "keyPoints": ["Spread only grows as the window widens", "Shrink while the condition still holds", "Each index enters and leaves each deque once"],
             "code": '''from collections import deque


def fastest_ramp(latency_ms, swing):
    hi, lo = deque(), deque()
    left = 0
    best = 0
    for right, v in enumerate(latency_ms):
        while hi and latency_ms[hi[-1]] <= v:
            hi.pop()
        hi.append(right)
        while lo and latency_ms[lo[-1]] >= v:
            lo.pop()
        lo.append(right)
        while latency_ms[hi[0]] - latency_ms[lo[0]] >= swing:
            size = right - left + 1
            if best == 0 or size < best:
                best = size
            left += 1
            if hi[0] < left:
                hi.popleft()
            if lo[0] < left:
                lo.popleft()
    return best
'''},
            {"name": "Extend from every start", "slow": True,
             "description": "From each start, extend right while tracking max and min, and stop at the first length that swings enough.",
             "time": "O(n²)", "space": "O(1)",
             "keyPoints": ["Stops early per start", "Quadratic on calm series"],
             "code": '''def fastest_ramp(latency_ms, swing):
    best = 0
    n = len(latency_ms)
    for i in range(n):
        hi = lo = latency_ms[i]
        for j in range(i, n):
            if best and j - i + 1 >= best:
                break
            hi = max(hi, latency_ms[j])
            lo = min(lo, latency_ms[j])
            if hi - lo >= swing:
                best = j - i + 1
                break
    return best
'''},
        ],
        "starter": '''def fastest_ramp(latency_ms: list[int], swing: int) -> int:
    """Length of the shortest run whose max - min is at least swing, or 0."""
    raise NotImplementedError
''',
    },
]
