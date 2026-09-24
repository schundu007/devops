"""Tests for DC-PLAT-02 Circular Dependency Detector.

(added) pytest wrapper. The cases themselves are the handbook's, read unchanged
from handbook.json (Source: Handbook #45 Course Schedule).

The handbook's Python solutions here are module-level functions (`canFinish`), not a
`Solution` class, so `run` below calls whichever one the module defines.
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


def peel_brute_force(n: int, prereqs: list[list[int]]) -> bool:
    """Independent check: repeatedly delete any node with no remaining dependency."""
    alive = set(range(n))
    edges = {(a, b) for a, b in prereqs}
    changed = True
    while changed:
        changed = False
        for node in list(alive):
            if not any(a == node and b in alive for a, b in edges):
                alive.remove(node)
                changed = True
    return not alive


# DevOps layer (added): the Argo workflow from the README.
STEPS = ["checkout", "build", "unit-test", "image-push", "deploy-staging", "smoke-test"]


def test_argo_dag_without_cycle_passes():
    deps = [[1, 0], [2, 1], [3, 1], [4, 3], [4, 2], [5, 4]]
    assert run(impl, {"numCourses": len(STEPS), "prerequisites": deps}) is True


def test_argo_dag_with_cycle_is_blocked():
    # Someone made build wait on smoke-test "to reuse its cache": build -> smoke-test -> deploy-staging -> image-push -> build.
    deps = [[1, 0], [2, 1], [3, 1], [4, 3], [4, 2], [5, 4], [1, 5]]
    assert run(impl, {"numCourses": len(STEPS), "prerequisites": deps}) is False


def test_self_contained_steps_are_fine():
    # No dependencies at all: every step can run in parallel.
    assert run(impl, {"numCourses": 50, "prerequisites": []}) is True


def test_random_graphs_match_brute_force():
    rng = random.Random(207)
    for _ in range(150):
        n = rng.randint(1, 12)
        pairs = [[a, b] for a in range(n) for b in range(n) if a != b]
        prereqs = rng.sample(pairs, rng.randint(0, min(len(pairs), 14)))
        assert run(impl, {"numCourses": n, "prerequisites": prereqs}) == peel_brute_force(n, prereqs)


def test_large_dag_then_one_back_edge():
    rng = random.Random(7)
    n = 2000
    prereqs = []
    seen = set()
    while len(prereqs) < 5000 - 1:
        a, b = sorted(rng.sample(range(n), 2), reverse=True)  # a > b: always forward, no cycle
        if (a, b) not in seen:
            seen.add((a, b))
            prereqs.append([a, b])
    assert run(impl, {"numCourses": n, "prerequisites": prereqs}) is True
    a, b = prereqs[0]
    assert run(impl, {"numCourses": n, "prerequisites": prereqs + [[b, a]]}) is False
