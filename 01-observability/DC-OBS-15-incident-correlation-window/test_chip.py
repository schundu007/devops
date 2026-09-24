"""Tests for DC-OBS-15 Incident Correlation Window."""
from __future__ import annotations

import random
from bisect import bisect_left

from chip import load_impl

impl = load_impl(__file__)


def brute(error_times: list[list[int]]) -> list[int]:
    # Independent reference: try every error time as a window start, and for each
    # service take its first error at or after that start.
    best = None
    for start in sorted({t for times in error_times for t in times}):
        ends = []
        for times in error_times:
            i = bisect_left(times, start)
            if i == len(times):
                break
            ends.append(times[i])
        else:
            cand = [start, max(ends)]
            if best is None or cand[1] - cand[0] < best[1] - best[0]:
                best = cand
    return best


def test_normal_three_services():
    errs = [[4, 10, 15, 24, 26], [0, 9, 12, 20], [5, 18, 22, 30]]
    assert impl.tightest_window(errs) == [20, 24]


def test_single_service_is_one_point():
    assert impl.tightest_window([[7, 9, 40]]) == [7, 7]


def test_all_services_fail_at_the_same_second():
    assert impl.tightest_window([[1, 50], [2, 50], [50, 60]]) == [50, 50]


def test_tie_goes_to_earlier_window():
    # Boundary: [1, 3] and [10, 12] are both width 2.
    assert impl.tightest_window([[1, 10], [3, 12]]) == [1, 3]


def test_single_error_each():
    assert impl.tightest_window([[100], [5], [42]]) == [5, 100]


def test_db_failover_correlation():
    # Production flavour: error seconds (after 03:40:00) for three services during a failover.
    orders = [12, 95, 96, 97, 310]
    payments = [40, 98, 99, 400]
    search = [3, 101, 500]
    # orders, payments and search all error within 95..101: the failover at ~95 s.
    assert impl.tightest_window([orders, payments, search]) == [97, 101]


def test_large_random_matches_brute_force():
    rng = random.Random(632)
    for _ in range(40):
        k = rng.randint(1, 6)
        errs = [sorted(rng.sample(range(0, 3_000), rng.randint(1, 60))) for _ in range(k)]
        assert impl.tightest_window(errs) == brute(errs)
