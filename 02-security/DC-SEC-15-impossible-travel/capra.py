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
