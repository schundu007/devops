"""Capra Playground export for DC-SEC-18 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "design", "fn": "TokenManager", "params": [], "types": {}, "ret": "value", "cmp": "exact"}


def ops(ttl, *calls):
    return {"ops": ["TokenManager"] + [c[0] for c in calls], "vals": [[ttl]] + [list(c[1:]) for c in calls]}


EXAMPLES = [
    {"args": ops(5, ("renew", "sess-a", 1), ("issue", "sess-a", 2), ("renew", "sess-a", 6), ("count_live", 7),
                 ("count_live", 11)),
     "explanation": "Renewing an unknown token does nothing. sess-a is renewed at 6 (expires 11), so it is live at 7 and gone at 11.",
     "why": {"t": "Renew extends", "d": "A renew moves the expiry forward; expiry == now counts as expired."}},
    {"args": ops(10, ("issue", "t1", 5), ("renew", "t1", 15), ("count_live", 15)),
     "explanation": "t1 expires at 15. At 15 it has already expired, so the renew is ignored.",
     "why": {"t": "Renew at expiry", "d": "A token cannot be renewed at the exact moment it expires."}},
]


def _large():
    rng = random.Random(1797)
    calls, now = [], 1
    for _ in range(1500):
        now += rng.randint(0, 3)
        r = rng.random()
        tok = f"tok-{rng.randint(0, 150)}"
        if r < 0.45:
            calls.append(("issue", tok, now))
        elif r < 0.8:
            calls.append(("renew", tok, now))
        else:
            calls.append(("count_live", now))
    return ops(40, *calls)


TESTS = [
    {"args": ops(3, ("count_live", 1)), "why": {"t": "Empty", "d": "No tokens issued."}},
    {"args": ops(1, ("issue", "x", 1), ("count_live", 1), ("count_live", 2)),
     "why": {"t": "TTL of 1", "d": "Live in the second it is issued, gone one second later."}},
    {"args": ops(5, ("issue", "a", 1), ("issue", "a", 3), ("count_live", 5), ("count_live", 8)),
     "why": {"t": "Re-issue", "d": "Issuing an existing id again resets its expiry and does not double-count it."}},
    {"args": ops(5, ("issue", "a", 1), ("issue", "b", 2), ("issue", "c", 3), ("count_live", 6), ("count_live", 7)),
     "why": {"t": "Expiry order", "d": "Tokens expire oldest first."}},
    {"args": ops(4, ("issue", "a", 1), ("renew", "a", 4), ("renew", "a", 7), ("renew", "a", 10), ("count_live", 13)),
     "why": {"t": "Chained renews", "d": "Renewing just before each expiry keeps the token alive."}},
    {"args": ops(2, ("issue", "a", 1), ("count_live", 100), ("renew", "a", 100), ("count_live", 100)),
     "why": {"t": "Long idle", "d": "After a long gap the token is gone and a renew cannot bring it back."}},
    {"args": _large(), "why": {"t": "Large input", "d": "1,500 mixed calls on 150 token ids."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "OrderedDict by expiry (Optimal)",
     "description": "Keep token -> expiry in an OrderedDict ordered by last issue or renew. With one shared TTL that is also expiry order, so every call first evicts expired tokens from the front.",
     "time": "O(1) amortized per call", "space": "O(live tokens)",
     "keyPoints": ["Equal TTLs make insertion order equal expiry order", "Evict from the front while expiry <= now", "Renew only live tokens"]},
    {"name": "Dict + scan", "slow": True,
     "description": "Store token -> expiry in a plain dict and count the unexpired ones on every count_live.",
     "time": "O(n) per count_live", "space": "O(all tokens ever issued)",
     "keyPoints": ["Simple", "Never frees expired tokens"],
     "code": '''from __future__ import annotations


class TokenManager:
    def __init__(self, ttl: int) -> None:
        self.ttl = ttl
        self.expiry: dict[str, int] = {}

    def issue(self, token_id: str, now: int) -> None:
        self.expiry[token_id] = now + self.ttl

    def renew(self, token_id: str, now: int) -> None:
        if self.expiry.get(token_id, 0) > now:
            self.expiry[token_id] = now + self.ttl

    def count_live(self, now: int) -> int:
        return sum(1 for e in self.expiry.values() if e > now)
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Dict + scan", "idea": "Count unexpired tokens on every query.", "time": "O(n) per count",
     "space": "O(tokens ever issued)", "use": "An occasional dashboard count."},
    {"name": "OrderedDict eviction", "idea": "Evict expired tokens from the front on every call.",
     "time": "O(1) amortized", "space": "O(live tokens)", "use": "Per-request quota and session checks."},
]

VARIANT_TITLE = "Shared TTL tokens"
VARIANT_APPROACH = "OrderedDict by expiry · O(1) amortized · O(live tokens)"


def sops(*calls):
    return {"ops": ["SessionStore"] + [c[0] for c in calls], "vals": [[]] + [list(c[1:]) for c in calls]}


def lops(ttl, cap, *calls):
    return {"ops": ["SessionLimiter"] + [c[0] for c in calls], "vals": [[ttl, cap]] + [list(c[1:]) for c in calls]}


def _ttl_large():
    rng = random.Random(18)
    calls, now = [], 1
    for _ in range(1500):
        now += rng.randint(0, 3)
        r = rng.random()
        tok = f"tok-{rng.randint(0, 120)}"
        if r < 0.4:
            calls.append(("issue", tok, now, rng.choice([5, 30, 60, 300])))
        elif r < 0.75:
            calls.append(("renew", tok, now))
        else:
            calls.append(("count_live", now))
    return sops(*calls)


def _cap_large():
    rng = random.Random(1797)
    calls, now, sid = [], 1, 0
    for _ in range(1500):
        now += rng.randint(0, 4)
        user = f"u{rng.randint(0, 30)}"
        if rng.random() < 0.65:
            sid += 1
            calls.append(("login", user, f"s{sid}", now))
        else:
            calls.append(("live", user, now))
    return lops(60, 3, *calls)


VARIANTS = [
    {
        "key": "per-token-ttl",
        "title": "Different TTL per token",
        "approach": "Dict + min-heap of expiries, lazy deletion · O(log n) amortized · O(issues + renews)",
        "spec": {"kind": "design", "fn": "SessionStore", "params": []},
        "statement": (
            "Track tokens with their own TTLs (a CI job token lasts 5 minutes, a browser session an hour), so issue order is no longer expiry order.\n"
            "\n"
            "### Methods\n"
            "- `issue(token_id, now, ttl)`: create or replace the token; it expires at `now + ttl`\n"
            "- `renew(token_id, now)`: if the token is still live, extend it to `now` plus **its own** `ttl`; otherwise do nothing\n"
            "- `count_live(now)`: how many tokens have not expired\n"
            "\n"
            "### Rules\n"
            "- A token whose expiry equals `now` has expired"
        ),
        "examples": [
            {"args": sops(("issue", "browser", 0, 60), ("issue", "ci-job", 10, 5), ("count_live", 14), ("count_live", 15), ("count_live", 59)),
             "explanation": "ci-job was issued later but expires first, at 15. The browser session lasts until 60.",
             "why": {"t": "Later issued, earlier expiry", "d": "Insertion order no longer matches expiry order."}},
            {"args": sops(("issue", "a", 0, 10), ("renew", "a", 9), ("renew", "a", 19), ("count_live", 19)),
             "explanation": "Renewed at 9 to expire at 19. At 19 it has expired, so the second renew does nothing.",
             "why": {"t": "Renew at expiry", "d": "A renew at the exact expiry instant is too late."}},
        ],
        "constraints": ["1 ≤ ttl ≤ 10⁵", "now never decreases across calls", "At most 2000 calls"],
        "hints": [
            "Keep token to (expiry, ttl) in a dict, and push (expiry, token) onto a min-heap on every issue and renew.",
            "To count, pop heap tops with expiry <= now; delete the token only if the dict still holds that same expiry.",
            "Entries left behind by a renew are stale; skip them when they surface instead of searching the heap.",
        ],
        "tests": [
            {"args": sops(("count_live", 0)), "why": {"t": "Empty", "d": "No tokens."}},
            {"args": sops(("issue", "x", 5, 1), ("count_live", 5), ("count_live", 6)), "why": {"t": "TTL of 1", "d": "Live only in the second it is issued."}},
            {"args": sops(("issue", "x", 0, 100), ("issue", "x", 1, 2), ("count_live", 3)), "why": {"t": "Re-issue shortens", "d": "A new issue replaces the old, longer expiry."}},
            {"args": sops(("renew", "ghost", 1), ("count_live", 1)), "why": {"t": "Renew unknown", "d": "Renewing a token never issued does nothing."}},
            {"args": sops(("issue", "a", 0, 3), ("issue", "b", 0, 3), ("issue", "c", 0, 5), ("count_live", 3), ("count_live", 4), ("count_live", 5)),
             "why": {"t": "Same expiry", "d": "Two tokens expire together."}},
            {"args": sops(("issue", "a", 0, 4), ("renew", "a", 3), ("renew", "a", 6), ("count_live", 9), ("count_live", 10)),
             "why": {"t": "Chained renews", "d": "Each renew uses the token's own ttl."}},
            {"args": _ttl_large(), "why": {"t": "Large input", "d": "1,500 mixed calls with four different TTLs."}},
        ],
        "solutions": [
            {"name": "Min-heap with lazy deletion (Optimal)",
             "description": "The dict is the truth. Every issue or renew pushes (expiry, token). count_live pops expired tops and removes a token only when the popped expiry is its current one.",
             "time": "O(log n) issue/renew, O(log n) amortized count", "space": "O(issues + renews)",
             "keyPoints": ["Expiry <= now means expired", "Stale heap entries are skipped, not searched for", "Renew keeps the token's own ttl"],
             "code": '''import heapq


class SessionStore:
    def __init__(self):
        self.tokens = {}
        self.heap = []

    def _evict(self, now):
        while self.heap and self.heap[0][0] <= now:
            exp, tok = heapq.heappop(self.heap)
            if tok in self.tokens and self.tokens[tok][0] == exp:
                del self.tokens[tok]

    def issue(self, token_id, now, ttl):
        self._evict(now)
        self.tokens[token_id] = (now + ttl, ttl)
        heapq.heappush(self.heap, (now + ttl, token_id))

    def renew(self, token_id, now):
        self._evict(now)
        if token_id in self.tokens:
            ttl = self.tokens[token_id][1]
            self.tokens[token_id] = (now + ttl, ttl)
            heapq.heappush(self.heap, (now + ttl, token_id))

    def count_live(self, now):
        self._evict(now)
        return len(self.tokens)
'''},
            {"name": "Dict + scan", "slow": True,
             "description": "Store token to (expiry, ttl) and count the unexpired ones on every count_live.",
             "time": "O(n) per count_live", "space": "O(tokens ever issued)",
             "keyPoints": ["Simple", "Never frees expired tokens"],
             "code": '''class SessionStore:
    def __init__(self):
        self.tokens = {}

    def issue(self, token_id, now, ttl):
        self.tokens[token_id] = (now + ttl, ttl)

    def renew(self, token_id, now):
        if token_id in self.tokens and self.tokens[token_id][0] > now:
            ttl = self.tokens[token_id][1]
            self.tokens[token_id] = (now + ttl, ttl)

    def count_live(self, now):
        return sum(1 for exp, _ in self.tokens.values() if exp > now)
'''},
        ],
        "starter": '''class SessionStore:
    def __init__(self):
        pass

    def issue(self, token_id, now, ttl):
        pass

    def renew(self, token_id, now):
        pass

    def count_live(self, now):
        pass
''',
    },
    {
        "key": "session-cap",
        "title": "Concurrent session limit per user",
        "approach": "Per-user deque in login order · O(1) amortized · O(live sessions)",
        "spec": {"kind": "design", "fn": "SessionLimiter", "params": []},
        "statement": (
            "Cap how many devices one account can be signed in on: one sign-in too many kicks out that account's oldest session.\n"
            "\n"
            "### Methods\n"
            "- `SessionLimiter(ttl, cap)`: create the limiter\n"
            "- `login(user, session_id, now)`: start a new session; if the user already has `cap` live sessions, end the **oldest** one and return its id, otherwise return `None`\n"
            "- `live(user, now)`: how many live sessions the user has\n"
            "\n"
            "### Rules\n"
            "- Every session lives `ttl` seconds from its login and expires at `login + ttl`\n"
            "- A session is expired when its expiry equals `now`\n"
            "- Session ids are never reused"
        ),
        "examples": [
            {"args": lops(100, 2, ("login", "ana", "laptop", 0), ("login", "ana", "phone", 5), ("login", "ana", "tv", 9), ("live", "ana", 10)),
             "explanation": "The third login exceeds the cap of 2, so the oldest session, laptop, is kicked out.",
             "why": {"t": "Evict the oldest", "d": "The cap is enforced at login, oldest first."}},
            {"args": lops(10, 1, ("login", "bo", "s1", 0), ("login", "bo", "s2", 10), ("live", "bo", 10)),
             "explanation": "s1 expired at 10, so s2 fits without evicting anything.",
             "why": {"t": "Expired does not count", "d": "Expired sessions are cleared before the cap is checked."}},
        ],
        "constraints": ["1 ≤ ttl ≤ 10⁵", "1 ≤ cap ≤ 10", "now never decreases across calls", "At most 2000 calls"],
        "hints": [
            "Every session has the same ttl, so within one user, login order is expiry order.",
            "Keep a deque per user. Pop expired sessions from the front, then, if the deque is full, pop one more and return it.",
        ],
        "tests": [
            {"args": lops(5, 1, ("live", "nobody", 0)), "why": {"t": "Unknown user", "d": "No sessions: 0."}},
            {"args": lops(5, 1, ("login", "a", "s1", 0), ("login", "a", "s2", 1), ("live", "a", 1)), "why": {"t": "Cap of one", "d": "Every new login replaces the previous session."}},
            {"args": lops(5, 2, ("login", "a", "s1", 0), ("login", "b", "s2", 0), ("login", "a", "s3", 1), ("live", "a", 1), ("live", "b", 1)),
             "why": {"t": "Users are independent", "d": "Another user's sessions never count against the cap."}},
            {"args": lops(5, 2, ("login", "a", "s1", 0), ("login", "a", "s2", 0), ("login", "a", "s3", 5), ("live", "a", 5)),
             "why": {"t": "All expire at once", "d": "Both old sessions expired at 5: nothing is evicted."}},
            {"args": lops(10, 2, ("login", "a", "s1", 0), ("login", "a", "s2", 3), ("login", "a", "s3", 10), ("live", "a", 12), ("live", "a", 13)),
             "why": {"t": "Partial expiry", "d": "One session expired, one still live: room for the new one."}},
            {"args": lops(100, 3, ("login", "a", "s1", 0), ("login", "a", "s2", 0), ("login", "a", "s3", 0), ("login", "a", "s4", 0), ("login", "a", "s5", 0)),
             "why": {"t": "Same-second logins", "d": "Ties keep login order: s1, then s2 are evicted."}},
            {"args": _cap_large(), "why": {"t": "Large input", "d": "1,500 logins and checks over 31 users, cap 3."}},
        ],
        "solutions": [
            {"name": "Deque per user (Optimal)",
             "description": "Each user keeps a deque of (login time, id) in login order. Drop expired ones from the front, then evict the front if the deque is at the cap.",
             "time": "O(1) amortized per call", "space": "O(live sessions)",
             "keyPoints": ["Equal ttl makes login order equal expiry order", "Expire before checking the cap", "Each session leaves the deque once"],
             "code": '''from collections import deque


class SessionLimiter:
    def __init__(self, ttl, cap):
        self.ttl = ttl
        self.cap = cap
        self.users = {}

    def _clean(self, user, now):
        q = self.users.setdefault(user, deque())
        while q and q[0][0] + self.ttl <= now:
            q.popleft()
        return q

    def login(self, user, session_id, now):
        q = self._clean(user, now)
        kicked = q.popleft()[1] if len(q) == self.cap else None
        q.append((now, session_id))
        return kicked

    def live(self, user, now):
        return len(self._clean(user, now))
'''},
            {"name": "Filter a list", "slow": True,
             "description": "Keep every session per user in a list and rebuild the live list on every call.",
             "time": "O(sessions of the user) per call", "space": "O(all sessions)",
             "keyPoints": ["Straightforward", "Rescans the user's whole history"],
             "code": '''class SessionLimiter:
    def __init__(self, ttl, cap):
        self.ttl = ttl
        self.cap = cap
        self.all = {}
        self.gone = set()

    def _live(self, user, now):
        return [s for s in self.all.get(user, []) if s[1] not in self.gone and s[0] + self.ttl > now]

    def login(self, user, session_id, now):
        live = self._live(user, now)
        kicked = None
        if len(live) >= self.cap:
            kicked = live[0][1]
            self.gone.add(kicked)
        self.all.setdefault(user, []).append((now, session_id))
        return kicked

    def live(self, user, now):
        return len(self._live(user, now))
'''},
        ],
        "starter": '''class SessionLimiter:
    def __init__(self, ttl, cap):
        pass

    def login(self, user, session_id, now):
        pass

    def live(self, user, now):
        pass
''',
    },
]
