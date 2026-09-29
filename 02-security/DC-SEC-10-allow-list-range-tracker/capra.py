"""Capra Playground export for DC-SEC-10 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "design", "fn": "AllowList", "params": [], "types": {}, "ret": "value", "cmp": "exact"}


def ops(*calls):
    return {"ops": ["AllowList"] + [c[0] for c in calls], "vals": [[]] + [list(c[1:]) for c in calls]}


EXAMPLES = [
    {"args": ops(("add", 80, 444), ("remove", 100, 200), ("covers", 80, 100), ("covers", 150, 160), ("ranges",)),
     "explanation": "Removing 100-199 from the middle splits [80, 444) into [80, 100) and [200, 444).",
     "why": {"t": "Split in the middle", "d": "A remove inside one range must leave two pieces."}},
    {"args": ops(("add", 10, 20), ("add", 20, 30), ("ranges",), ("covers", 15, 25)),
     "explanation": "Touching ranges merge: [10, 20) and [20, 30) become [10, 30).",
     "why": {"t": "Touching ranges", "d": "Ranges that only touch are reported merged."}},
]


def _large():
    rng = random.Random(10)
    calls = []
    for _ in range(150):
        lo = rng.randint(0, 900)
        hi = lo + rng.randint(1, 60)
        calls.append((rng.choice(["add", "add", "remove"]), lo, hi))
        if rng.random() < 0.4:
            q = rng.randint(0, 950)
            calls.append(("covers", q, q + rng.randint(1, 20)))
    calls.append(("ranges",))
    return ops(*calls)


TESTS = [
    {"args": ops(("covers", 0, 1), ("ranges",)), "why": {"t": "Empty list", "d": "Nothing is allowed yet."}},
    {"args": ops(("add", 443, 444), ("covers", 443, 444), ("covers", 442, 444)),
     "why": {"t": "Single port", "d": "A one-value range, and a query one value wider."}},
    {"args": ops(("add", 100, 200), ("covers", 100, 200), ("covers", 100, 201), ("covers", 199, 200)),
     "why": {"t": "Half-open boundary", "d": "hi is excluded: [100, 200) does not cover 200."}},
    {"args": ops(("add", 0, 10), ("add", 20, 30), ("add", 5, 25), ("ranges",)),
     "why": {"t": "Bridge", "d": "One add overlaps two ranges and joins them."}},
    {"args": ops(("add", 0, 100), ("remove", 0, 100), ("ranges",), ("covers", 0, 1)),
     "why": {"t": "Remove everything", "d": "Removing the exact range leaves nothing."}},
    {"args": ops(("add", 10, 20), ("remove", 30, 40), ("remove", 0, 5), ("ranges",)),
     "why": {"t": "Remove outside", "d": "Removing ranges that do not overlap changes nothing."}},
    {"args": ops(("add", 0, 10), ("add", 20, 30), ("add", 40, 50), ("remove", 5, 45), ("ranges",)),
     "why": {"t": "Remove across several", "d": "Keep the left part of the first and the right part of the last."}},
    {"args": ops(("add", 0, 10), ("add", 20, 30), ("covers", 5, 25)),
     "why": {"t": "Gap inside the query", "d": "A query spanning a gap is not covered."}},
    {"args": ops(("add", 3000, 4000), ("add", 3500, 3600), ("ranges",)),
     "why": {"t": "Duplicate add", "d": "Adding a range already allowed changes nothing."}},
    {"args": _large(), "why": {"t": "Large input", "d": "About 200 random adds, removes and queries."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Sorted disjoint ranges (Optimal)",
     "description": "Keep ranges sorted, never overlapping and never touching. add replaces the block of ranges that overlap or touch with one spanning range. remove keeps only the left part of the first overlapping range and the right part of the last. covers checks the one range that starts at or before lo.",
     "time": "O(log n) covers; O(log n + k) add/remove", "space": "O(n)",
     "keyPoints": ["Half-open ranges make splits exact", "Merging touching ranges keeps covers a single lookup", "A remove can add at most one range"]},
    {"name": "Set of allowed values", "slow": True,
     "description": "Store every allowed value in a set. add and remove update each value; covers checks each value; ranges rebuilds runs from the sorted set.",
     "time": "O(hi - lo) per call", "space": "O(allowed values)",
     "keyPoints": ["Fine for 65,536 ports", "Hopeless for IPv4's 4 billion addresses"],
     "code": '''from __future__ import annotations


class AllowList:
    def __init__(self) -> None:
        self._on: set[int] = set()

    def add(self, lo: int, hi: int) -> None:
        self._on.update(range(lo, hi))

    def remove(self, lo: int, hi: int) -> None:
        self._on.difference_update(range(lo, hi))

    def covers(self, lo: int, hi: int) -> bool:
        return all(v in self._on for v in range(lo, hi))

    def ranges(self) -> list[tuple[int, int]]:
        out: list[tuple[int, int]] = []
        for v in sorted(self._on):
            if out and out[-1][1] == v:
                out[-1] = (out[-1][0], v + 1)
            else:
                out.append((v, v + 1))
        return out
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Set of values", "idea": "Track every allowed value individually.",
     "time": "O(range size) per call", "space": "O(values)", "use": "Tiny spaces such as ports."},
    {"name": "Sorted disjoint ranges", "idea": "Binary search a sorted list of merged, half-open ranges.",
     "time": "O(log n) query", "space": "O(ranges)", "use": "IP allow-lists and any large space."},
]

VARIANT_TITLE = "Allow-list ranges"
VARIANT_APPROACH = "Sorted disjoint ranges + binary search · O(log n) covers · O(n)"


def cops(*calls):
    return {"ops": ["AllowCount"] + [c[0] for c in calls], "vals": [[]] + [list(c[1:]) for c in calls]}


def pops(*calls):
    return {"ops": ["PortAllocator"] + [c[0] for c in calls], "vals": [[]] + [list(c[1:]) for c in calls]}


def _count_large():
    rng = random.Random(2276)
    calls = []
    for _ in range(300):
        lo = rng.randint(0, 3000)
        calls.append(("add", lo, lo + rng.randint(1, 80)))
        if rng.random() < 0.4:
            calls.append(("count",))
    return cops(*calls)


def _port_large():
    rng = random.Random(49152)
    calls = []
    for _ in range(250):
        lo = rng.randint(0, 1500)
        calls.append((rng.choice(["reserve", "reserve", "release"]), lo, lo + rng.randint(1, 50)))
        if rng.random() < 0.5:
            calls.append(("first_free", rng.randint(0, 1600)))
    return pops(*calls)


RANGES_CORE = '''    def __init__(self):
        self.starts = []
        self.ends = []

    def _add(self, lo, hi):
        i = bisect_left(self.ends, lo)
        j = bisect_right(self.starts, hi)
        if i < j:
            lo = min(lo, self.starts[i])
            hi = max(hi, self.ends[j - 1])
        self.starts[i:j] = [lo]
        self.ends[i:j] = [hi]
'''

VARIANTS = [
    {
        "key": "count-allowed",
        "title": "How many addresses are allowed",
        "approach": "Sorted disjoint ranges + running total · O(log n + k) add, O(1) count · O(n)",
        "spec": {"kind": "design", "fn": "AllowCount", "params": []},
        "statement": (
            "Count how many addresses an allow-list opens up in total, after every change, for a security review.\n"
            "\n"
            "### Methods\n"
            "- `add(lo, hi)`: allow every value in the half-open range `[lo, hi)`\n"
            "- `count()`: how many **distinct** values are allowed right now\n"
            "\n"
            "### Rules\n"
            "- Ranges may overlap earlier ones\n"
            "- `count` is called often, so it should not walk every range"
        ),
        "examples": [
            {"args": cops(("add", 10, 20), ("count",), ("add", 15, 30), ("count",), ("add", 0, 5), ("count",)),
             "explanation": "10 values, then the overlap 15-19 is counted once (20 values), then 5 more.",
             "why": {"t": "Overlap counted once", "d": "Merging must not double-count shared values."}},
        ],
        "constraints": ["0 ≤ lo < hi ≤ 2³²", "At most 2000 calls"],
        "hints": [
            "Keep the ranges merged, sorted and non-touching, exactly as in the main problem.",
            "Keep a running total. When add replaces a block of ranges with one, subtract their lengths and add the new one.",
            "The block to replace is found with two binary searches; each range is merged away at most once.",
        ],
        "tests": [
            {"args": cops(("count",)), "why": {"t": "Empty", "d": "Nothing allowed yet."}},
            {"args": cops(("add", 7, 8), ("count",)), "why": {"t": "Single value", "d": "A one-value range counts 1."}},
            {"args": cops(("add", 0, 10), ("add", 10, 20), ("count",)), "why": {"t": "Touching ranges", "d": "Adjacent ranges share no values: 20."}},
            {"args": cops(("add", 0, 100), ("add", 20, 30), ("add", 0, 100), ("count",)), "why": {"t": "Duplicate and nested", "d": "Adding a covered range changes nothing."}},
            {"args": cops(("add", 0, 5), ("add", 10, 15), ("add", 20, 25), ("add", 3, 22), ("count",)), "why": {"t": "Bridge several", "d": "One add swallows three ranges and the gaps."}},
            {"args": cops(("add", 0, 4294967296), ("count",)), "why": {"t": "All of IPv4", "d": "2^32 values: a set of values is hopeless here."}},
            {"args": _count_large(), "why": {"t": "Large input", "d": "300 random adds with interleaved counts."}},
        ],
        "solutions": [
            {"name": "Merged ranges + running total (Optimal)",
             "description": "Maintain sorted disjoint ranges. On add, find the block that overlaps or touches, subtract its total length, replace it with the merged range and add that length.",
             "time": "O(log n + k) add, O(1) count", "space": "O(n)",
             "keyPoints": ["Update the total only for the replaced block", "Half-open lengths are hi - lo", "Touching ranges merge"],
             "code": '''from bisect import bisect_left, bisect_right


class AllowCount:
    def __init__(self):
        self.starts = []
        self.ends = []
        self.total = 0

    def add(self, lo, hi):
        i = bisect_left(self.ends, lo)
        j = bisect_right(self.starts, hi)
        if i < j:
            lo = min(lo, self.starts[i])
            hi = max(hi, self.ends[j - 1])
            self.total -= sum(e - s for s, e in zip(self.starts[i:j], self.ends[i:j]))
        self.starts[i:j] = [lo]
        self.ends[i:j] = [hi]
        self.total += hi - lo

    def count(self):
        return self.total
'''},
            {"name": "Recount every range", "slow": True,
             "description": "Keep all added ranges; on count, sort them and sweep to sum the union length.",
             "time": "O(1) add, O(n log n) count", "space": "O(adds)",
             "keyPoints": ["Handles huge ranges, unlike a set of values", "Re-sorts on every count"],
             "code": '''class AllowCount:
    def __init__(self):
        self.ranges = []

    def add(self, lo, hi):
        self.ranges.append((lo, hi))

    def count(self):
        total, reach = 0, None
        for lo, hi in sorted(self.ranges):
            if reach is None or lo > reach:
                total += hi - lo
                reach = hi
            elif hi > reach:
                total += hi - reach
                reach = hi
        return total
'''},
        ],
        "starter": '''class AllowCount:
    def __init__(self):
        pass

    def add(self, lo, hi):
        pass

    def count(self):
        pass
''',
    },
    {
        "key": "port-allocator",
        "title": "Next free port",
        "approach": "Sorted disjoint reserved ranges + binary search · O(log n) first_free · O(n)",
        "spec": {"kind": "design", "fn": "PortAllocator", "params": []},
        "statement": (
            "Hand out host ports to containers: blocks get reserved and released, and a container asks for the first free port at or above a base.\n"
            "\n"
            "### Methods\n"
            "- `reserve(lo, hi)`: mark every port in `[lo, hi)` as reserved\n"
            "- `release(lo, hi)`: mark every port in `[lo, hi)` as free again\n"
            "- `first_free(port)`: the smallest port `>= port` that is not reserved\n"
            "\n"
            "### Rules\n"
            "- Reserved ranges may overlap\n"
            "- A release can split a reserved block\n"
            "- Ports are unbounded above, so a free port always exists"
        ),
        "examples": [
            {"args": pops(("reserve", 8000, 8100), ("first_free", 8000), ("first_free", 7999), ("release", 8050, 8060), ("first_free", 8000)),
             "explanation": "8000-8099 are taken, so the answer is 8100. 7999 is free itself. Releasing 8050-8059 opens a hole at 8050.",
             "why": {"t": "Skip a block · Hole", "d": "The answer is the end of the block that contains the port, or the port itself."}},
        ],
        "constraints": ["0 ≤ lo < hi ≤ 10⁶", "0 ≤ port ≤ 10⁶", "At most 2000 calls"],
        "hints": [
            "Store reserved ports as sorted, merged, non-touching half-open ranges.",
            "Find the one range that starts at or before `port`. If it contains `port`, the answer is its end, which is free because ranges never touch.",
            "Otherwise `port` itself is free.",
        ],
        "tests": [
            {"args": pops(("first_free", 0)), "why": {"t": "Nothing reserved", "d": "Every port is free."}},
            {"args": pops(("reserve", 0, 1), ("first_free", 0), ("first_free", 1)), "why": {"t": "Single port", "d": "Port 0 taken: 1 is next."}},
            {"args": pops(("reserve", 10, 20), ("reserve", 20, 30), ("first_free", 15)), "why": {"t": "Touching blocks", "d": "Adjacent blocks merge, so the answer is 30, not 20."}},
            {"args": pops(("reserve", 10, 20), ("first_free", 20), ("first_free", 9)), "why": {"t": "Half-open end", "d": "hi itself is free."}},
            {"args": pops(("reserve", 0, 100), ("release", 0, 100), ("first_free", 50)), "why": {"t": "Release everything", "d": "A full release frees the whole block."}},
            {"args": pops(("reserve", 0, 10), ("reserve", 20, 30), ("reserve", 40, 50), ("release", 5, 45), ("first_free", 3), ("first_free", 46)),
             "why": {"t": "Release across blocks", "d": "Keeps the left piece of the first and right piece of the last."}},
            {"args": pops(("release", 5, 9), ("reserve", 1, 3), ("release", 1, 2), ("first_free", 1), ("first_free", 2)),
             "why": {"t": "Release unreserved · Split at start", "d": "Releasing free ports is harmless; a split can free the first port."}},
            {"args": _port_large(), "why": {"t": "Large input", "d": "250 reserves and releases with interleaved lookups."}},
        ],
        "solutions": [
            {"name": "Sorted disjoint ranges (Optimal)",
             "description": "Reserve merges the overlapping or touching block into one range; release trims the block to its outer pieces. first_free checks the single range starting at or before the port.",
             "time": "O(log n) first_free, O(log n + k) reserve/release", "space": "O(n)",
             "keyPoints": ["Merged, non-touching ranges make the end of a range free", "Release can split one range", "One bisect answers a lookup"],
             "code": '''from bisect import bisect_left, bisect_right


class PortAllocator:
''' + RANGES_CORE + '''
    def reserve(self, lo, hi):
        self._add(lo, hi)

    def release(self, lo, hi):
        i = bisect_right(self.ends, lo)
        j = bisect_left(self.starts, hi)
        if i >= j:
            return
        ns, ne = [], []
        if self.starts[i] < lo:
            ns.append(self.starts[i])
            ne.append(lo)
        if self.ends[j - 1] > hi:
            ns.append(hi)
            ne.append(self.ends[j - 1])
        self.starts[i:j] = ns
        self.ends[i:j] = ne

    def first_free(self, port):
        k = bisect_right(self.starts, port) - 1
        if k >= 0 and self.ends[k] > port:
            return self.ends[k]
        return port
'''},
            {"name": "Set of reserved ports", "slow": True,
             "description": "Track every reserved port in a set and walk upward from the base until a free one appears.",
             "time": "O(hi - lo) reserve/release, O(block size) first_free", "space": "O(reserved ports)",
             "keyPoints": ["Fine for 65,536 ports", "Walks the whole block on each lookup"],
             "code": '''class PortAllocator:
    def __init__(self):
        self.taken = set()

    def reserve(self, lo, hi):
        self.taken.update(range(lo, hi))

    def release(self, lo, hi):
        self.taken.difference_update(range(lo, hi))

    def first_free(self, port):
        while port in self.taken:
            port += 1
        return port
'''},
        ],
        "starter": '''class PortAllocator:
    def __init__(self):
        pass

    def reserve(self, lo, hi):
        pass

    def release(self, lo, hi):
        pass

    def first_free(self, port):
        pass
''',
    },
]
