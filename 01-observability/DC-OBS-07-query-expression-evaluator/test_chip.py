"""Tests for DC-OBS-07 Query Expression Evaluator."""
from __future__ import annotations

import random

import pytest
from chip import load_impl

impl = load_impl(__file__)
ev = impl.evaluate
VALS = {"errors": 42, "timeouts": 8, "retries": 11, "total": 1000}


def test_normal_with_metrics():
    assert ev("(errors + timeouts) - retries", VALS) == 39


def test_single_operand():
    assert ev("7", {}) == 7
    assert ev("errors", VALS) == 42
    assert ev("   ", {}) == 0   # blank query: nothing to add


def test_unary_minus_and_nesting():
    assert ev("-(2 + 3)", {}) == -5
    assert ev("1 - (-(4 - 10))", {}) == -5
    assert ev("-errors + total", VALS) == 958


def test_minus_before_parentheses_flips_everything_inside():
    # Boundary: the classic bug is flipping only the first term inside the brackets.
    assert ev("100 - (errors - timeouts + retries)", VALS) == 55


def test_unknown_metric_raises():
    with pytest.raises(KeyError):
        ev("errors + dropped", VALS)


def test_capacity_headroom_query():
    # Production flavour: headroom = limit - (used_by_team_a + used_by_team_b) - reserved.
    vals = {"cpu_limit": 640, "team_a": 212, "team_b": 187, "reserved": 64}
    assert ev("cpu_limit - (team_a + team_b) - reserved", vals) == 177


def test_deep_nesting_and_long_input():
    depth = 20_000
    assert ev("(" * depth + "1" + ")" * depth, {}) == 1
    assert ev(" + ".join(["errors"] * 50_000), VALS) == 42 * 50_000


def _random_expr(rng: random.Random, depth: int) -> str:
    parts = []
    for k in range(rng.randint(1, 4)):
        if k:
            parts.append(rng.choice([" + ", " - ", "-", "+"]))
        roll = rng.random()
        if depth and roll < 0.3:
            inner = _random_expr(rng, depth - 1)
            # Unary minus is only legal at the start of a level (k == 0).
            parts.append(("-" if k == 0 and rng.random() < 0.3 else "") + f"({inner})")
        elif roll < 0.6:
            parts.append(rng.choice(list(VALS)))
        else:
            parts.append(str(rng.randint(0, 999)))
    return "".join(parts)


def test_random_matches_python_eval():
    rng = random.Random(224)
    for _ in range(2_000):
        expr = _random_expr(rng, 4)
        # Python's own evaluator on the same generated text is the independent reference.
        assert ev(expr, VALS) == eval(expr, {"__builtins__": {}}, dict(VALS)), expr
