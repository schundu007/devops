"""Capra Playground export for DC-CAP-02 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "min_nightly_capacity", "params": ["files", "nights"], "types": {}, "ret": "value", "cmp": "exact"}

EXAMPLES = [
    {"args": {"files": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "nights": 5},
     "explanation": "[1..5]=15, [6,7]=13, [8], [9], [10]. With 14 you would need 6 nights.",
     "why": {"t": "Ten files", "d": "The classic split."}},
    {"args": {"files": [3, 2, 2, 4, 1, 4], "nights": 3},
     "explanation": "[3,2] [2,4] [1,4]. Order is fixed, so the 1 cannot move earlier.",
     "why": {"t": "Order matters", "d": "Files must be copied in order."}},
    {"args": {"files": [500], "nights": 3},
     "explanation": "Capacity can never be smaller than the largest file.",
     "why": {"t": "Single file", "d": "The lower bound is max(files)."}},
]

_rng = random.Random(1011)
_BIG = [_rng.randint(1, 500) for _ in range(3000)]

TESTS = [
    {"args": {"files": [5, 5, 5, 5], "nights": 4}, "why": {"t": "One file per night", "d": "nights == len(files): the answer is max(files)."}},
    {"args": {"files": [5, 5, 5, 5], "nights": 1}, "why": {"t": "One night", "d": "Everything in one night: the answer is sum(files)."}},
    {"args": {"files": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1], "nights": 3}, "why": {"t": "All equal", "d": "Ten 1 GB files over three nights: 4."}},
    {"args": {"files": [500, 1, 1, 1, 500], "nights": 2}, "why": {"t": "Big at both ends", "d": "The big files force a split point."}},
    {"args": {"files": [1, 2, 3, 1, 1], "nights": 4}, "why": {"t": "Boundary", "d": "The answer equals max(files) exactly."}},
    {"args": {"files": [120, 80, 300, 40, 40, 220, 90, 60], "nights": 3},
     "why": {"t": "Nightly DB dumps", "d": "Ordered dump sizes in GB, three-night migration window."}},
    {"args": {"files": _BIG, "nights": 7}, "why": {"t": "Large input", "d": "3,000 random files over 7 nights."}},
    {"args": {"files": _BIG, "nights": 3000}, "why": {"t": "Large, one per night", "d": "Every file gets its own night."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Binary search on capacity (Optimal)",
     "description": "The answer lies between max(files) and sum(files). For a candidate capacity, count nights greedily in order; binary search for the smallest capacity that fits the deadline.",
     "time": "O(n · log(sum − max))", "space": "O(1) extra",
     "keyPoints": ["Feasibility is monotonic: more capacity never needs more nights", "Greedy packing is optimal when order is fixed", "Search between max and sum"]},
    {"name": "Try every capacity", "slow": True,
     "description": "Start at max(files) and try each larger capacity until the greedy count fits the deadline.",
     "time": "O(n · (sum − max))", "space": "O(1)",
     "keyPoints": ["Same greedy check", "Linear instead of binary search over the range"],
     "code": '''from __future__ import annotations


def min_nightly_capacity(files: list[int], nights: int) -> int:
    def nights_needed(cap: int) -> int:
        used, count = 0, 1
        for size in files:
            if used + size > cap:
                count += 1
                used = 0
            used += size
        return count

    cap = max(files)
    while nights_needed(cap) > nights:
        cap += 1
    return cap
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Linear search", "idea": "Try capacities upward from max(files).", "time": "O(n · (sum − max))",
     "space": "O(1)", "use": "Small totals only."},
    {"name": "Binary search on the answer", "idea": "Greedy feasibility check plus binary search.", "time": "O(n · log(sum − max))",
     "space": "O(1)", "use": "The standard answer."},
]

VARIANT_TITLE = "Nightly backup capacity"
VARIANT_APPROACH = "Binary search on capacity + greedy check · O(n · log(sum − max)) · O(1)"

_vr = random.Random(875)
_EXPORTS = [_vr.randint(1, 10**6) for _ in range(2000)]
_RACKS = sorted(_vr.sample(range(0, 10**6), 1500))

VARIANTS = [
    {
        "key": "export-throttle",
        "title": "Throttle a batch export",
        "approach": "Binary search on the rate · O(n · log max) · O(1)",
        "spec": {"kind": "fn", "fn": "min_export_rate", "params": ["tables", "hours"]},
        "statement": (
            "A nightly job exports database tables to object storage. `tables[i]` is the size of table `i` in GB. "
            "The exporter runs at a fixed rate of `r` GB per hour and handles **one table at a time**; when a table "
            "finishes early, the rest of that hour is wasted (the next table starts on the next hour boundary).\n\n"
            "So table `i` takes `ceil(tables[i] / r)` hours. Return the smallest integer rate `r` that finishes "
            "every table within `hours` hours. A lower rate means less load on the primary database."
        ),
        "examples": [
            {"args": {"tables": [3, 6, 7, 11], "hours": 8},
             "explanation": "At 4 GB/h the tables take 1 + 2 + 2 + 3 = 8 hours. At 3 GB/h they take 1 + 2 + 3 + 4 = 10.",
             "why": {"t": "Classic", "d": "The answer sits well below the largest table."}},
            {"args": {"tables": [30, 11, 23, 4, 20], "hours": 5},
             "explanation": "One hour per table is all the budget allows, so the rate must cover the largest table: 30.",
             "why": {"t": "One hour each", "d": "hours == len(tables) forces the rate to max(tables)."}},
        ],
        "constraints": [
            "1 ≤ tables.length ≤ 10⁴",
            "1 ≤ tables[i] ≤ 10⁹",
            "tables.length ≤ hours ≤ 10⁹",
        ],
        "hints": [
            "If rate `r` finishes in time, every rate above `r` does too. That monotonic yes/no is a binary search.",
            "The rate never needs to exceed `max(tables)`: at that rate every table already takes one hour.",
            "Count hours with `(size + r - 1) // r` to stay in integers.",
        ],
        "tests": [
            {"args": {"tables": [1], "hours": 1}, "why": {"t": "Minimal", "d": "One 1 GB table in one hour."}},
            {"args": {"tables": [10**9], "hours": 10**9}, "why": {"t": "Huge budget", "d": "One GB per hour is enough when the budget is huge."}},
            {"args": {"tables": [30, 11, 23, 4, 20], "hours": 6}, "why": {"t": "One spare hour", "d": "A single spare hour lowers the rate a lot."}},
            {"args": {"tables": [5, 5, 5, 5], "hours": 7}, "why": {"t": "All equal", "d": "Equal tables: the budget divides evenly or not at all."}},
            {"args": {"tables": [312884470], "hours": 968709470}, "why": {"t": "Budget above size", "d": "More hours than GB: rate 1."}},
            {"args": {"tables": [805306368, 805306368, 805306368], "hours": 1000000000}, "why": {"t": "Large sizes", "d": "Sizes near 10⁹ must not overflow or loop forever."}},
            {"args": {"tables": _EXPORTS, "hours": 5000}, "why": {"t": "Large input", "d": "2,000 random table sizes."}},
        ],
        "solutions": [
            {"name": "Binary search on the rate (Optimal)",
             "description": "Search rates between 1 and max(tables). For each candidate, sum ceil(size / rate) and move the bounds toward the smallest rate that fits.",
             "time": "O(n · log max)", "space": "O(1)",
             "keyPoints": ["Hours needed only drops as the rate grows", "Upper bound max(tables) always fits", "Integer ceiling division"],
             "code": '''def min_export_rate(tables, hours):
    lo, hi = 1, max(tables)
    while lo < hi:
        mid = (lo + hi) // 2
        if sum((t + mid - 1) // mid for t in tables) <= hours:
            hi = mid
        else:
            lo = mid + 1
    return lo
'''},
            {"name": "Scan candidate rates", "slow": True,
             "description": "Start at ceil(sum / hours), a rate below which the tables cannot fit, and raise the rate one GB/h at a time until the hour count fits.",
             "time": "O(n · (answer − sum/hours))", "space": "O(1)",
             "keyPoints": ["Start at ceil(sum / hours): no smaller rate can fit", "Walk up one GB/h at a time", "Correct but slow when the gap is wide"],
             "code": '''def min_export_rate(tables, hours):
    rate = max(1, (sum(tables) + hours - 1) // hours)
    while sum((t + rate - 1) // rate for t in tables) > hours:
        rate += 1
    return rate
'''},
        ],
        "starter": '''def min_export_rate(tables: list[int], hours: int) -> int:
    """Smallest GB-per-hour rate that exports every table within `hours`."""
    raise NotImplementedError
''',
    },
    {
        "key": "replica-spread",
        "title": "Spread replicas across racks",
        "approach": "Binary search on the gap + greedy placement · O(n · log range) · O(1)",
        "spec": {"kind": "fn", "fn": "max_min_spread", "params": ["positions", "replicas"]},
        "statement": (
            "A storage cluster has free slots at distinct positions along a row of racks, given sorted in "
            "`positions` (in meters). You must place `replicas` copies of a shard, one per slot.\n\n"
            "Replicas that sit close together share power and cooling, so a single failure can take out several. "
            "Place them so the **smallest distance between any two replicas** is as large as possible, and return that distance."
        ),
        "examples": [
            {"args": {"positions": [1, 2, 3, 4, 7], "replicas": 3},
             "explanation": "Place at 1, 4 and 7: every pair is at least 3 apart. No placement reaches 4.",
             "why": {"t": "Classic", "d": "Greedy placement from the left finds the best spread."}},
            {"args": {"positions": [5, 100], "replicas": 2},
             "explanation": "Two replicas must use both slots, 95 m apart.",
             "why": {"t": "Two slots", "d": "Every slot is used, so the answer is their gap."}},
        ],
        "constraints": [
            "2 ≤ positions.length ≤ 10⁴, sorted ascending, distinct",
            "0 ≤ positions[i] ≤ 10⁹",
            "2 ≤ replicas ≤ positions.length",
        ],
        "hints": [
            "Fix a gap `g`. Can you place all replicas at least `g` apart? Put one at the first slot, then each next one at the first slot `g` or more past the last.",
            "If gap `g` works, every smaller gap works. Binary search for the largest one that does.",
        ],
        "tests": [
            {"args": {"positions": [0, 1], "replicas": 2}, "why": {"t": "Minimal", "d": "Two adjacent slots."}},
            {"args": {"positions": [0, 10, 20, 30, 40], "replicas": 5}, "why": {"t": "Every slot", "d": "replicas == slots: the answer is the smallest neighbor gap."}},
            {"args": {"positions": [0, 10, 20, 30, 40], "replicas": 2}, "why": {"t": "Two ends", "d": "Two replicas go to the two ends."}},
            {"args": {"positions": [0, 1, 2, 3, 100], "replicas": 3}, "why": {"t": "Outlier slot", "d": "One far slot; the other two replicas crowd together."}},
            {"args": {"positions": [0, 3, 4, 7, 10, 11], "replicas": 3}, "why": {"t": "Tie gaps", "d": "Several placements give the same best gap."}},
            {"args": {"positions": [0, 10**9], "replicas": 2}, "why": {"t": "Wide range", "d": "Positions at both extremes."}},
            {"args": {"positions": _RACKS, "replicas": 40}, "why": {"t": "Large input", "d": "1,500 random slots, 40 replicas."}},
        ],
        "solutions": [
            {"name": "Binary search on the gap (Optimal)",
             "description": "Binary search the answer between 1 and the full span. For each candidate gap, place replicas greedily from the left and check that all of them fit.",
             "time": "O(n · log range)", "space": "O(1)",
             "keyPoints": ["Feasibility is monotonic in the gap", "Greedy leftmost placement is optimal", "Search for the largest feasible gap"],
             "code": '''def max_min_spread(positions, replicas):
    def fits(gap):
        count, last = 1, positions[0]
        for p in positions[1:]:
            if p - last >= gap:
                count += 1
                last = p
                if count == replicas:
                    return True
        return count >= replicas

    lo, hi = 1, positions[-1] - positions[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if fits(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo
'''},
            {"name": "Walk the gap down", "slow": True,
             "description": "No placement beats span / (replicas − 1). Start there and lower the gap one meter at a time until the greedy placement fits.",
             "time": "O(n · (bound − answer))", "space": "O(1)",
             "keyPoints": ["Upper bound: an even spread over the span", "Same greedy feasibility check", "Linear walk instead of binary search"],
             "code": '''def max_min_spread(positions, replicas):
    def fits(gap):
        count, last = 1, positions[0]
        for p in positions[1:]:
            if p - last >= gap:
                count += 1
                last = p
        return count >= replicas

    gap = (positions[-1] - positions[0]) // (replicas - 1)
    while not fits(gap):
        gap -= 1
    return gap
'''},
        ],
        "starter": '''def max_min_spread(positions: list[int], replicas: int) -> int:
    """Largest possible minimum distance between any two placed replicas."""
    raise NotImplementedError
''',
    },
]
