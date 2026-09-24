"""Tests for DC-NET-05 Route Prefix Trie.

(added) pytest wrapper. The cases themselves are the handbook's, read unchanged
from handbook.json (Source: Handbook #36 Implement Trie (Prefix Tree)).
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


# DevOps layer (added): the gateway route table from the README.
def test_gateway_route_table():
    t = impl.Trie()
    for route in ["/api/v1/orders", "/api/v1/orders/refunds", "/api/v2/users", "/healthz"]:
        t.insert(route)
    assert t.search("/api/v1/orders") is True
    assert t.search("/api/v1/order") is False          # a prefix, not a route
    assert t.startsWith("/api/v1/order") is True
    assert t.startsWith("/api/v3") is False
    assert t.search("/healthz") is True
    assert t.startsWith("/") is True
    assert t.search("/api/v1/orders/refunds/42") is False


# DevOps layer (added): large random cross-check against a set-based brute force.
def test_random_matches_brute_force():
    rng = random.Random(208)
    t = impl.Trie()
    routes: set[str] = set()
    alphabet = "abc"
    for _ in range(5_000):
        w = "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 8)))
        op = rng.random()
        if op < 0.4:
            t.insert(w)
            routes.add(w)
        elif op < 0.7:
            assert t.search(w) == (w in routes), w
        else:
            assert t.startsWith(w) == any(r.startswith(w) for r in routes), w
