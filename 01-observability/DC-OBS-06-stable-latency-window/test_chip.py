"""Tests for DC-OBS-06 Longest Stable Latency Window."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)
f = impl.longest_stable_window


def brute_force(xs: list[int], limit: int) -> int:
    best = 0
    for i in range(len(xs)):
        lo = hi = xs[i]
        for j in range(i, len(xs)):
            lo, hi = min(lo, xs[j]), max(hi, xs[j])
            if hi - lo > limit:
                break
            best = max(best, j - i + 1)
    return best


def test_normal():
    assert f([120, 125, 118, 300, 310, 305, 122], 10) == 3


def test_empty_and_single():
    assert f([], 5) == 0
    assert f([250], 0) == 1


def test_limit_zero_needs_equal_values():
    # Boundary: limit 0 means the band has no width at all.
    assert f([40, 40, 41, 41, 41, 40], 0) == 3


def test_band_edge_is_inclusive():
    # Boundary: max - min == limit is still stable.
    assert f([100, 110, 100, 111], 10) == 3


def test_calm_period_before_incident():
    # Production flavour: p99 of checkout-api, one sample per minute. Latency sat
    # in 180-195 ms for 45 minutes, then climbed as the DB connection pool filled.
    calm = [180 + (i * 7) % 16 for i in range(45)]          # values in 180..195
    incident = [210, 260, 340, 520, 900, 1400, 1450, 1420]
    series = [400, 380] + calm + incident
    assert f(series, 15) == 45


def test_large_random_matches_brute_force():
    rng = random.Random(1438)
    for _ in range(30):
        xs = [rng.randint(0, 50) for _ in range(rng.randint(0, 400))]
        limit = rng.randint(0, 20)
        assert f(xs, limit) == brute_force(xs, limit)
    big = [rng.randint(90, 130) for _ in range(100_000)]
    assert f(big, 40) == 100_000   # the whole series fits in a 40 ms band
