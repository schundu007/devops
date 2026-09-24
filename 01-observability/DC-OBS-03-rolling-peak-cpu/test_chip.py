"""Tests for DC-OBS-03 Rolling Peak CPU.

(added) pytest wrapper. The cases themselves are the handbook's, read unchanged
from handbook.json (Source: Handbook #83 Sliding Window Maximum).
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


# DevOps layer (added): HPA-style scale-down stabilization from the README.
def test_hpa_scale_down_stabilization():
    # One desired-replica recommendation every 15 s; a 300 s window holds 20 of them.
    recs = [12] * 5 + [4] * 3 + [12] * 4 + [3] * 30
    peaks = impl.Solution().maxSlidingWindow(recs, 20)
    # The 45-second dip to 4 never shows up: the window still holds a 12.
    assert all(p == 12 for p in peaks[:12])
    # Scale-down happens only once every 12 has been out of the window for a while.
    assert peaks[-1] == 3
    assert peaks.index(3) == 12   # the first window that holds no 12 starts at index 12


# DevOps layer (added): large-input sanity check against a brute force.
def test_large_random_matches_brute_force():
    rng = random.Random(239)
    cpu = [rng.randint(0, 100) for _ in range(20_000)]
    k = 40
    expected = [max(cpu[i:i + k]) for i in range(len(cpu) - k + 1)]
    assert impl.Solution().maxSlidingWindow(cpu, k) == expected
