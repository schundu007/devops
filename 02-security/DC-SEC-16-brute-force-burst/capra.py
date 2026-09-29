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

VARIANT_TITLE = "Three uses in an hour"
VARIANT_APPROACH = "Group, sort, slide 3 · O(n log n) · O(n)"

_THR_FAST = '''from collections import defaultdict


def threshold_alerts(events: list[list], k: int, window: int) -> list[str]:
    by_name: dict[str, list[int]] = defaultdict(list)
    for name, t in events:
        by_name[name].append(t)
    out = []
    for name, ts in by_name.items():
        ts.sort()
        if any(ts[i + k - 1] - ts[i] <= window for i in range(len(ts) - k + 1)):
            out.append(name)
    return sorted(out)
'''

_THR_SLOW = '''def threshold_alerts(events: list[list], k: int, window: int) -> list[str]:
    alerted = set()
    for name, t in events:
        if name in alerted:
            continue
        inside = sum(1 for n2, t2 in events if n2 == name and t <= t2 <= t + window)
        if inside >= k:
            alerted.add(name)
    return sorted(alerted)
'''

_FIRST_FAST = '''from collections import defaultdict, deque


def first_alerts(events: list[list], k: int, window: int) -> list[list]:
    recent: dict[str, deque] = defaultdict(deque)
    fired = set()
    out = []
    for name, t in events:
        if name in fired:
            continue
        q = recent[name]
        q.append(t)
        while q[0] < t - window:
            q.popleft()
        if len(q) >= k:
            fired.add(name)
            out.append([name, t])
            del recent[name]
    return out
'''

_FIRST_SLOW = '''def first_alerts(events: list[list], k: int, window: int) -> list[list]:
    fired = set()
    out = []
    for i, (name, t) in enumerate(events):
        if name in fired:
            continue
        count = sum(1 for n2, t2 in events[:i + 1] if n2 == name and t2 >= t - window)
        if count >= k:
            fired.add(name)
            out.append([name, t])
    return out
'''


def _th(events, k, window, t, d):
    return {"args": {"events": [list(e) for e in events], "k": k, "window": window}, "why": {"t": t, "d": d}}


def _big_events(seed, n, sort, accounts, span):
    rng = random.Random(seed)
    ev = [["acct-%d" % rng.randint(0, accounts - 1), rng.randint(0, span)] for _ in range(n)]
    return sorted(ev, key=lambda e: e[1]) if sort else ev


VARIANTS = [
    {
        "key": "k-in-window",
        "title": "Any threshold, any window",
        "approach": "Group, sort, slide a window of k · O(n log n) · O(n)",
        "spec": {"kind": "fn", "fn": "threshold_alerts", "params": ["events", "k", "window"], "cmp": "exact"},
        "statement": (
            "Detection rules differ per signal: 5 failed SSH logins in 60 seconds, 20 failed API keys in 10 "
            "minutes. Generalize the key-card alert.\n\n"
            "`events[i] = [name, t]` is a failure for account `name` at second `t` (unsorted, duplicates "
            "allowed). An account alerts when some `k` of its events fit in a span of at most `window` "
            "seconds (last - first ≤ window).\n\n"
            "Return the alerted account names sorted ascending."
        ),
        "examples": [
            {"args": {"events": [["root", 0], ["root", 30], ["root", 61], ["root", 90]], "k": 3, "window": 60},
             "explanation": "30, 61 and 90 span 60 seconds, so root alerts even though 0, 30 and 61 do not fit.",
             "why": {"t": "Later window", "d": "The burst need not start at the first event."}},
            {"args": {"events": [["svc", 5], ["svc", 5]], "k": 3, "window": 1000},
             "explanation": "Only two events: k = 3 is never reached.",
             "why": {"t": "Too few events", "d": "Fewer than k events can never alert."}},
        ],
        "constraints": ["0 ≤ events.length ≤ 5000", "0 ≤ t ≤ 10⁹", "1 ≤ k ≤ 1000", "0 ≤ window ≤ 10⁹"],
        "hints": [
            "Group by account and sort each account's times, as in the main problem.",
            "k events fit in the window exactly when some k consecutive sorted times do: check ts[i+k-1] - ts[i].",
        ],
        "tests": [
            _th([], 3, 60, "Empty", "No events: no alerts."),
            _th([["a", 10]], 1, 0, "k = 1", "Any single event alerts."),
            _th([["a", 7], ["a", 7], ["a", 7]], 3, 0, "Zero window, duplicates", "Three events in the same second fit a 0-second window."),
            _th([["a", 0], ["a", 60], ["b", 0], ["b", 61]], 2, 60, "Window edge", "Exactly `window` apart counts; one second more does not."),
            _th([["z", 3], ["m", 1], ["z", 1], ["m", 2], ["q", 100]], 2, 5, "Sorted output", "Several alerts come back in name order."),
            _th([["x", 900], ["x", 100], ["x", 500], ["x", 300], ["x", 700]], 3, 399, "Unsorted, spread out", "Every triple spans at least 400 seconds."),
            _th(_big_events(1604, 3000, False, 60, 30000), 5, 900, "Large input", "3,000 failures across 60 accounts, 5 in 15 minutes."),
        ],
        "solutions": [
            {"name": "Group, sort, window of k (Optimal)",
             "description": "Sort each account's times once; the account alerts if any k consecutive times span at most window.",
             "time": "O(n log n)", "space": "O(n)",
             "keyPoints": ["Consecutive sorted times are the tightest k-sets", "One pass per account after sorting", "Return names sorted"],
             "code": _THR_FAST},
            {"name": "Count forward from every event", "slow": True,
             "description": "For each event, count the same account's events in [t, t + window] by scanning the whole log.",
             "time": "O(n²)", "space": "O(n)",
             "keyPoints": ["No sorting needed", "Rescans the log for every event"],
             "code": _THR_SLOW},
        ],
        "starter": "def threshold_alerts(events: list[list], k: int, window: int) -> list[str]:\n    pass\n",
    },
    {
        "key": "first-alert-stream",
        "title": "Alert as events stream in",
        "approach": "Per-account deque of recent times · O(n) · O(n)",
        "spec": {"kind": "fn", "fn": "first_alerts", "params": ["events", "k", "window"], "cmp": "exact"},
        "statement": (
            "In production the detector sees failures live, in time order, and must page **the moment** an "
            "account crosses the line. `events[i] = [name, t]` arrive with non-decreasing `t`.\n\n"
            "When an event gives its account `k` events within the last `window` seconds (times in "
            "`[t - window, t]`, this event included), the account fires once, at time `t`. Later events for "
            "an account that already fired are ignored.\n\n"
            "Return `[name, t]` for each firing, in the order they fire."
        ),
        "examples": [
            {"args": {"events": [["bob", 0], ["amy", 10], ["bob", 20], ["amy", 30], ["bob", 40], ["amy", 41]], "k": 3, "window": 40},
             "explanation": "bob's third event at 40 has 0 and 20 inside [0, 40]: fire at 40. amy's third at 41 finds 10 and 30 inside [1, 41]: fire at 41.",
             "why": {"t": "Two accounts", "d": "Each account fires on the event that completes its burst."}},
        ],
        "constraints": ["0 ≤ events.length ≤ 5000", "t non-decreasing, 0 ≤ t ≤ 10⁹", "1 ≤ k ≤ 1000", "0 ≤ window ≤ 10⁹"],
        "hints": [
            "Keep a queue of each account's recent times; drop times older than t - window before counting.",
            "Once an account fires, forget its queue and skip its later events.",
        ],
        "tests": [
            _th([], 2, 10, "Empty", "No events: no firings."),
            _th([["a", 0]], 1, 0, "k = 1", "The first event fires immediately."),
            _th([["a", 0], ["a", 11], ["a", 22]], 2, 10, "Never close enough", "Every gap is 11 seconds, above a 10-second window."),
            _th([["a", 0], ["a", 10]], 2, 10, "Window edge", "An event exactly `window` earlier is still inside."),
            _th([["a", 5], ["b", 5], ["a", 5], ["b", 5], ["a", 5]], 2, 0, "Ties in one second", "Firing order follows input order."),
            _th([["a", 0], ["a", 1], ["a", 2], ["a", 3]], 2, 5, "Fires once", "Later events for a fired account are ignored."),
            _th(_big_events(2034, 4000, True, 80, 40000), 4, 600, "Large input", "4,000 time-ordered failures across 80 accounts, 4 in 10 minutes."),
        ],
        "solutions": [
            {"name": "Per-account deque (Optimal)",
             "description": "Append each event's time to its account's deque, pop times older than t - window, and fire when the deque holds k.",
             "time": "O(n)", "space": "O(n)",
             "keyPoints": ["Each time is pushed and popped at most once", "Time order means no sorting", "Fire once, then drop the account's state"],
             "code": _FIRST_FAST},
            {"name": "Rescan the history", "slow": True,
             "description": "For every event, count the account's earlier events inside the window by scanning everything seen so far.",
             "time": "O(n²)", "space": "O(1) extra",
             "keyPoints": ["Stateless and simple", "Quadratic in the log length"],
             "code": _FIRST_SLOW},
        ],
        "starter": "def first_alerts(events: list[list], k: int, window: int) -> list[list]:\n    pass\n",
    },
]
