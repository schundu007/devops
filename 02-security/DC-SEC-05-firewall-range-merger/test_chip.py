"""Tests for DC-SEC-05 Firewall Range Merger.

(added) pytest wrapper. The cases themselves are the handbook's, read unchanged
from handbook.json (Source: Handbook #61 Merge Intervals).
"""
from __future__ import annotations

import copy
import ipaddress
import os
import random

import pytest
from chip import case_id, handbook, handbook_solutions, load_impl

HB = handbook(__file__)
SPEC = HB["spec"]
impl = load_impl(__file__)


def run(module, args):
    # The handbook's Python code is a plain function, not a Solution class.
    # Arguments are deep-copied because the handbook's merge changes its input (see Review note).
    fn = getattr(module, SPEC["fn"], None) or getattr(module.Solution(), SPEC["fn"])
    return fn(*[copy.deepcopy(args[p]) for p in SPEC["params"]])


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


# DevOps layer (added): overlapping security-group port rules.
def test_security_group_port_rules():
    rules = [[400, 8080], [80, 443], [22, 22], [9000, 9100], [9050, 9200]]
    assert impl.merge(copy.deepcopy(rules)) == [[22, 22], [80, 8080], [9000, 9200]]
    # Inclusive port ranges that only touch (443 and 444) are NOT merged by this rule.
    assert impl.merge([[80, 443], [444, 500]]) == [[80, 443], [444, 500]]


# DevOps layer (added): CIDRs -> integer [start, end) -> merge -> CIDRs.
def test_cidr_merge_via_integers():
    cidrs = ["10.0.0.0/25", "10.0.0.128/25", "10.0.1.0/24", "10.0.0.64/26", "192.0.2.0/28", "192.0.2.8/29"]
    nets = [ipaddress.ip_network(c) for c in cidrs]
    # Half-open [start, end+1): blocks that are merely adjacent now share an endpoint and merge.
    spans = [[int(n.network_address), int(n.broadcast_address) + 1] for n in nets]
    merged = impl.merge(spans)
    back = [
        net
        for s, e in merged
        for net in ipaddress.summarize_address_range(ipaddress.IPv4Address(s), ipaddress.IPv4Address(e - 1))
    ]
    assert back == list(ipaddress.collapse_addresses(nets))
    assert [str(n) for n in back] == ["10.0.0.0/23", "192.0.2.0/28"]


# DevOps layer (added): large random check against a doubled-coordinate sweep.
def test_large_random_matches_sweep():
    rng = random.Random(56)
    for _ in range(300):
        ivs = []
        for _ in range(rng.randint(1, 40)):
            a = rng.randint(0, 200)
            ivs.append([a, a + rng.randint(0, 15)])
        covered = set()
        for a, b in ivs:
            covered.update(range(2 * a, 2 * b + 1))  # doubling keeps [1,4],[5,6] apart
        expected, run_start, prev = [], None, None
        for p in sorted(covered):
            if run_start is None:
                run_start = p
            elif p != prev + 1:
                expected.append([run_start // 2, prev // 2])
                run_start = p
            prev = p
        expected.append([run_start // 2, prev // 2])
        assert impl.merge(copy.deepcopy(ivs)) == expected
    big = [[i, i + 2] for i in range(0, 30_000, 2)]
    assert impl.merge(big) == [[0, 30_000]]
