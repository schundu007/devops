"""Tests for DC-PLAT-03 Minimum CI Runners.

(added) pytest wrapper. The cases themselves are the handbook's, read unchanged
from handbook.json (Source: Handbook #64 Meeting Rooms II).

The handbook's Python solutions here are module-level functions (`minMeetingRooms`),
so `run` below calls whichever form the module defines.
"""
from __future__ import annotations

import os
import random

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


def peak_brute_force(jobs: list[list[int]]) -> int:
    """Independent check: the peak is reached at some job's start time."""
    return max(sum(1 for s, e in jobs if s <= t < e) for t, _ in jobs)


# DevOps layer (added): the merge-queue morning from the README.
def test_merge_queue_morning():
    # Minutes after 09:00: lint, unit, integration and e2e jobs from four merges.
    jobs = [[0, 4], [0, 12], [2, 30], [5, 9], [9, 20], [12, 18], [12, 40], [20, 26], [26, 31]]
    # Peak at 09:12: [2,30], [9,20], [12,18] and [12,40] all run ([0,12] has just ended).
    assert run(impl, {"intervals": jobs}) == 4


def test_back_to_back_jobs_share_a_runner():
    # A runner freed at minute 10 can take a job that starts at minute 10.
    assert run(impl, {"intervals": [[0, 10], [10, 20], [20, 30]]}) == 1


def test_all_jobs_at_once():
    assert run(impl, {"intervals": [[0, 60]] * 25}) == 25


def test_large_random_matches_brute_force():
    rng = random.Random(253)
    jobs = []
    for _ in range(2_000):
        s = rng.randint(0, 10_000)
        jobs.append([s, s + rng.randint(1, 600)])
    assert run(impl, {"intervals": jobs}) == peak_brute_force(jobs)
