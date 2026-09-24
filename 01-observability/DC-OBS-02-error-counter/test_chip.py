"""Tests for DC-OBS-02 5-Minute Error Counter.

(added) pytest wrapper. The cases themselves are the handbook's, read unchanged
from handbook.json (Source: Handbook #102 Design Hit Counter).
"""
from __future__ import annotations

import os
import random

import pytest
from chip import case_id, handbook, handbook_solutions, load_impl, run_handbook_case

HB = handbook(__file__)
impl = load_impl(__file__)


# From handbook: all 30 cases, unchanged.
@pytest.mark.parametrize("case", HB["tests"], ids=case_id)
def test_handbook_case(case):
    assert run_handbook_case(impl, HB["spec"], case["args"]) == case["expected"]


# Step 3 check: every Python solution copied from the handbook passes the copied cases.
@pytest.mark.skipif(os.environ.get("CHIP_TARGET") == "starter", reason="checks handbook code only")
@pytest.mark.parametrize("name,module", handbook_solutions(__file__), ids=lambda x: x if isinstance(x, str) else "")
def test_every_handbook_solution(name, module):
    for case in HB["tests"]:
        assert run_handbook_case(module, HB["spec"], case["args"]) == case["expected"], name


# DevOps layer (added): the on-call scenario from the README.
def test_checkout_api_error_budget_page():
    c = impl.HitCounter()
    t0 = 1_700_000_000
    for s in range(t0, t0 + 60):          # a 60 s burst: 3 x 5xx per second
        for _ in range(3):
            c.hit(s)
    for s in range(t0 + 60, t0 + 240, 20):  # then a trickle: 1 every 20 s
        c.hit(s)
    assert c.getHits(t0 + 239) == 180 + 9  # everything is still inside the window
    assert c.getHits(t0 + 300) == 177 + 9  # second t0 has just left (t0+300-300 = t0)
    assert c.getHits(t0 + 358) == 3 + 9    # only the burst's last second remains
    assert c.getHits(t0 + 359) == 9        # ...and now it has left too
    assert c.getHits(t0 + 600) == 0        # quiet for 5 min: the alert resolves


# DevOps layer (added): random cross-check against the definition.
def test_random_matches_definition():
    rng = random.Random(362)
    c = impl.HitCounter()
    hits: list[int] = []
    t = 1
    for _ in range(5_000):
        t += rng.choice([0, 0, 1, 2, 7, 150, 301])
        if rng.random() < 0.7:
            c.hit(t)
            hits.append(t)
        else:
            assert c.getHits(t) == sum(1 for h in hits if t - 300 < h <= t)
