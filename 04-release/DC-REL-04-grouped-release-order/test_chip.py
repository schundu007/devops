"""Tests for DC-REL-04 Grouped Release Order.

Many orders can be correct, so tests check validity, not one exact list.
"""
from __future__ import annotations

import random
from itertools import permutations

from chip import load_impl

impl = load_impl(__file__)


def is_valid(order: list[int], n: int, service: list[int], before: list[list[int]]) -> bool:
    if sorted(order) != list(range(n)):
        return False                                   # every step exactly once
    pos = {s: i for i, s in enumerate(order)}
    if any(pos[p] >= pos[i] for i in range(n) for p in before[i]):
        return False                                   # a before-rule is broken
    for g in set(x for x in service if x != -1):       # each service's steps contiguous
        idx = sorted(pos[s] for s in range(n) if service[s] == g)
        if idx[-1] - idx[0] + 1 != len(idx):
            return False
    return True


def exists_by_brute_force(n: int, service: list[int], before: list[list[int]]) -> bool:
    return any(is_valid(list(p), n, service, before) for p in permutations(range(n)))


def check(n, m, service, before, expect_possible):
    order = impl.release_order(n, m, service, before)
    if expect_possible:
        assert is_valid(order, n, service, before), order
    else:
        assert order == []


def test_normal_mixed_services():
    service = [-1, -1, 1, 0, 0, 1, 0, -1]
    before = [[], [6], [5], [6], [3, 6], [], [], []]
    check(8, 2, service, before, True)


def test_single_step_and_empty():
    check(1, 1, [0], [[]], True)
    check(1, 0, [-1], [[]], True)
    assert impl.release_order(0, 0, [], []) == []


def test_step_cycle_is_impossible():
    check(3, 1, [-1, -1, -1], [[2], [0], [1]], False)


def test_service_cycle_is_impossible_even_without_step_cycle():
    # Service 0 = steps {0, 1}, service 1 = steps {2, 3}.
    # 0 before 2 (svc0 -> svc1) and 3 before 1 (svc1 -> svc0): services cannot both be contiguous.
    service = [0, 0, 1, 1]
    before = [[], [3], [0], []]
    check(4, 2, service, before, False)
    assert not exists_by_brute_force(4, service, before)


def test_release_train_db_before_api_before_frontend():
    # Production flavour: services db(0), api(1), web(2), each with several steps;
    # step 9 is a standalone "announce in #releases" step that runs last.
    # 0 db-backup, 1 db-migrate, 2 api-canary, 3 api-rollout, 4 api-smoke,
    # 5 web-build, 6 web-cdn-purge, 7 web-rollout, 8 db-verify, 9 announce
    service = [0, 0, 1, 1, 1, 2, 2, 2, 0, -1]
    before = [[], [0], [8], [2], [3], [], [7], [5, 4], [1], [6]]
    order = impl.release_order(10, 3, service, before)
    assert is_valid(order, 10, service, before), order
    assert order[-1] == 9
    assert order.index(8) < order.index(2) < order.index(7)  # db before api before web


def test_random_small_cases_agree_with_brute_force():
    rng = random.Random(1203)
    for _ in range(400):
        n = rng.randint(1, 6)
        m = rng.randint(0, 3)
        service = [rng.randint(-1, m - 1) if m else -1 for _ in range(n)]
        before = [[p for p in range(n) if p != i and rng.random() < 0.2] for i in range(n)]
        order = impl.release_order(n, m, service, before)
        possible = exists_by_brute_force(n, service, before)
        if possible:
            assert is_valid(order, n, service, before), (n, m, service, before, order)
        else:
            assert order == []


def test_large_consistent_instance_is_solved():
    # Build a hidden valid grouped order, then only add rules that it satisfies.
    rng = random.Random(42)
    n, m = 3_000, 60
    service = [rng.randint(-1, m - 1) for _ in range(n)]
    groups = sorted(set(service) - {-1})
    rng.shuffle(groups)
    hidden = [s for g in groups for s in range(n) if service[s] == g]
    standalone = [s for s in range(n) if service[s] == -1]
    rng.shuffle(standalone)
    hidden += standalone                                    # standalone steps last, any order
    pos = {s: i for i, s in enumerate(hidden)}
    before: list[list[int]] = [[] for _ in range(n)]
    for _ in range(10_000):
        a, b = rng.sample(range(n), 2)
        if pos[a] < pos[b]:
            before[b].append(a)
    order = impl.release_order(n, m, service, before)
    assert is_valid(order, n, service, before)
