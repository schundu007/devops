"""Tests for DC-SEC-18 Session Token Manager."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)


class Brute:
    # Independent reference: a plain dict, scanned on every count.
    def __init__(self, ttl: int) -> None:
        self.ttl, self.exp = ttl, {}

    def issue(self, tid: str, now: int) -> None:
        self.exp[tid] = now + self.ttl

    def renew(self, tid: str, now: int) -> None:
        if self.exp.get(tid, -1) > now:
            self.exp[tid] = now + self.ttl

    def count_live(self, now: int) -> int:
        return sum(1 for e in self.exp.values() if e > now)


def test_normal_issue_renew_count():
    m = impl.TokenManager(5)
    m.issue("tok-a", 1)
    m.issue("tok-b", 2)
    assert m.count_live(3) == 2
    m.renew("tok-a", 4)          # tok-a now expires at 9
    assert m.count_live(7) == 1  # tok-b expired at 7
    assert m.count_live(9) == 0


def test_empty_manager():
    assert impl.TokenManager(10).count_live(1) == 0


def test_expiry_boundary_expires_first():
    m = impl.TokenManager(5)
    m.issue("tok", 1)            # expires at 6
    m.renew("tok", 6)            # too late: already expired at 6
    assert m.count_live(7) == 0


def test_renew_unknown_token_is_ignored():
    m = impl.TokenManager(5)
    m.renew("ghost", 1)
    assert m.count_live(2) == 0


def test_reissue_after_expiry():
    m = impl.TokenManager(3)
    m.issue("tok", 1)
    assert m.count_live(4) == 0
    m.issue("tok", 5)
    assert m.count_live(6) == 1


def test_production_vault_lease_renewals():
    # ttl 3600 s. A worker renews its lease every 1800 s; a crashed pod stops renewing.
    m = impl.TokenManager(3600)
    m.issue("lease/worker-1", 10)
    m.issue("lease/pod-crashed", 20)
    for t in range(1810, 10_000, 1800):
        m.renew("lease/worker-1", t)
    assert m.count_live(9_999) == 1   # pod-crashed expired at 3620


def test_large_random_matches_brute_force():
    rng = random.Random(1797)
    m, b = impl.TokenManager(50), Brute(50)
    ids = [f"tok-{i}" for i in range(300)]
    now = 0
    for _ in range(40_000):
        now += rng.randint(1, 3)
        op = rng.random()
        tid = rng.choice(ids)
        if op < 0.4:
            m.issue(tid, now); b.issue(tid, now)
        elif op < 0.8:
            m.renew(tid, now); b.renew(tid, now)
        else:
            assert m.count_live(now) == b.count_live(now)
