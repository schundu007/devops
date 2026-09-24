"""Tests for DC-PLAT-07 Round-Robin Load Balancer."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)
busiest = impl.busiest_backends


def brute_force(k: int, arrival: list[int], load: list[int]) -> list[int]:
    """Independent check: scan the backends one by one for every request."""
    free_at = [0] * k
    served = [0] * k
    for i, (t, d) in enumerate(zip(arrival, load)):
        for step in range(k):
            b = (i + step) % k
            if free_at[b] <= t:
                free_at[b] = t + d
                served[b] += 1
                break
    top = max(served)
    return [b for b in range(k) if served[b] == top]


def test_skip_busy_backend():
    # 3 backends. r0->b0 (busy until 10), r1->b1 (until 3), r2->b2 (until 12),
    # r3 at t=3 prefers b0 (busy) and takes b1 (free at exactly 3).
    assert busiest(3, [0, 1, 2, 3], [10, 2, 10, 5]) == [1]


def test_all_busy_drops_request():
    # r2 finds both backends busy and is dropped; the tie stays [0, 1].
    assert busiest(2, [0, 1, 2], [100, 100, 1]) == [0, 1]


def test_single_backend_and_single_request():
    assert busiest(1, [5], [1]) == [0]
    assert busiest(4, [5], [1]) == [0]  # only b0 served anything


def test_all_idle_backends_tie():
    # Short requests: plain round robin, every backend serves the same number.
    assert busiest(3, list(range(9)), [1] * 9) == [0, 1, 2]


def test_wraparound_to_lower_ids():
    # b1 and b2 hold long requests. r4 prefers b1 and r5 prefers b2: both are busy and
    # nothing above them is idle, so each wraps around to b0.
    assert busiest(3, [0, 1, 2, 3, 4, 5], [1, 50, 50, 1, 1, 1]) == [0]


def test_hot_backend_under_long_requests():
    # Production flavour: backend b1 keeps getting the long uploads, so it is busy when
    # its turn comes and its neighbours absorb the extra traffic.
    arrival = list(range(0, 60))
    load = [30 if i % 4 == 1 else 1 for i in range(60)]
    assert busiest(4, arrival, load) == brute_force(4, arrival, load)


def test_large_random_matches_brute_force():
    rng = random.Random(1606)
    for _ in range(30):
        k = rng.randint(1, 12)
        n = rng.randint(1, 300)
        arrival = sorted(rng.sample(range(1, 5 * n), n))
        load = [rng.randint(1, 40) for _ in range(n)]
        assert busiest(k, arrival, load) == brute_force(k, arrival, load)
    k, n = 500, 20_000
    arrival = list(range(1, n + 1))
    load = [rng.randint(1, 2_000) for _ in range(n)]
    assert busiest(k, arrival, load) == brute_force(k, arrival, load)
