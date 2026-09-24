"""Tests for DC-SEC-13 Secret Exposure Over Time."""
from __future__ import annotations

import random
from itertools import groupby

from chip import load_impl

impl = load_impl(__file__)


def brute(n: int, sessions: list[list[int]], first: int) -> list[int]:
    # Independent reference: per time slot, sweep the slot's sessions until stable.
    has = {0, first}
    for _, grp in groupby(sorted(sessions, key=lambda s: s[2]), key=lambda s: s[2]):
        grp = list(grp)
        changed = True
        while changed:
            changed = False
            for a, b, _t in grp:
                if (a in has) != (b in has):
                    has |= {a, b}
                    changed = True
    return sorted(has)


def test_normal_chain_over_time():
    # 1 holds it from t=0. 1->2 at t=5, then 2->3 at t=8. 4-3 at t=1 was too early.
    assert impl.exposed(5, [[1, 2, 5], [2, 3, 8], [4, 3, 1]], 1) == [0, 1, 2, 3]


def test_time_order_matters():
    # 3 met 2 at t=2, but 2 only got the secret at t=5, so 3 stays clean.
    assert impl.exposed(4, [[3, 2, 2], [1, 2, 5]], 1) == [0, 1, 2]


def test_same_time_chain_spreads_instantly():
    # At t=3: 3-4 and 4-1 and 1 holds it -> 3 and 4 both exposed.
    assert impl.exposed(5, [[3, 4, 3], [4, 1, 3]], 1) == [0, 1, 3, 4]


def test_minimal_and_no_sessions():
    assert impl.exposed(2, [], 1) == [0, 1]


def test_clean_group_is_reset_before_later_slot():
    # t=1: 2-3 meet (both clean). t=2: 3-1 meet -> 3 exposed. 2 must stay clean.
    assert impl.exposed(4, [[2, 3, 1], [3, 1, 2]], 1) == [0, 1, 3]


def test_production_leaked_vault_token():
    # 0 = the leak itself, 1 = ci-runner-07 used the token at t=0.
    # t=10: ci-runner-07 opened a session to deploy-bot (2).
    # t=10: deploy-bot to k8s-admin (3) in the same minute -> exposed.
    # t=5 (earlier): k8s-admin talked to backup-svc (4) -> clean.
    sessions = [[1, 2, 10], [2, 3, 10], [3, 4, 5]]
    assert impl.exposed(5, sessions, 1) == [0, 1, 2, 3]


def test_large_random_matches_brute_force():
    rng = random.Random(2092)
    for _ in range(30):
        n = rng.randint(2, 60)
        sessions = []
        for _ in range(rng.randint(0, 150)):
            a, b = rng.sample(range(n), 2)
            sessions.append([a, b, rng.randint(1, 20)])
        first = rng.randint(1, n - 1)
        assert impl.exposed(n, sessions, first) == brute(n, sessions, first)
    # One large run: 20,000 parties, 50,000 sessions over 500 time slots.
    n = 20_000
    sessions = [[*rng.sample(range(n), 2), rng.randint(1, 500)] for _ in range(50_000)]
    assert impl.exposed(n, sessions, 1) == brute(n, sessions, 1)
