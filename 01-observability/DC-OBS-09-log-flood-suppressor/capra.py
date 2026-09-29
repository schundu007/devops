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

VARIANT_TITLE = "Quiet period per message"
VARIANT_APPROACH = "Next allowed time per message · O(1) per call · O(m)"

_REPEAT_FAST = '''from __future__ import annotations


class RepeatCollapser:
    def __init__(self, window: int = 10) -> None:
        self.window = window
        self._state: dict[str, list[int]] = {}

    def log(self, timestamp: int, message: str) -> int:
        entry = self._state.get(message)
        if entry is not None and timestamp < entry[0]:
            entry[1] += 1
            return -1
        hidden = 0 if entry is None else entry[1]
        self._state[message] = [timestamp + self.window, 0]
        return hidden
'''

_REPEAT_SLOW = '''from __future__ import annotations


class RepeatCollapser:
    def __init__(self, window: int = 10) -> None:
        self.window = window
        self._calls: list[tuple[int, str, bool]] = []

    def log(self, timestamp: int, message: str) -> int:
        last = -1
        for i, (t, m, printed) in enumerate(self._calls):
            if m == message and printed:
                last = i
        if last >= 0 and timestamp - self._calls[last][0] < self.window:
            self._calls.append((timestamp, message, False))
            return -1
        hidden = sum(1 for t, m, p in self._calls[last + 1:] if m == message and not p) if last >= 0 else 0
        self._calls.append((timestamp, message, True))
        return hidden
'''

_RATE_FAST = '''from __future__ import annotations

from collections import deque


class LogRateLimiter:
    def __init__(self, limit: int, window: int) -> None:
        self.limit = limit
        self.window = window
        self._printed: dict[str, deque[int]] = {}

    def should_print(self, timestamp: int, message: str) -> bool:
        q = self._printed.setdefault(message, deque())
        while q and q[0] <= timestamp - self.window:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(timestamp)
        return True
'''

_RATE_SLOW = '''from __future__ import annotations


class LogRateLimiter:
    def __init__(self, limit: int, window: int) -> None:
        self.limit = limit
        self.window = window
        self._printed: list[tuple[int, str]] = []

    def should_print(self, timestamp: int, message: str) -> bool:
        recent = sum(1 for t, m in self._printed if m == message and t > timestamp - self.window)
        if recent >= self.limit:
            return False
        self._printed.append((timestamp, message))
        return True
'''


def _rops(window, *calls):
    return {"ops": ["RepeatCollapser"] + ["log"] * len(calls),
            "vals": [[] if window is None else [window]] + [list(c) for c in calls]}


def _lops(limit, window, *calls):
    return {"ops": ["LogRateLimiter"] + ["should_print"] * len(calls),
            "vals": [[limit, window]] + [list(c) for c in calls]}


def _stream(seed, n, kinds):
    rng = random.Random(seed)
    msgs = [f"upstream 503 svc={i}" for i in range(kinds)]
    t, calls = 0, []
    for _ in range(n):
        t += rng.choice([0, 0, 1, 1, 2, 4])
        calls.append((t, rng.choice(msgs)))
    return calls


VARIANTS = [
    {
        "key": "repeat-counter",
        "title": "\"Last message repeated N times\"",
        "approach": "Next allowed time plus a hidden counter per message · O(1) per call · O(m)",
        "spec": {"kind": "design", "fn": "RepeatCollapser", "params": []},
        "statement": (
            "syslog does not just drop repeats; when a message finally prints again it says how many copies it hid. "
            "Build `RepeatCollapser(window = 10)` with `log(timestamp, message)`:\n\n"
            "- if the message printed less than `window` seconds ago, suppress it and return `-1`\n"
            "- otherwise print it and return how many copies of it were suppressed since it last printed (0 the first time)\n\n"
            "As in the main problem, a suppressed call does not extend the quiet period. Timestamps never go backwards."
        ),
        "examples": [
            {"args": _rops(10, (1, "disk full"), (3, "disk full"), (5, "disk full"), (11, "disk full"), (12, "disk full")),
             "explanation": "Prints at 1 (0 hidden), hides 3 and 5, prints at 11 reporting 2 hidden, hides 12.",
             "why": {"t": "Count then reset", "d": "The counter resets each time the message prints."}},
        ],
        "constraints": ["1 ≤ window ≤ 10⁴", "0 ≤ timestamp ≤ 10⁹, non-decreasing", "0 ≤ calls ≤ 1,500"],
        "hints": [
            "Keep one small record per message: when it may print again, and how many copies were hidden since the last print.",
            "A suppressed call only bumps the counter; it never touches the next-allowed time.",
            "On a print, return the counter and then reset it to 0.",
        ],
        "tests": [
            {"args": _rops(None, (0, "x"), (9, "x"), (10, "x")), "why": {"t": "Default window", "d": "10 seconds when no window is given."}},
            {"args": _rops(10, (0, "")), "why": {"t": "Single call", "d": "The first print reports 0 hidden."}},
            {"args": _rops(5, (0, "a"), (1, "b"), (2, "a"), (3, "b"), (6, "a"), (6, "b")),
             "why": {"t": "Messages are independent", "d": "Each message keeps its own counter."}},
            {"args": _rops(3, (7, "burst"), (7, "burst"), (7, "burst"), (7, "burst"), (10, "burst")),
             "why": {"t": "Same-second burst", "d": "Three hidden copies within one second."}},
            {"args": _rops(2, (0, "tick"), (2, "tick"), (4, "tick")),
             "why": {"t": "Exactly window apart", "d": "Nothing is ever hidden, so each print reports 0."}},
            {"args": _rops(10, *[(t, "retrying") for t in range(0, 25)]),
             "why": {"t": "Suppression does not extend", "d": "A message every second prints at 0, 10 and 20, each reporting 9 hidden."}},
            {"args": _rops(10, *_stream(909, 400, 12)), "why": {"t": "Larger input", "d": "400 calls across 12 messages."}},
        ],
        "solutions": [
            {"name": "Next allowed time and counter (Optimal)",
             "description": "Store [next_allowed, hidden] per message. A suppressed call increments hidden; a printed call returns hidden and resets the record.",
             "time": "O(1) per call", "space": "O(m) distinct messages",
             "keyPoints": ["One lookup per call", "Suppressed calls only bump the counter", "Reset the counter on print"],
             "code": _REPEAT_FAST},
            {"name": "Scan the whole call history", "slow": True,
             "description": "Keep every call with a printed flag; find the message's last print by scanning, then count the hidden calls after it.",
             "time": "O(c) per call for c calls so far", "space": "O(c)",
             "keyPoints": ["Obviously correct", "Gets slower with every call"],
             "code": _REPEAT_SLOW},
        ],
        "starter": "class RepeatCollapser:\n    def __init__(self, window: int = 10) -> None:\n        pass\n\n    def log(self, timestamp: int, message: str) -> int:\n        pass\n",
    },
    {
        "key": "sliding-rate",
        "title": "At most N prints per window",
        "approach": "Deque of printed timestamps per message · O(1) amortized per call · O(m · limit)",
        "spec": {"kind": "design", "fn": "LogRateLimiter", "params": []},
        "statement": (
            "One print per window hides too much during an incident; the on-call wants a few samples. "
            "Build `LogRateLimiter(limit, window)` with `should_print(timestamp, message)`:\n\n"
            "- print (return `True`) when fewer than `limit` copies of this message were **printed** in `(timestamp - window, timestamp]`\n"
            "- otherwise return `False`; a suppressed call does not count\n\n"
            "Timestamps never go backwards. With `limit = 1` this is the main problem."
        ),
        "examples": [
            {"args": _lops(2, 10, (0, "5xx spike"), (1, "5xx spike"), (2, "5xx spike"), (10, "5xx spike"), (11, "5xx spike"), (12, "5xx spike")),
             "explanation": "0 and 1 print, 2 is the third in the window. At 10 the print from 0 has left; at 11 the one from 1 has left; 12 finds two prints (10, 11).",
             "why": {"t": "Sliding window", "d": "Old prints leave the window one at a time."}},
        ],
        "constraints": ["1 ≤ limit ≤ 50", "1 ≤ window ≤ 10⁴", "0 ≤ timestamp ≤ 10⁹, non-decreasing", "0 ≤ calls ≤ 1,500"],
        "hints": [
            "Only printed timestamps matter, and only those still inside the window.",
            "Keep a queue of printed timestamps per message; pop from the front while the oldest is `<= timestamp - window`.",
            "After trimming, the queue length is the count; it never grows past `limit`.",
        ],
        "tests": [
            {"args": _lops(1, 10, (0, "a"), (9, "a"), (10, "a")), "why": {"t": "Limit of one", "d": "Behaves like the main problem."}},
            {"args": _lops(3, 5, (4, "x"), (4, "x"), (4, "x"), (4, "x")), "why": {"t": "Same-second burst", "d": "Exactly `limit` copies print."}},
            {"args": _lops(2, 5, (0, "a"), (0, "b"), (1, "a"), (1, "b"), (2, "a"), (2, "b")),
             "why": {"t": "Messages are independent", "d": "Each message has its own allowance."}},
            {"args": _lops(1, 3, (0, "m"), (1, "m"), (2, "m"), (3, "m")),
             "why": {"t": "Suppressed calls do not count", "d": "Hidden calls at 1 and 2 never block the print at 3."}},
            {"args": _lops(2, 1, (5, "z"), (5, "z"), (5, "z"), (6, "z")), "why": {"t": "One-second window", "d": "The next second starts a fresh window."}},
            {"args": _lops(50, 10, (0, "")), "why": {"t": "Single call", "d": "The first call always prints."}},
            {"args": _lops(3, 10, *_stream(910, 500, 10)), "why": {"t": "Larger input", "d": "500 calls across 10 messages."}},
        ],
        "solutions": [
            {"name": "Deque per message (Optimal)",
             "description": "Keep a deque of printed timestamps per message, trim entries that left the window, and print only while the deque holds fewer than limit.",
             "time": "O(1) amortized per call", "space": "O(m · limit)",
             "keyPoints": ["Each timestamp enters and leaves once", "Only printed calls enter the deque", "Memory is bounded by limit per message"],
             "code": _RATE_FAST},
            {"name": "Scan every printed line", "slow": True,
             "description": "Keep all printed (timestamp, message) pairs and count matches inside the window on every call.",
             "time": "O(p) per call", "space": "O(p)",
             "keyPoints": ["Simple and correct", "History grows without bound"],
             "code": _RATE_SLOW},
        ],
        "starter": "class LogRateLimiter:\n    def __init__(self, limit: int, window: int) -> None:\n        pass\n\n    def should_print(self, timestamp: int, message: str) -> bool:\n        pass\n",
    },
]
