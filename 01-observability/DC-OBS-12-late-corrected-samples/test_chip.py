"""Tests for DC-OBS-12 Late & Corrected Samples."""
from __future__ import annotations

import random

import pytest
from chip import load_impl

impl = load_impl(__file__)


@pytest.fixture
def st():
    return impl.SampleTracker()


def test_normal_sequence(st):
    st.update(1, 10.0)
    st.update(2, 5.0)
    assert st.current() == 5.0
    assert st.maximum() == 10.0
    st.update(1, 3.0)  # correction: the 10 never happened
    assert st.maximum() == 5.0
    st.update(4, 2.0)
    assert st.minimum() == 2.0
    assert st.current() == 2.0


def test_single_sample(st):
    st.update(7, 42.0)
    assert st.current() == st.maximum() == st.minimum() == 42.0


def test_late_sample_does_not_change_current(st):
    st.update(100, 1.0)
    st.update(50, 99.0)  # late: older timestamp arrives after a newer one
    assert st.current() == 1.0
    assert st.maximum() == 99.0


def test_correcting_the_latest_changes_current(st):
    st.update(5, 1.0)
    st.update(5, 8.0)
    assert st.current() == 8.0
    assert st.maximum() == st.minimum() == 8.0


def test_repeated_corrections_same_value_back(st):
    # Boundary: a value corrected away and then back must count again.
    st.update(1, 50.0)
    st.update(2, 10.0)
    st.update(1, 0.0)
    st.update(1, 50.0)
    assert st.maximum() == 50.0
    assert st.minimum() == 10.0


def test_exporter_backfill_after_outage(st):
    # Production flavour: a remote-write queue replays 10 minutes of cpu samples late,
    # and one bad reading (a counter reset spike) is later corrected by the exporter.
    t0 = 1_700_000_000
    for i in range(20):
        st.update(t0 + 600 + 15 * i, 0.30)       # live samples after the outage
    for i in range(40):
        st.update(t0 + 15 * i, 0.20)             # backfilled samples from the gap
    st.update(t0 + 150, 9999.0)                  # the spike
    assert st.maximum() == 9999.0
    st.update(t0 + 150, 0.21)                    # the correction
    assert st.maximum() == 0.30
    assert st.minimum() == 0.20
    assert st.current() == 0.30


def test_large_random_matches_brute_force(st):
    rng = random.Random(2034)
    truth: dict[int, float] = {}
    for _ in range(20_000):
        t = rng.randint(1, 2_000)
        v = float(rng.randint(-1_000, 1_000))
        st.update(t, v)
        truth[t] = v
        if rng.random() < 0.05:
            assert st.current() == truth[max(truth)]
            assert st.maximum() == max(truth.values())
            assert st.minimum() == min(truth.values())
