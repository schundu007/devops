"""Tests for DC-OBS-16 Error Budget Window."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)


def brute(checks: list[int], budget: int) -> int:
    best = 0
    for i in range(len(checks)):
        fails = 0
        for j in range(i, len(checks)):
            fails += checks[j] == 0
            if fails > budget:
                break
            best = max(best, j - i + 1)
    return best


def test_normal():
    assert impl.longest_window([1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0], 2) == 6


def test_empty_and_single():
    assert impl.longest_window([], 3) == 0
    assert impl.longest_window([0], 0) == 0
    assert impl.longest_window([1], 0) == 1


def test_zero_budget_is_longest_all_pass_run():
    assert impl.longest_window([1, 0, 1, 1, 1, 0, 1, 1], 0) == 3


def test_budget_covers_everything():
    # Boundary: budget >= total failures means the whole series fits.
    checks = [0, 1, 0, 1, 0]
    assert impl.longest_window(checks, 3) == 5
    assert impl.longest_window(checks, 2) == 4


def test_all_failures():
    assert impl.longest_window([0, 0, 0, 0], 1) == 1


def test_synthetic_probe_error_budget():
    # Production flavour: a blackbox probe every 30 s for 2 hours (240 checks). With a
    # budget of 4 failed probes, how long can we go? A 6-probe outage sits at 100-105.
    checks = [1] * 240
    for i in (20, 60, 100, 101, 102, 103, 104, 105, 180, 220):
        checks[i] = 0
    # Budget 4: best window is 104..239, holding failures 104, 105, 180 and 220.
    assert impl.longest_window(checks, 4) == 240 - 104
    # Budget 2: best window is 106..239, after the outage, holding 180 and 220.
    assert impl.longest_window(checks, 2) == 240 - 106


def test_large_random_matches_brute_force():
    rng = random.Random(1004)
    for _ in range(30):
        n = rng.randint(0, 300)
        checks = [1 if rng.random() < 0.8 else 0 for _ in range(n)]
        budget = rng.randint(0, 10)
        assert impl.longest_window(checks, budget) == brute(checks, budget)
    big = [1 if rng.random() < 0.9 else 0 for _ in range(3_000)]
    assert impl.longest_window(big, 50) == brute(big, 50)
