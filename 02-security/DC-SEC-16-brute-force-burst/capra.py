"""Capra Playground export for DC-SEC-16 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "burst_alerts", "params": ["names", "times"], "types": {}, "ret": "value", "cmp": "exact"}


def case(pairs):
    return {"names": [n for n, _ in pairs], "times": [t for _, t in pairs]}


EXAMPLES = [
    {"args": case([("alice", "10:00"), ("alice", "10:40"), ("alice", "11:00"), ("bob", "11:00"),
                   ("bob", "13:00"), ("bob", "12:05"), ("bob", "15:00")]),
     "explanation": "alice's first and third use are exactly 60 minutes apart, which counts. bob never fits 3 uses in an hour.",
     "why": {"t": "Window edge", "d": "Three uses exactly 60 minutes apart raise an alert."}},
    {"args": case([("svc-deploy", "09:00"), ("svc-deploy", "09:30"), ("svc-deploy", "10:01")]),
     "explanation": "09:00 to 10:01 is 61 minutes, one minute too wide.",
     "why": {"t": "Just outside", "d": "61 minutes is outside the window."}},
    {"args": case([("key-7", "14:20"), ("key-7", "13:50"), ("key-7", "14:05")]),
     "explanation": "Times arrive unsorted; sorted they are 13:50, 14:05, 14:20, all within 30 minutes.",
     "why": {"t": "Unsorted input", "d": "Times must be sorted per name before checking."}},
]


def _large():
    rng = random.Random(1604)
    pairs = []
    for i in range(3000):
        name = f"user-{rng.randint(0, 400)}"
        pairs.append((name, f"{rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}"))
    return case(pairs)


TESTS = [
    {"args": case([]), "why": {"t": "Empty", "d": "No uses at all: no alerts."}},
    {"args": case([("ci-bot", "08:00")]), "why": {"t": "Single use", "d": "One use can never be a burst."}},
    {"args": case([("ci-bot", "08:00"), ("ci-bot", "08:01")]), "why": {"t": "Two uses", "d": "Two uses are one short of a burst."}},
    {"args": case([("k", "23:59"), ("k", "23:59"), ("k", "23:59")]),
     "why": {"t": "Duplicates", "d": "Three uses in the same minute are a burst."}},
    {"args": case([("night", "23:30"), ("night", "23:50"), ("night", "00:10")]),
     "why": {"t": "No midnight wrap", "d": "Times are within one day; 00:10 is early morning, not after 23:50."}},
    {"args": case([("zed", "01:00"), ("amy", "02:00"), ("zed", "01:10"), ("amy", "02:30"), ("zed", "01:20"), ("amy", "02:59"), ("mo", "05:00")]),
     "why": {"t": "Sorted output", "d": "Several alerted names come back sorted ascending."}},
    {"args": case([("a", "00:00"), ("a", "01:01"), ("a", "02:02"), ("a", "03:03")]),
     "why": {"t": "Spread out", "d": "Many uses, but never 3 inside one hour."}},
    {"args": _large(), "why": {"t": "Large input", "d": "3,000 uses across 400 accounts."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Group, sort, slide 3 (Optimal)",
     "description": "Convert each time to minutes, group by name and sort. A burst exists exactly when some 3 consecutive uses in sorted order span at most 60 minutes.",
     "time": "O(n log n)", "space": "O(n)",
     "keyPoints": ["Sort each account's uses once", "Only consecutive triples need checking", "Return the names sorted"]},
    {"name": "Every triple", "slow": True,
     "description": "For each account, try every triple of its uses and check whether it fits in 60 minutes.",
     "time": "O(k³) per account", "space": "O(n)",
     "keyPoints": ["Obviously correct", "An account with 1,000 failures means 166 million triples"],
     "code": '''from __future__ import annotations

from collections import defaultdict
from itertools import combinations


def burst_alerts(names: list[str], times: list[str]) -> list[str]:
    minutes: dict[str, list[int]] = defaultdict(list)
    for name, hhmm in zip(names, times):
        h, m = hhmm.split(":")
        minutes[name].append(int(h) * 60 + int(m))
    alerted = []
    for name, ts in minutes.items():
        if any(max(t) - min(t) <= 60 for t in combinations(ts, 3)):
            alerted.append(name)
    return sorted(alerted)
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Every triple", "idea": "Check all triples of each account's uses.", "time": "O(k³)", "space": "O(n)",
     "use": "Tiny logs only."},
    {"name": "Sort + sliding window of 3", "idea": "Sort each account's minutes; check consecutive triples.",
     "time": "O(n log n)", "space": "O(n)", "use": "Real auth logs."},
]
