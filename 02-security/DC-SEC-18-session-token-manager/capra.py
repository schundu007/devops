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
     "time": "O(1) amortised per call", "space": "O(live tokens)",
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
     "time": "O(1) amortised", "space": "O(live tokens)", "use": "Per-request quota and session checks."},
]
