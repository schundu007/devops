"""Tests for DC-PLAT-01 IaC Apply Order.

(added) pytest wrapper. The cases themselves are the handbook's, read unchanged
from handbook.json (Source: Handbook #96 Course Schedule II).

The handbook marks this problem `cmp: "topo"`: any valid order is accepted, so the
listed `expected` is one valid answer, not the only one. `is_valid_order` below is a
local (added) checker that accepts every valid order, the way the handbook's runner does.
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


def is_valid_order(n: int, prereqs: list[list[int]], order: list[int]) -> bool:
    """True if `order` lists every node 0..n-1 once and puts each b before a for [a, b]."""
    if sorted(order) != list(range(n)):
        return False
    pos = {node: i for i, node in enumerate(order)}
    return all(pos[b] < pos[a] for a, b in prereqs)


def check(args, expected, got):
    if expected == []:
        assert got == []  # a cycle: no order exists
    else:
        assert is_valid_order(args["numCourses"], args["prerequisites"], got)


# From handbook: all cases, unchanged.
@pytest.mark.parametrize("case", HB["tests"], ids=case_id)
def test_handbook_case(case):
    check(case["args"], case["expected"], run(impl, case["args"]))


# Step 3 check: every Python solution copied from the handbook passes the copied cases.
@pytest.mark.skipif(os.environ.get("CHIP_TARGET") == "starter", reason="checks handbook code only")
@pytest.mark.parametrize("name,module", handbook_solutions(__file__), ids=lambda x: x if isinstance(x, str) else "")
def test_every_handbook_solution(name, module):
    for case in HB["tests"]:
        check(case["args"], case["expected"], run(module, case["args"]))


# DevOps layer (added): the Terraform scenario from the README.
RESOURCES = [
    "aws_vpc.main",               # 0
    "aws_subnet.private_a",       # 1
    "aws_subnet.private_b",       # 2
    "aws_security_group.web",     # 3
    "aws_instance.web_a",         # 4
    "aws_instance.web_b",         # 5
    "aws_lb.web",                 # 6
]
DEPS = [[1, 0], [2, 0], [3, 0], [4, 1], [4, 3], [5, 2], [5, 3], [6, 1], [6, 2], [6, 4], [6, 5]]


def test_terraform_apply_and_destroy_order():
    order = run(impl, {"numCourses": len(RESOURCES), "prerequisites": DEPS})
    assert is_valid_order(len(RESOURCES), DEPS, order)
    assert order[0] == 0 and order[-1] == 6  # the VPC first, the load balancer last
    # Destroy runs in reverse: reversing a valid apply order is valid for the reversed edges.
    assert is_valid_order(len(RESOURCES), [[b, a] for a, b in DEPS], order[::-1])


def test_terraform_cycle_returns_empty():
    # The security group references the instance, and the instance references the group.
    assert run(impl, {"numCourses": 3, "prerequisites": [[1, 0], [2, 1], [1, 2]]}) == []


def test_large_random_dag_is_valid():
    rng = random.Random(210)
    n = 2000
    perm = list(range(n))
    rng.shuffle(perm)
    rank = {node: i for i, node in enumerate(perm)}
    edges = set()
    while len(edges) < 8000:
        a, b = rng.sample(range(n), 2)
        if rank[b] < rank[a]:
            edges.add((a, b))
    prereqs = [list(e) for e in edges]
    assert is_valid_order(n, prereqs, run(impl, {"numCourses": n, "prerequisites": prereqs}))
