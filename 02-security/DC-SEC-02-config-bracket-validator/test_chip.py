"""Tests for DC-SEC-02 Config Bracket Validator.

(added) pytest wrapper. The cases themselves are the handbook's, read unchanged
from handbook.json (Source: Handbook #16 Valid Parentheses).
"""
from __future__ import annotations

import copy
import os
import random

import pytest
from chip import case_id, handbook, handbook_solutions, load_impl

HB = handbook(__file__)
SPEC = HB["spec"]
impl = load_impl(__file__)


def run(module, args):
    # The handbook's Python code is a plain function, not a Solution class.
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


def brackets_only(text: str) -> str:
    """DevOps layer: keep bracket characters that are outside double-quoted strings."""
    out, in_string, escaped = [], False, False
    for ch in text:
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        elif ch == '"':
            in_string = True
        elif ch in "()[]{}":
            out.append(ch)
    return "".join(out)


# DevOps layer (added): a CI pre-check on a Terraform-style block.
def test_ci_precheck_on_hcl_skeleton():
    good = '''resource "aws_security_group" "web" {
  ingress {
    cidr_blocks = ["10.0.0.0/16", "192.0.2.0/24"]
    description = "text with ) and ] inside a string"
  }
}'''
    bad = good.replace('"192.0.2.0/24"]', '"192.0.2.0/24"')  # missing ]
    assert impl.isValid(brackets_only(good)) is True
    assert impl.isValid(brackets_only(bad)) is False


# DevOps layer (added): deep nesting and a large random cross-check.
def test_large_inputs():
    assert impl.isValid("[" * 50_000 + "]" * 50_000) is True
    assert impl.isValid("{" * 50_000 + "]" * 50_000) is False
    rng = random.Random(20)
    for _ in range(500):
        s = "".join(rng.choice("()[]{}") for _ in range(rng.randrange(0, 12, 2)))
        ref = s
        while "()" in ref or "[]" in ref or "{}" in ref:  # independent reference
            ref = ref.replace("()", "").replace("[]", "").replace("{}", "")
        assert impl.isValid(s) is (ref == ""), s
