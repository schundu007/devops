"""Tests for DC-OBS-01 Metric Point-in-Time Lookup."""
from __future__ import annotations

import random

import pytest
from chip import load_impl

impl = load_impl(__file__)
T0 = 1_700_000_000  # an epoch second; all data here is synthetic


@pytest.fixture
def store():
    return impl.MetricStore()


def test_normal_lookup_between_samples(store):
    store.record("cpu_usage", 0.42, T0)
    store.record("cpu_usage", 0.87, T0 + 15)
    assert store.value_at("cpu_usage", T0 + 10) == 0.42
    assert store.value_at("cpu_usage", T0 + 15) == 0.87  # exact match wins
    assert store.value_at("cpu_usage", T0 + 999) == 0.87  # after the last sample


def test_unknown_metric_and_empty_store(store):
    assert store.value_at("cpu_usage", T0) is None
    store.record("mem_bytes", 1024.0, T0)
    assert store.value_at("cpu_usage", T0) is None


def test_before_first_sample_is_none(store):
    store.record("cpu_usage", 0.5, T0)
    assert store.value_at("cpu_usage", T0 - 1) is None
    assert store.value_at("cpu_usage", T0) == 0.5  # boundary: exactly the first sample


def test_zero_value_is_a_real_answer(store):
    # A falsy value must not be confused with "no sample".
    store.record("queue_depth", 0.0, T0)
    assert store.value_at("queue_depth", T0 + 5) == 0.0


def test_metrics_are_independent(store):
    store.record("cpu_usage", 0.1, T0)
    store.record("mem_bytes", 5e8, T0 + 30)
    store.record("cpu_usage", 0.9, T0 + 60)
    assert store.value_at("mem_bytes", T0 + 59) == 5e8
    assert store.value_at("cpu_usage", T0 + 59) == 0.1
    assert store.value_at("mem_bytes", T0 + 29) is None


def test_scrape_gap_returns_last_known_value(store):
    # Production flavour: node-exporter on ip-10-0-3-17 scrapes every 15 s,
    # then the node reboots and the scrape misses 10:05:00-10:12:00.
    # A dashboard at 10:08:30 sees the last value before the gap.
    t_1005 = T0 + 5 * 60
    for i in range(20):
        store.record("node_cpu{instance=\"10.0.3.17\"}", float(i), t_1005 - 300 + 15 * i)
    store.record("node_cpu{instance=\"10.0.3.17\"}", 99.0, t_1005 + 7 * 60)
    assert store.value_at("node_cpu{instance=\"10.0.3.17\"}", t_1005 + 3 * 60 + 30) == 19.0
    assert store.value_at("node_cpu{instance=\"10.0.3.17\"}", t_1005 + 7 * 60) == 99.0


def test_large_input_matches_brute_force(store):
    rng = random.Random(7)
    times: list[int] = []
    t = T0
    for _ in range(100_000):
        t += rng.randint(1, 30)
        times.append(t)
        store.record("cpu_usage", float(t % 97), t)
    queries = sorted(rng.randint(T0 - 10, t + 10) for _ in range(5_000))
    # Independent reference: one linear sweep over samples and sorted queries.
    j, last = 0, None
    for q in queries:
        while j < len(times) and times[j] <= q:
            last = float(times[j] % 97)
            j += 1
        assert store.value_at("cpu_usage", q) == last
