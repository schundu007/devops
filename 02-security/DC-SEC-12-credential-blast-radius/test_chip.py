"""Tests for DC-SEC-12 Blast Radius of a Leaked Credential."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)


def brute(holds: list[list[int]], leaked: int) -> list[int]:
    # Independent reference: grow the set until a full pass adds nothing.
    reach = {leaked}
    changed = True
    while changed:
        changed = False
        for i in range(len(holds)):
            if i in reach:
                for j in holds[i]:
                    if j not in reach:
                        reach.add(j)
                        changed = True
    return sorted(reach)


def test_normal_chain():
    assert impl.blast_radius([[1], [2], [3], []], 0) == [0, 1, 2, 3]


def test_single_resource_holds_nothing():
    assert impl.blast_radius([[]], 0) == [0]


def test_cycle_and_self_reference():
    # 0 -> 1 -> 0 and 2 holds its own key; 2 is not reachable.
    assert impl.blast_radius([[1, 0], [0], [2]], 0) == [0, 1]


def test_direction_matters():
    # 1 holds 0's key, not the other way round: leaking 0 reaches nothing else.
    assert impl.blast_radius([[], [0]], 0) == [0]
    assert impl.blast_radius([[], [0]], 1) == [0, 1]


def test_long_chain_no_recursion_limit():
    n = 50_000
    holds = [[i + 1] for i in range(n - 1)] + [[]]
    assert impl.blast_radius(holds, 0) == list(range(n))


def test_production_leaked_ci_token():
    # 0 ci-deploy-token -> 1 build VM (instance role) -> 2 artifacts bucket
    # 2 bucket stores 3 db-password in a .env file -> 3 orders-db
    # 4 audit-bucket and 5 hr-db are separate; 5 holds 3 but 3 holds nothing.
    holds = [[1], [2], [3], [], [], [3]]
    assert impl.blast_radius(holds, 0) == [0, 1, 2, 3]
    assert 4 not in impl.blast_radius(holds, 0)


def test_large_random_matches_brute_force():
    rng = random.Random(841)
    n = 400
    holds = [rng.sample(range(n), rng.randint(0, 2)) for _ in range(n)]
    for leaked in rng.sample(range(n), 20):
        assert impl.blast_radius(holds, leaked) == brute(holds, leaked)
