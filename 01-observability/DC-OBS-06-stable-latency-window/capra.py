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
     "why": {"t": "Alternating spikes", "d": "Neighbours differ by 8, so no window longer than 1 fits."}},
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
