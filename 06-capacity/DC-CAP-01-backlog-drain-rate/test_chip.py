"""Tests for DC-CAP-01 Backlog Drain Rate.

(added) pytest wrapper. The cases themselves are the handbook's, read unchanged
from handbook.json (Source: Handbook #85 Koko Eating Bananas).
"""
from __future__ import annotations

import os
import random

import pytest
from chip import case_id, handbook, handbook_solutions, load_impl, run_handbook_case

HB = handbook(__file__)
impl = load_impl(__file__)


# From handbook: all cases, unchanged.
@pytest.mark.parametrize("case", HB["tests"], ids=case_id)
def test_handbook_case(case):
    assert run_handbook_case(impl, HB["spec"], case["args"]) == case["expected"]


# Step 3 check: every Python solution copied from the handbook passes the copied cases.
@pytest.mark.skipif(os.environ.get("CHIP_TARGET") == "starter", reason="checks handbook code only")
@pytest.mark.parametrize("name,module", handbook_solutions(__file__), ids=lambda x: x if isinstance(x, str) else "")
def test_every_handbook_solution(name, module):
    for case in HB["tests"]:
        assert run_handbook_case(module, HB["spec"], case["args"]) == case["expected"], name


def _hours(backlogs: list[int], rate: int) -> int:
    return sum((b + rate - 1) // rate for b in backlogs)


# DevOps layer (added): the post-outage Kafka scenario from the README.
def test_orders_topic_after_outage():
    # Messages (in thousands) waiting on 6 partitions after a 40-minute consumer outage.
    backlogs = [1_200, 300, 4_800, 950, 2_100, 60]
    rate = impl.Solution().minEatingSpeed(backlogs, 8)
    assert _hours(backlogs, rate) <= 8          # the SLA is met
    assert _hours(backlogs, rate - 1) > 8       # and no smaller rate meets it
    # 4,800 needs 3 hours and 2,100 needs 1 hour at 2,100/h: 1+1+3+1+1+1 = 8.
    assert rate == 2_100


# DevOps layer (added): large random inputs against the definition.
def test_random_matches_definition():
    rng = random.Random(875)
    for _ in range(200):
        backlogs = [rng.randint(1, 10**6) for _ in range(rng.randint(1, 50))]
        h = rng.randint(len(backlogs), len(backlogs) * 20)
        rate = impl.Solution().minEatingSpeed(backlogs, h)
        assert _hours(backlogs, rate) <= h
        assert rate == 1 or _hours(backlogs, rate - 1) > h
