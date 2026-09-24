"""Tests for DC-SEC-06 Tenant Quota Guardrail."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)


def reference_peak(jobs):
    """Independent O(n^2) reference: check the load at every start time."""
    peak = 0
    for _, t, _ in jobs:
        peak = max(peak, sum(v for v, s, e in jobs if s <= t < e))
    return peak


def test_normal_overlap():
    jobs = [(8, 0, 60), (16, 30, 90), (4, 45, 120)]
    assert impl.peak_usage(jobs) == 28
    assert impl.fits_quota(jobs, 28) is True
    assert impl.fits_quota(jobs, 27) is False


def test_empty_and_single():
    assert impl.peak_usage([]) == 0
    assert impl.fits_quota([], 0) is True
    assert impl.fits_quota([(64, 10, 20)], 32) is False


def test_back_to_back_jobs_share_capacity():
    # Boundary: a job ending at t=60 frees its vCPUs for a job starting at t=60.
    jobs = [(32, 0, 60), (32, 60, 120)]
    assert impl.peak_usage(jobs) == 32
    assert impl.fits_quota(jobs, 32) is True


def test_zero_length_job_uses_nothing():
    assert impl.peak_usage([(100, 5, 5), (3, 0, 10)]) == 3


def test_production_nightly_batch_window():
    # Tenant "analytics" has a 96 vCPU quota. Times are minutes after 00:00 UTC.
    jobs = [
        (32, 60, 180),    # etl-orders       01:00-03:00
        (32, 120, 240),   # etl-clickstream  02:00-04:00
        (16, 150, 170),   # reindex-search   02:30-02:50
        (24, 165, 200),   # ml-features      02:45-03:20  <- all four overlap at 02:45
    ]
    assert impl.peak_usage(jobs) == 104
    assert impl.fits_quota(jobs, 96) is False
    moved = jobs[:3] + [(24, 170, 205)]   # start ml-features at 02:50 instead
    assert impl.fits_quota(moved, 96) is True


def test_large_random_matches_reference():
    rng = random.Random(1094)
    for _ in range(200):
        jobs = []
        for _ in range(rng.randint(1, 60)):
            s = rng.randint(0, 500)
            jobs.append((rng.randint(1, 64), s, s + rng.randint(0, 100)))
        assert impl.peak_usage(jobs) == reference_peak(jobs)
    big = [(1, i, i + 1_000_000) for i in range(0, 100_000)]
    assert impl.peak_usage(big) == 100_000
