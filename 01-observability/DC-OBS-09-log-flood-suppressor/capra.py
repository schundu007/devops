"""Capra Playground export for DC-OBS-09 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "design", "fn": "LogSuppressor", "params": [], "types": {}, "ret": "value", "cmp": "exact"}


def ops(window, *calls):
    """window None uses the default of 10 seconds."""
    return {"ops": ["LogSuppressor"] + ["should_print"] * len(calls),
            "vals": [[] if window is None else [window]] + [list(c) for c in calls]}


EXAMPLES = [
    {"args": ops(10, (1, "db timeout"), (2, "cache miss"), (3, "db timeout"), (10, "db timeout"), (11, "db timeout")),
     "explanation": "db timeout printed at 1 is quiet until 11. cache miss is a different message, so it prints.",
     "why": {"t": "Basic window", "d": "The same message is held back for 10 seconds; others are not."}},
    {"args": ops(10, *[(t, "retrying upstream") for t in range(0, 35)]),
     "explanation": "Printed at 0, 10, 20 and 30. Suppressed calls must not restart the quiet period, or it would print only at 0.",
     "why": {"t": "Suppression does not extend", "d": "A message logged every second still prints once per window."}},
]

T = 1_700_000_000


def _large():
    rng = random.Random(359)
    msgs = [f"error code={i}" for i in range(30)]
    t, calls = T, []
    for _ in range(1500):
        t += rng.choice([0, 0, 1, 1, 2, 5])
        calls.append((t, rng.choice(msgs)))
    return ops(10, *calls)


TESTS = [
    {"args": ops(None, (5, "x"), (14, "x"), (15, "x")),
     "why": {"t": "Default window", "d": "Without an argument the window is 10 seconds: 15 is allowed, 14 is not."}},
    {"args": ops(10, (T, "same second"), (T, "same second"), (T, "same second")),
     "why": {"t": "Same-second burst", "d": "A burst in one second prints exactly once."}},
    {"args": ops(10, (100, "a"), (100, "b"), (105, "a"), (105, "b")),
     "why": {"t": "Messages are independent", "d": "Each message has its own quiet period."}},
    {"args": ops(1, (1, "tick"), (2, "tick"), (2, "tick"), (3, "tick")),
     "why": {"t": "One-second window", "d": "A window of 1 allows the next second but not the same second."}},
    {"args": ops(10, (0, "")),
     "why": {"t": "Empty message", "d": "An empty string is still a message and prints the first time."}},
    {"args": ops(60, (0, "OOMKilled pod=checkout-7d9f4"), (30, "OOMKilled pod=checkout-7d9f4"),
                 (59, "OOMKilled pod=checkout-7d9f4"), (60, "OOMKilled pod=checkout-7d9f4"), (61, "OOMKilled pod=search-5c8b7")),
     "why": {"t": "Alert router", "d": "A 60-second repeat window per alert text, like a repeat interval."}},
    {"args": _large(),
     "why": {"t": "Large input", "d": "1,500 calls across 30 messages."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Next allowed time per message (Optimal)",
     "description": "Keep message -> earliest second it may print again. Print (and set timestamp + window) only when the call is at or after that second; a suppressed call changes nothing.",
     "time": "O(1) average per call", "space": "O(m) distinct messages",
     "keyPoints": ["One dict lookup per call", "Suppressed calls must not move the next-allowed time", "Memory grows with distinct messages"]},
    {"name": "Scan printed history", "slow": True,
     "description": "Keep every printed (timestamp, message) and scan back for the same message within the window.",
     "time": "O(p) per call for p printed lines", "space": "O(p)",
     "keyPoints": ["Obviously correct", "Gets slower as the log grows"],
     "code": '''from __future__ import annotations


class LogSuppressor:
    def __init__(self, window: int = 10) -> None:
        self.window = window
        self._printed: list[tuple[int, str]] = []

    def should_print(self, timestamp: int, message: str) -> bool:
        for t, m in self._printed:
            if m == message and timestamp - t < self.window:
                return False
        self._printed.append((timestamp, message))
        return True
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Scan printed history", "idea": "Look back through every printed line for the same message.",
     "time": "O(p) per call", "space": "O(p)", "use": "Tiny logs only."},
    {"name": "Next-allowed map", "idea": "Store when each message may print again; one lookup per call.",
     "time": "O(1) per call", "space": "O(distinct messages)", "use": "Log agents and alert routers."},
]
