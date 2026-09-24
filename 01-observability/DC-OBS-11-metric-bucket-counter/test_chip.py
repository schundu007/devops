"""Tests for DC-OBS-11 Metric Bucket Counter."""
from __future__ import annotations

import random

import pytest
from chip import load_impl

impl = load_impl(__file__)
T0 = 1_700_000_000  # synthetic epoch second


@pytest.fixture
def ec():
    return impl.EventCounter()


def test_minute_buckets(ec):
    for t in (0, 60, 10):
        ec.record("deploy", t)
    assert ec.counts("minute", "deploy", 0, 59) == [2]
    assert ec.counts("minute", "deploy", 0, 60) == [2, 1]  # last bucket is just second 60
    ec.record("deploy", 120)
    assert ec.counts("hour", "deploy", 0, 210) == [4]


def test_unknown_name_gives_zero_buckets(ec):
    assert ec.counts("minute", "oom_kill", 0, 179) == [0, 0, 0]


def test_single_second_range(ec):
    ec.record("oom_kill", 5)
    assert ec.counts("day", "oom_kill", 5, 5) == [1]
    assert ec.counts("minute", "oom_kill", 6, 6) == [0]


def test_buckets_align_to_start_and_ends_are_inclusive(ec):
    for t in (100, 159, 160, 219, 220):
        ec.record("5xx", t)
    # Buckets: [100,159] [160,219] [220,220]
    assert ec.counts("minute", "5xx", 100, 220) == [2, 2, 1]
    # Shift the start by one second and the buckets move with it: [101,160] [161,218].
    # 100 and 219/220 fall outside [start, end] and are ignored.
    assert ec.counts("minute", "5xx", 101, 218) == [2, 0]


def test_out_of_order_and_duplicate_times(ec):
    for t in (300, 5, 300, 61, 5):
        ec.record("restart", t)
    assert ec.counts("minute", "restart", 0, 359) == [2, 1, 0, 0, 0, 2]


def test_zoom_out_dashboard(ec):
    # Production flavour: pod restarts across one day, viewed per hour then per day.
    restarts = [T0 + h * 3600 + m for h, m in [(0, 5), (0, 50), (3, 0), (23, 59)]]
    for t in restarts:
        ec.record("kube_pod_restarts{pod=\"api-6c9f8-lq2xz\"}", t)
    hourly = ec.counts("hour", "kube_pod_restarts{pod=\"api-6c9f8-lq2xz\"}", T0, T0 + 86399)
    assert len(hourly) == 24 and hourly[0] == 2 and hourly[3] == 1 and hourly[23] == 1
    assert sum(hourly) == 4
    assert ec.counts("day", "kube_pod_restarts{pod=\"api-6c9f8-lq2xz\"}", T0, T0 + 86399) == [4]


def test_large_random_matches_brute_force(ec):
    rng = random.Random(1348)
    times = [rng.randint(0, 500_000) for _ in range(20_000)]
    for t in times:
        ec.record("evt", t)
    for _ in range(50):
        step = rng.choice(["minute", "hour", "day"])
        size = impl.BUCKET_SECONDS[step]
        a = rng.randint(0, 400_000)
        b = a + rng.randint(0, 100_000)
        expected = [0] * ((b - a) // size + 1)
        for t in times:
            if a <= t <= b:
                expected[(t - a) // size] += 1
        assert ec.counts(step, "evt", a, b) == expected
