"""Tests for DC-PLAT-15 On-Call Coverage Gaps."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)


def brute_force(schedules: list[list[list[int]]]) -> list[list[int]]:
    """Independent reference: mark every covered unit of time, then read off the holes."""
    shifts = [s for person in schedules for s in person]
    if not shifts:
        return []
    lo = min(s for s, _ in shifts)
    hi = max(e for _, e in shifts)
    covered = [False] * (hi - lo)
    for s, e in shifts:
        for t in range(s, e):
            covered[t - lo] = True
    gaps, t = [], 0
    while t < len(covered):
        if covered[t]:
            t += 1
            continue
        start = t
        while t < len(covered) and not covered[t]:
            t += 1
        gaps.append([start + lo, t + lo])
    return gaps


def test_normal_gap_between_engineers():
    schedules = [[[0, 8], [20, 24]], [[6, 12]]]
    assert impl.coverage_gaps(schedules) == [[12, 20]]


def test_empty_inputs():
    assert impl.coverage_gaps([]) == []
    assert impl.coverage_gaps([[], []]) == []


def test_single_engineer():
    assert impl.coverage_gaps([[[0, 4]]]) == []
    assert impl.coverage_gaps([[[0, 4], [6, 9], [9, 10]]]) == [[4, 6]]


def test_touching_shifts_leave_no_gap():
    # Boundary: a handover at exactly 8 and 16 is full coverage.
    assert impl.coverage_gaps([[[0, 8]], [[8, 16]], [[16, 24]]]) == []
    # One unit apart is a real gap.
    assert impl.coverage_gaps([[[0, 8]], [[9, 16]]]) == [[8, 9]]


def test_long_shift_hides_later_short_ones():
    # A 0-100 shift covers everything else; the running max matters, not the last end.
    assert impl.coverage_gaps([[[0, 100]], [[10, 20], [30, 40]], [[101, 110]]]) == [[100, 101]]


def test_follow_the_sun_week():
    # Production flavour: hours of one week (0-168). APAC, EMEA and US each cover
    # 8 h a day, Mon-Fri. The US shift on Friday ends at 120 (Friday 24:00) and
    # the weekend rota was forgotten except Sunday afternoon.
    apac = [[24 * d, 24 * d + 8] for d in range(5)]
    emea = [[24 * d + 8, 24 * d + 16] for d in range(5)]
    us = [[24 * d + 16, 24 * d + 24] for d in range(5)]
    weekend = [[156, 164]]
    assert impl.coverage_gaps([apac, emea, us, weekend]) == [[120, 156]]


def test_large_random_matches_brute_force():
    rng = random.Random(759)
    for _ in range(40):
        schedules = []
        for _ in range(rng.randint(1, 30)):
            t, shifts = rng.randint(0, 50), []
            for _ in range(rng.randint(0, 20)):
                length = rng.randint(1, 40)
                shifts.append([t, t + length])
                t += length + rng.randint(0, 60)
            schedules.append(shifts)
        assert impl.coverage_gaps(schedules) == brute_force(schedules)
