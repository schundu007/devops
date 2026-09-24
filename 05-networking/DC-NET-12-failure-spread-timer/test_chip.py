"""Tests for DC-NET-12 Failure Spread Timer.

(added) pytest wrapper. The cases themselves are the handbook's, read unchanged
from handbook.json (Source: Handbook #95 Rotting Oranges).
"""
from __future__ import annotations

import copy
import os
import random

import pytest
from chip import case_id, handbook, handbook_solutions, load_impl, run_handbook_case

HB = handbook(__file__)
impl = load_impl(__file__)


# From handbook: all cases, unchanged. Args are deep-copied so no run can mutate them.
@pytest.mark.parametrize("case", HB["tests"], ids=case_id)
def test_handbook_case(case):
    assert run_handbook_case(impl, HB["spec"], copy.deepcopy(case["args"])) == case["expected"]


# Step 3 check: every Python solution copied from the handbook passes the copied cases.
@pytest.mark.skipif(os.environ.get("CHIP_TARGET") == "starter", reason="checks handbook code only")
@pytest.mark.parametrize("name,module", handbook_solutions(__file__), ids=lambda x: x if isinstance(x, str) else "")
def test_every_handbook_solution(name, module):
    for case in HB["tests"]:
        got = run_handbook_case(module, HB["spec"], copy.deepcopy(case["args"]))
        assert got == case["expected"], name


# DevOps layer (added): the rack scenario from the README.
def test_rack_cascade_with_isolated_segment():
    # 2 = failed node, 1 = healthy node, 0 = empty slot / firewall gap.
    rack = [
        [2, 1, 1, 0, 1],
        [1, 1, 0, 0, 1],
        [0, 1, 1, 0, 1],
    ]
    # The right-hand column is cut off by empty slots: it is never reached.
    assert impl.Solution().orangesRotting(copy.deepcopy(rack)) == -1
    rack[0][3] = 1  # remove the gap: the failure now reaches every node
    assert impl.Solution().orangesRotting(copy.deepcopy(rack)) == 6


def _brute(grid: list[list[int]]) -> int:
    g = [row[:] for row in grid]
    m, n = len(g), len(g[0])
    minutes = 0
    while True:
        to_fail = [(r, c) for r in range(m) for c in range(n) if g[r][c] == 1 and any(
            0 <= r + dr < m and 0 <= c + dc < n and g[r + dr][c + dc] == 2
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
        if not to_fail:
            break
        for r, c in to_fail:
            g[r][c] = 2
        minutes += 1
    return -1 if any(1 in row for row in g) else minutes


# DevOps layer (added): random grids against a minute-by-minute simulation.
def test_random_grids_match_simulation():
    rng = random.Random(994)
    for _ in range(300):
        m, n = rng.randint(1, 10), rng.randint(1, 10)
        grid = [[rng.choice([0, 1, 1, 1, 2]) for _ in range(n)] for _ in range(m)]
        assert impl.Solution().orangesRotting(copy.deepcopy(grid)) == _brute(grid)
