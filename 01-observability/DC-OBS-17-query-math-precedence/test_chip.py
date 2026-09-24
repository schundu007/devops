"""Tests for DC-OBS-17 Query Math with Precedence."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)


def reference(expr: str) -> int:
    # Independent reference: two passes over tokens, * and / first, then + and -.
    tokens: list[str] = []
    num = ""
    for ch in expr.replace(" ", ""):
        if ch.isdigit():
            num += ch
        else:
            tokens += [num, ch]
            num = ""
    tokens.append(num)
    terms = [int(tokens[0])]
    ops: list[str] = []
    for op, n in zip(tokens[1::2], tokens[2::2]):
        if op == "*":
            terms[-1] *= int(n)
        elif op == "/":
            q = abs(terms[-1]) // int(n)
            terms[-1] = q if terms[-1] >= 0 else -q
        else:
            ops.append(op)
            terms.append(int(n))
    total = terms[0]
    for op, t in zip(ops, terms[1:]):
        total = total + t if op == "+" else total - t
    return total


def test_precedence():
    assert impl.evaluate("3+2*2") == 7
    assert impl.evaluate("2*3+4") == 10


def test_single_number_and_spaces():
    assert impl.evaluate("42") == 42
    assert impl.evaluate("  7  ") == 7
    assert impl.evaluate(" 3 / 2 ") == 1


def test_division_truncates_toward_zero():
    # Boundary: 7/2 is 3, so 1 - 3 = -2. A solution that stores -7 and floors
    # (-7 // 2 = -4) would wrongly return -3.
    assert impl.evaluate("1-7/2") == -2
    assert impl.evaluate("0-3/2") == -1


def test_left_to_right_within_a_level():
    assert impl.evaluate("14-3-2") == 9
    assert impl.evaluate("100/10*3") == 30
    assert impl.evaluate("2*3/4") == 1


def test_multi_digit_numbers():
    assert impl.evaluate("1000*2+30/7") == 2004


def test_error_percentage_query():
    # Production flavour: 5xx percent for the last hour, integer math.
    # errors=37, total=1200: 37*100/1200 = 3 (percent, truncated)
    assert impl.evaluate("37 * 100 / 1200") == 3
    # errors / total * 100 in integer math is 0: order matters, which is why PromQL uses floats.
    assert impl.evaluate("37 / 1200 * 100") == 0
    # (errors + timeouts - retries) rewritten without parentheses: 37 + 12 - 5
    assert impl.evaluate("37 + 12 - 5") == 44


def test_large_random_matches_reference():
    rng = random.Random(227)
    for _ in range(300):
        parts = [str(rng.randint(0, 999))]
        for _ in range(rng.randint(0, 40)):
            op = rng.choice("+-*/")
            n = rng.randint(1, 999) if op == "/" else rng.randint(0, 999)
            parts += [op, str(n)]
        expr = " ".join(parts) if rng.random() < 0.5 else "".join(parts)
        assert impl.evaluate(expr) == reference(expr), expr
