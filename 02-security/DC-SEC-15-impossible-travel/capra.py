"""Capra Playground export for DC-SEC-15 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "flag_events", "params": ["events"], "types": {}, "ret": "value", "cmp": "exact"}


def case(events):
    return {"events": events}


EXAMPLES = [
    {"args": case(["dana,20,800,berlin", "dana,50,100,tokyo"]),
     "explanation": "Berlin at minute 20 and Tokyo at minute 50 are 30 minutes apart: both events are impossible travel.",
     "why": {"t": "Impossible travel", "d": "Two cities within 60 minutes."}},
    {"args": case(["lee,10,1200,paris", "lee,200,50,paris"]),
     "explanation": "The first event's risk is over 1,000. The second is the same city, much later.",
     "why": {"t": "Risk limit", "d": "A single action over the risk limit is flagged on its own."}},
    {"args": case(["sam,0,10,oslo", "sam,60,10,rome"]),
     "explanation": "A difference of exactly 60 minutes counts.",
     "why": {"t": "Window edge", "d": "60 minutes apart is still inside the window."}},
]


def _large():
    rng = random.Random(15)
    cities = ["berlin", "tokyo", "paris", "oslo", "rome"]
    return case([f"u{rng.randint(0, 20)},{rng.randint(0, 3000)},{rng.randint(0, 1100)},{rng.choice(cities)}" for _ in range(700)])


TESTS = [
    {"args": case([]), "why": {"t": "No events", "d": "Nothing to flag."}},
    {"args": case(["ann,5,1000,lima"]), "why": {"t": "Risk exactly at limit", "d": "1,000 is not over the limit."}},
    {"args": case(["ann,5,1001,lima"]), "why": {"t": "Risk just over", "d": "1,001 is flagged."}},
    {"args": case(["sam,0,10,oslo", "sam,61,10,rome"]), "why": {"t": "Just outside window", "d": "61 minutes apart is fine."}},
    {"args": case(["a,10,1,x", "b,20,1,y"]), "why": {"t": "Different users", "d": "Two cities but different users."}},
    {"args": case(["a,10,1,x", "a,20,1,x", "a,30,1,x"]), "why": {"t": "Same city", "d": "Many events in one city are fine."}},
    {"args": case(["a,10,1,x", "a,10,1,x", "a,40,1,y"]), "why": {"t": "Duplicate events", "d": "A suspicious string listed twice is returned twice."}},
    {"args": case(["a,100,1,x", "a,20,1,y", "a,500,1,x"]), "why": {"t": "Unsorted input", "d": "Events arrive out of time order; output keeps input order."}},
    {"args": _large(), "why": {"t": "Large input", "d": "700 events across 21 users and 5 cities."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Group, sort and slide (Optimal)",
     "description": "Group events by user and sort each user's events by minute. Slide a window [t - 60, t + 60] with two pointers, counting cities inside it. Two or more distinct cities in an event's window flags it; risk over 1,000 flags it too. Return flagged events in input order.",
     "time": "O(n log n)", "space": "O(n)",
     "keyPoints": ["Group by user first", "Each pointer moves at most n steps", "Keep input order in the output"]},
    {"name": "Compare every pair", "slow": True,
     "description": "For each event, compare it with every other event: same user, different city, and at most 60 minutes apart flags it.",
     "time": "O(n²)", "space": "O(n)",
     "keyPoints": ["Direct translation of the rule", "Too slow for a day of sign-ins"],
     "code": '''from __future__ import annotations


def flag_events(events: list[str]) -> list[str]:
    parsed = [e.split(",") for e in events]
    out = []
    for i, (user, minute, risk, city) in enumerate(parsed):
        bad = int(risk) > 1000 or any(
            j != i and u == user and c != city and abs(int(m) - int(minute)) <= 60
            for j, (u, m, _r, c) in enumerate(parsed)
        )
        if bad:
            out.append(events[i])
    return out
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Compare every pair", "idea": "Check every event against every other event.",
     "time": "O(n²)", "space": "O(n)", "use": "A few hundred events."},
    {"name": "Group, sort and slide", "idea": "Per user, a two-pointer window counts cities within 60 minutes.",
     "time": "O(n log n)", "space": "O(n)", "use": "Identity threat detection over a day of logs."},
]

VARIANT_TITLE = "Impossible travel"
VARIANT_APPROACH = "Group, sort and slide · O(n log n) · O(n)"

_SPREAD_FAST = '''from __future__ import annotations

from collections import Counter, defaultdict


def flag_users(events: list[str], k: int, window: int) -> list[str]:
    by_user: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for e in events:
        user, minute, country = e.split(",")
        by_user[user].append((int(minute), country))
    flagged = []
    for user, evs in by_user.items():
        evs.sort()
        seen: Counter[str] = Counter()
        lo = 0
        for t, country in evs:
            seen[country] += 1
            while evs[lo][0] < t - window:
                c = evs[lo][1]
                seen[c] -= 1
                if seen[c] == 0:
                    del seen[c]
                lo += 1
            if len(seen) >= k:
                flagged.append(user)
                break
    return sorted(flagged)
'''

_SPREAD_SLOW = '''from __future__ import annotations


def flag_users(events: list[str], k: int, window: int) -> list[str]:
    parsed = [(u, int(m), c) for u, m, c in (e.split(",") for e in events)]
    flagged = set()
    for user, t, _ in parsed:
        countries = {c for u, m, c in parsed if u == user and t <= m <= t + window}
        if len(countries) >= k:
            flagged.add(user)
    return sorted(flagged)
'''

_MFA_FAST = '''from __future__ import annotations

from collections import defaultdict


def mfa_fatigue(denials: list[str], k: int, window: int) -> list[list]:
    by_user: dict[str, list[int]] = defaultdict(list)
    for d in denials:
        user, minute = d.split(",")
        by_user[user].append(int(minute))
    out = []
    for user in sorted(by_user):
        times = sorted(by_user[user])
        lo = 0
        for hi, t in enumerate(times):
            while times[lo] < t - window:
                lo += 1
            if hi - lo + 1 >= k:
                out.append([user, t])
                break
    return out
'''

_MFA_SLOW = '''from __future__ import annotations


def mfa_fatigue(denials: list[str], k: int, window: int) -> list[list]:
    parsed = [(u, int(m)) for u, m in (d.split(",") for d in denials)]
    first: dict[str, int] = {}
    for user, t in parsed:
        count = sum(1 for u, m in parsed if u == user and t - window <= m <= t)
        if count >= k and (user not in first or t < first[user]):
            first[user] = t
    return [[u, first[u]] for u in sorted(first)]
'''


def _spread_large():
    rng = random.Random(1501)
    countries = ["US", "DE", "IN", "BR", "JP", "NG"]
    return {"events": [f"u{rng.randint(0, 25)},{rng.randint(0, 5000)},{rng.choice(countries)}" for _ in range(500)],
            "k": 3, "window": 90}


def _mfa_large():
    rng = random.Random(1502)
    return {"denials": [f"u{rng.randint(0, 30)},{rng.randint(0, 3000)}" for _ in range(500)], "k": 4, "window": 120}


VARIANTS = [
    {
        "key": "country-spread",
        "title": "Too many countries in a window",
        "approach": "Group, sort, slide with a country counter · O(n log n) · O(n)",
        "spec": {"kind": "fn", "fn": "flag_users", "params": ["events", "k", "window"]},
        "statement": (
            "Sign-ins from a VPN hop between two countries all day, so two countries is too noisy. "
            "Flag a user when their sign-ins come from **k or more distinct countries** within `window` minutes.\n\n"
            "- each event is `\"user,minute,country\"`; events arrive in any order\n"
            "- a user is flagged when some set of their events spans at most `window` minutes (last minus first) and covers at least `k` countries\n\n"
            "Return the flagged users, sorted, each once."
        ),
        "examples": [
            {"args": {"events": ["ana,0,US", "ana,30,DE", "ana,50,IN", "bo,0,US", "bo,30,DE", "bo,200,IN"], "k": 3, "window": 60},
             "explanation": "ana hits three countries within 50 minutes. bo's third country arrives 200 minutes after the first.",
             "why": {"t": "Spread in time", "d": "The same three countries only count inside one window."}},
        ],
        "constraints": ["0 ≤ events.length ≤ 1,000", "2 ≤ k ≤ 10", "0 ≤ minute ≤ 10⁵", "0 ≤ window ≤ 10⁴"],
        "hints": [
            "Group by user and sort each user's events by minute.",
            "Slide a window: add the new event's country, then drop events older than `t - window` from the left.",
            "Keep a counter of countries in the window; its size is the distinct count.",
        ],
        "tests": [
            {"args": {"events": [], "k": 2, "window": 60}, "why": {"t": "No events", "d": "Nobody to flag."}},
            {"args": {"events": ["a,0,US", "a,60,DE"], "k": 2, "window": 60}, "why": {"t": "Window edge", "d": "Exactly window minutes apart still counts."}},
            {"args": {"events": ["a,0,US", "a,61,DE"], "k": 2, "window": 60}, "why": {"t": "Just outside", "d": "One minute too far apart."}},
            {"args": {"events": ["a,5,US", "a,5,US", "a,6,US", "a,7,DE"], "k": 3, "window": 60}, "why": {"t": "Repeats are not new countries", "d": "Only two distinct countries."}},
            {"args": {"events": ["z,90,JP", "z,10,US", "z,50,DE", "y,0,US"], "k": 3, "window": 80}, "why": {"t": "Unsorted input", "d": "Events arrive out of order."}},
            {"args": {"events": ["b,0,US", "a,0,US", "b,1,DE", "a,1,DE"], "k": 2, "window": 0}, "why": {"t": "Zero window", "d": "With window 0 only same-minute sign-ins count, so nobody is flagged."}},
            {"args": _spread_large(), "why": {"t": "Larger input", "d": "500 sign-ins across 26 users and 6 countries."}},
        ],
        "solutions": [
            {"name": "Group, sort and slide (Optimal)",
             "description": "Per user, sort by minute and move a two-pointer window of width `window`, keeping a counter of countries; flag the user as soon as it holds k.",
             "time": "O(n log n)", "space": "O(n)",
             "keyPoints": ["Counter size = distinct countries", "Each pointer moves at most n steps", "Stop scanning a user once flagged"],
             "code": _SPREAD_FAST},
            {"name": "Window from every event", "slow": True,
             "description": "For every event, collect the user's countries in [t, t + window] by scanning all events.",
             "time": "O(n²)", "space": "O(n)",
             "keyPoints": ["Any qualifying window starts at some event", "Quadratic in the number of sign-ins"],
             "code": _SPREAD_SLOW},
        ],
        "starter": "def flag_users(events: list[str], k: int, window: int) -> list[str]:\n    pass\n",
    },
    {
        "key": "mfa-fatigue",
        "title": "MFA push-fatigue attack",
        "approach": "Group, sort, count in a sliding window · O(n log n) · O(n)",
        "spec": {"kind": "fn", "fn": "mfa_fatigue", "params": ["denials", "k", "window"]},
        "statement": (
            "An attacker with a stolen password spams MFA pushes until the victim taps approve. "
            "Each **denied** push is logged as `\"user,minute\"`, in any order.\n\n"
            "- a user is under attack once `k` or more denials fall in `[t - window, t]` for some denial minute `t`\n"
            "- report the **first** such minute `t` for each user\n\n"
            "Return `[user, minute]` pairs sorted by user."
        ),
        "examples": [
            {"args": {"denials": ["kim,0", "kim,2", "kim,3", "kim,9", "raj,0", "raj,20", "raj,40"], "k": 3, "window": 5},
             "explanation": "kim's third denial within 5 minutes lands at minute 3. raj's denials are 20 minutes apart.",
             "why": {"t": "First trigger minute", "d": "Report when the alert would first fire."}},
        ],
        "constraints": ["0 ≤ denials.length ≤ 1,000", "1 ≤ k ≤ 50", "0 ≤ minute ≤ 10⁵", "0 ≤ window ≤ 10⁴"],
        "hints": [
            "Group denial minutes by user and sort them.",
            "With two pointers, the window `[t - window, t]` holds `hi - lo + 1` denials.",
            "The first `hi` where that reaches k is the answer for the user.",
        ],
        "tests": [
            {"args": {"denials": [], "k": 3, "window": 5}, "why": {"t": "No denials", "d": "No alerts."}},
            {"args": {"denials": ["a,7"], "k": 1, "window": 0}, "why": {"t": "k = 1", "d": "A single denial fires at once."}},
            {"args": {"denials": ["a,0", "a,5", "a,10"], "k": 3, "window": 10}, "why": {"t": "Window edge", "d": "Denials exactly window apart are inside."}},
            {"args": {"denials": ["a,0", "a,5", "a,11"], "k": 3, "window": 10}, "why": {"t": "Just outside", "d": "The first denial has left by minute 11."}},
            {"args": {"denials": ["b,4", "b,4", "b,4", "a,1"], "k": 3, "window": 0}, "why": {"t": "Same minute", "d": "Three denials in one minute; a never fires."}},
            {"args": {"denials": ["c,50", "c,10", "c,12", "c,48", "c,49"], "k": 3, "window": 5}, "why": {"t": "Unsorted input", "d": "The early pair never fires; the later three do at 50."}},
            {"args": _mfa_large(), "why": {"t": "Larger input", "d": "500 denials across 31 users."}},
        ],
        "solutions": [
            {"name": "Group, sort and slide (Optimal)",
             "description": "Sort each user's denial minutes and advance a left pointer past anything older than t - window; the first time the window holds k denials, record t.",
             "time": "O(n log n)", "space": "O(n)",
             "keyPoints": ["Counting, not distinct values, so no counter is needed", "The first hit in sorted order is the earliest minute", "Stop once a user fires"],
             "code": _MFA_FAST},
            {"name": "Count behind every denial", "slow": True,
             "description": "For each denial, count the same user's denials in [t - window, t] by scanning all of them, and keep the smallest t that reaches k.",
             "time": "O(n²)", "space": "O(n)",
             "keyPoints": ["Direct translation of the rule", "Quadratic scan"],
             "code": _MFA_SLOW},
        ],
        "starter": "def mfa_fatigue(denials: list[str], k: int, window: int) -> list[list]:\n    pass\n",
    },
]
