"""Tests for DC-SEC-20 Nested Config Parser."""
from __future__ import annotations

import json
import random

import pytest
from chip import load_impl

impl = load_impl(__file__)


def gen(rng: random.Random, depth: int) -> object:
    if depth == 0 or rng.random() < 0.3:
        return rng.randint(-10**6, 10**6)
    return [gen(rng, depth - 1) for _ in range(rng.randint(0, 4))]


def dump(v: object) -> str:
    return json.dumps(v, separators=(",", ":"))


def test_normal_nested_list():
    assert impl.parse("[123,[456,[789]]]") == [123, [456, [789]]]


def test_bare_integers_and_empty_list():
    assert impl.parse("324") == 324
    assert impl.parse("-7") == -7
    assert impl.parse("[]") == []
    assert impl.parse("[[],[]]") == [[], []]


def test_negative_numbers_and_zero():
    assert impl.parse("[-1,0,[-20]]") == [-1, 0, [-20]]


def test_depth_limit_boundary():
    assert impl.parse("[[[1]]]", max_depth=3) == [[[1]]]
    with pytest.raises(ValueError):
        impl.parse("[[[1]]]", max_depth=2)
    assert impl.parse("5", max_depth=0) == 5


def test_deep_nesting_attack_is_refused_fast():
    # 100,000 levels: a recursive parser would hit Python's recursion limit.
    payload = "[" * 100_000 + "]" * 100_000
    with pytest.raises(ValueError):
        impl.parse(payload)
    # With a high enough limit it must still work, iteratively.
    assert impl.parse("[" * 5_000 + "]" * 5_000, max_depth=5_000) is not None


def test_production_policy_rule_tree():
    # Port groups for a fake network policy: [[80,443],[8080,[9000,9001]],[]]
    assert impl.parse("[[80,443],[8080,[9000,9001]],[]]") == [[80, 443], [8080, [9000, 9001]], []]


def test_large_random_matches_json_loads():
    rng = random.Random(385)
    for _ in range(300):
        v = gen(rng, rng.randint(0, 8))
        assert impl.parse(dump(v)) == json.loads(dump(v))
    big = [gen(rng, 3) for _ in range(5_000)]
    assert impl.parse(dump(big)) == big
