"""Tests for DC-PLAT-08 Weighted Job Dispatcher."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)
assign = impl.assign_jobs


def brute_force(weights: list[int], durations: list[int]) -> list[int]:
    """Independent check: scan every worker for every job."""
    idle_at = [0] * len(weights)
    out = []
    now = 0
    for j, d in enumerate(durations):
        now = max(now, j)
        if min(idle_at) > now:
            now = min(idle_at)
        best = min((weights[i], i) for i in range(len(weights)) if idle_at[i] <= now)[1]
        idle_at[best] = now + d
        out.append(best)
    return out


def test_cheapest_idle_worker_wins():
    # Worker 1 is cheapest; it takes job 0, and job 1 (at second 1) finds it busy.
    assert assign([3, 1, 2], [2, 2, 1]) == [1, 2, 1]


def test_ties_break_on_lowest_index():
    assert assign([5, 5, 5], [10, 10, 10]) == [0, 1, 2]


def test_job_waits_when_all_busy():
    # One worker: every job waits for the previous one.
    assert assign([7], [3, 1, 4]) == [0, 0, 0]


def test_worker_finishing_at_t_is_idle_at_t():
    # Job 0 runs 0..1 on worker 0 (cheapest). Job 1 is queued at 1: worker 0 is idle again.
    assert assign([1, 9], [1, 1]) == [0, 0]


def test_waiting_job_takes_the_first_finisher_even_if_expensive():
    # At second 2 both workers are busy; worker 1 (expensive) finishes first, at 3.
    assert assign([1, 9], [10, 2, 1]) == [0, 1, 1]


def test_spot_and_on_demand_runners():
    # Production flavour: weights are $/hour (spot runners are cheap), durations in seconds.
    weights = [9, 9, 3, 3]            # 2 on-demand, 2 spot
    durations = [5, 5, 5, 5, 1, 1]
    got = assign(weights, durations)
    assert got[:2] == [2, 3]          # spot first
    assert got == brute_force(weights, durations)


def test_large_random_matches_brute_force():
    rng = random.Random(1882)
    for _ in range(40):
        m = rng.randint(1, 15)
        weights = [rng.randint(1, 10) for _ in range(m)]
        durations = [rng.randint(1, 30) for _ in range(rng.randint(1, 200))]
        assert assign(weights, durations) == brute_force(weights, durations)
    weights = [rng.randint(1, 1_000) for _ in range(300)]
    durations = [rng.randint(1, 800) for _ in range(20_000)]
    assert assign(weights, durations) == brute_force(weights, durations)
