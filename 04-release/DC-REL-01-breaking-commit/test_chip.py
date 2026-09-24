"""Tests for DC-REL-01 Find the Breaking Commit."""
from __future__ import annotations

import random

import pytest
from chip import load_impl

impl = load_impl(__file__)


class CI:
    """A fake CI system: commits >= first_bad fail. Counts every run."""

    def __init__(self, first_bad: int) -> None:
        self.first_bad = first_bad
        self.runs = 0

    def is_bad(self, commit: int) -> bool:
        self.runs += 1
        return commit >= self.first_bad


def run(n: int, first_bad: int) -> tuple[int, int]:
    ci = CI(first_bad)
    return impl.first_bad_commit(n, ci.is_bad), ci.runs


def test_normal_middle_commit():
    assert run(5, 4)[0] == 4


def test_single_commit_is_the_bad_one():
    answer, runs = run(1, 1)
    assert answer == 1
    assert runs <= 1


def test_boundaries_first_and_last():
    assert run(10, 1)[0] == 1    # the very first commit already broke it
    assert run(10, 10)[0] == 10  # only HEAD is bad


def test_run_count_is_logarithmic():
    n = 2**31 - 1
    for first_bad in (1, 2, 1_000_003, n // 2, n - 1, n):
        answer, runs = run(n, first_bad)
        assert answer == first_bad
        assert runs <= n.bit_length()  # ceil(log2 n) CI runs at most: 31 here


def test_release_regression_between_tags():
    # Production flavour: 40 commits between tag v1.27.3 (good) and HEAD (bad).
    # The 23rd commit, "bump grpc to 1.62", broke the integration suite.
    answer, runs = run(40, 23)
    assert answer == 23
    assert runs <= 6  # 40 commits need at most ceil(log2 40) = 6 runs


def test_large_random_matches_linear_scan():
    rng = random.Random(278)
    for _ in range(300):
        n = rng.randint(1, 3_000)
        first_bad = rng.randint(1, n)
        ci = CI(first_bad)
        brute = next(c for c in range(1, n + 1) if ci.is_bad(c))  # linear reference
        answer, runs = run(n, first_bad)
        assert answer == brute
        assert runs <= max(1, n.bit_length())
