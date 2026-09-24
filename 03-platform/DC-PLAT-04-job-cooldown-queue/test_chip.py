"""Tests for DC-PLAT-04 Job Queue with Cooldown.

(added) pytest wrapper. The cases themselves are the handbook's, read unchanged
from handbook.json (Source: Handbook #73 Task Scheduler).

The handbook's Python solutions here are module-level functions (`leastInterval`),
so `run` below calls whichever form the module defines.
"""
from __future__ import annotations

import heapq
import os
import random
from collections import Counter

import pytest
from chip import case_id, handbook, handbook_solutions, load_impl

HB = handbook(__file__)
SPEC = HB["spec"]
impl = load_impl(__file__)


def run(module, args):
    fn = getattr(module.Solution(), SPEC["fn"]) if hasattr(module, "Solution") else getattr(module, SPEC["fn"])
    return fn(*[args[p] for p in SPEC["params"]])


# From handbook: all cases, unchanged.
@pytest.mark.parametrize("case", HB["tests"], ids=case_id)
def test_handbook_case(case):
    assert run(impl, case["args"]) == case["expected"]


# Step 3 check: every Python solution copied from the handbook passes the copied cases.
@pytest.mark.skipif(os.environ.get("CHIP_TARGET") == "starter", reason="checks handbook code only")
@pytest.mark.parametrize("name,module", handbook_solutions(__file__), ids=lambda x: x if isinstance(x, str) else "")
def test_every_handbook_solution(name, module):
    for case in HB["tests"]:
        assert run(module, case["args"]) == case["expected"], name


def simulate(tasks: list[str], n: int) -> int:
    """Independent check: tick by tick, run the ready job type with the most jobs left."""
    ready = [-c for c in Counter(tasks).values()]
    heapq.heapify(ready)
    cooling: list[tuple[int, int]] = []  # (tick when it is ready again, -remaining)
    t = 0
    while ready or cooling:
        while cooling and cooling[0][0] <= t:
            heapq.heappush(ready, heapq.heappop(cooling)[1])
        if ready:
            left = heapq.heappop(ready) + 1
            if left:
                heapq.heappush(cooling, (t + n + 1, left))
        t += 1
    return t


# DevOps layer (added): the rate-limited cloud API from the README.
def test_rate_limited_rotation_jobs():
    # R = rotate-keys, S = snapshot, C = cert-renew; each type needs 2 idle slots between runs.
    jobs = list("RRRRSSSC")
    assert run(impl, {"tasks": jobs, "n": 2}) == 10  # R . . R . . R . . R -> fill gaps with S, S, S, C


def test_no_cooldown_is_just_the_job_count():
    assert run(impl, {"tasks": list("ABCABCAB"), "n": 0}) == 8


def test_many_types_need_no_idle():
    # 26 job types, 2 each, cooldown 5: enough variety to never idle.
    jobs = [chr(65 + i) for i in range(26)] * 2
    assert run(impl, {"tasks": jobs, "n": 5}) == 52


def test_random_matches_simulation():
    rng = random.Random(621)
    for _ in range(300):
        jobs = [chr(65 + rng.randint(0, rng.randint(0, 25))) for _ in range(rng.randint(1, 60))]
        n = rng.randint(0, 12)
        assert run(impl, {"tasks": jobs, "n": n}) == simulate(jobs, n)


def test_large_input():
    rng = random.Random(1)
    jobs = [chr(65 + rng.randint(0, 5)) for _ in range(10_000)]
    assert run(impl, {"tasks": jobs, "n": 100}) == simulate(jobs, 100)
