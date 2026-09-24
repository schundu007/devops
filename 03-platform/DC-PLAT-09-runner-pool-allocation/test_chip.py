"""Tests for DC-PLAT-09 Runner Pool Allocation."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)


def brute_force(n: int, jobs: list[list[int]]) -> int:
    """Independent reference: scan every runner for every job, O(n) per job."""
    free_at = [0] * n
    ran = [0] * n
    for start, end in sorted(jobs):
        idle = [r for r in range(n) if free_at[r] <= start]
        if idle:
            r = min(idle)
            free_at[r] = end
        else:
            r = min(range(n), key=lambda x: (free_at[x], x))
            free_at[r] += end - start
        ran[r] += 1
    best = max(ran)
    return ran.index(best)


def test_normal_three_runners():
    # runner-1 picks up three short jobs while runner-0 and runner-2 hold long ones.
    jobs = [[0, 5], [1, 2], [2, 4], [3, 9], [4, 6], [6, 7]]
    assert impl.busiest_runner(3, jobs) == 1


def test_empty_and_single():
    assert impl.busiest_runner(4, []) == 0
    assert impl.busiest_runner(1, [[10, 20]]) == 0
    assert impl.busiest_runner(3, [[10, 20]]) == 0  # lowest idle runner wins


def test_delayed_job_goes_to_first_free_runner():
    # Both runners busy at t=2; runner-0 frees first (t=10), so the job runs 10-12 there.
    assert impl.busiest_runner(2, [[0, 10], [1, 11], [2, 4]]) == 0


def test_free_at_exactly_start_counts_as_idle():
    # Boundary: runner-0 ends at 5 and the next job is queued at 5.
    assert impl.busiest_runner(2, [[0, 5], [5, 6], [6, 7]]) == 0


def test_tie_goes_to_lower_runner():
    # Two runners, two jobs each -> runner-0 wins the tie.
    jobs = [[0, 10], [1, 10], [20, 30], [21, 30]]
    assert impl.busiest_runner(2, jobs) == 0


def test_nightly_batch_on_small_pool():
    # Production flavour: 3 self-hosted runners, a nightly burst of 12 builds
    # queued one minute apart, each 10 minutes long. From build 4 on, every build
    # waits for the runner that frees first, so work rotates 0,1,2,0,1,2...:
    # 4 builds each, and the tie goes to runner-0.
    jobs = [[m, m + 10] for m in range(12)]
    assert impl.busiest_runner(3, jobs) == brute_force(3, jobs) == 0
    # One extra quick build at minute 50 (all idle) lands on runner-0: 5 vs 4 vs 4.
    assert impl.busiest_runner(3, jobs + [[50, 51]]) == 0
    # A build queued at 39 waits for runner-0 (free at 40, busy until 61), so the
    # quick build at 45 lands on runner-1 (free at 41): 5 vs 5 vs 4, tie -> runner-0.
    assert impl.busiest_runner(3, jobs + [[39, 60], [45, 46]]) == 0


def test_large_random_matches_brute_force():
    rng = random.Random(2402)
    for _ in range(20):
        n = rng.randint(1, 30)
        starts = rng.sample(range(0, 50_000), 1_500)
        jobs = [[s, s + rng.randint(1, 400)] for s in starts]
        assert impl.busiest_runner(n, jobs) == brute_force(n, jobs)
