"""Tests for DC-SEC-03 Nested Rule Expander."""
from __future__ import annotations

import random
import re

import pytest
from chip import load_impl

impl = load_impl(__file__)
INNERMOST = re.compile(r"(\d+)\[([^\[\]]*)\]")


def reference(template: str) -> str:
    """Independent reference: rewrite the innermost block until none are left."""
    while True:
        new = INNERMOST.sub(lambda m: m.group(2) * int(m.group(1)), template)
        if new == template:
            return new
        template = new


def test_normal_and_nested():
    assert impl.expand("3[ab]") == "ababab"
    assert impl.expand("2[x3[y]]") == "xyyyxyyy"
    assert impl.expand("port:2[a-]end") == "port:a-a-end"


def test_empty_and_single():
    assert impl.expand("") == ""
    assert impl.expand("a") == "a"
    assert impl.expand("1[a]") == "a"


def test_multi_digit_count_and_zero():
    assert impl.expand("12[z]") == "z" * 12
    assert impl.expand("ab0[cd]ef") == "abef"  # boundary: zero repeats


def test_expansion_bomb_is_refused():
    # 10 levels of 10[...] would be 10^10 characters.
    bomb = "10[" * 10 + "x" + "]" * 10
    with pytest.raises(ValueError):
        impl.expand(bomb)
    # Exactly at the cap is fine; one over is not.
    assert len(impl.expand("100[a]", max_output=100)) == 100
    with pytest.raises(ValueError):
        impl.expand("101[a]", max_output=100)


def test_production_policy_template():
    # A Helm-style template for three regional replicas of the same allow rule.
    tmpl = "allow:2[sqs:SendMessage,]3[vpce-a,]end"
    assert impl.expand(tmpl) == "allow:sqs:SendMessage,sqs:SendMessage,vpce-a,vpce-a,vpce-a,end"


def test_large_random_matches_reference():
    rng = random.Random(394)

    def gen(depth: int) -> str:
        parts = []
        for _ in range(rng.randint(0, 3)):
            if depth < 4 and rng.random() < 0.4:
                parts.append(f"{rng.randint(1, 4)}[{gen(depth + 1)}]")
            else:
                parts.append(rng.choice("abc:-,"))
        return "".join(parts)

    for _ in range(2_000):
        t = gen(0)
        assert impl.expand(t) == reference(t), t
    big = "50[" + "20[ab]" + "]"
    assert impl.expand(big) == "ab" * 1_000
