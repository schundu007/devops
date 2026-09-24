"""Tests for DC-OBS-10 Log Time-Range Query."""
from __future__ import annotations

import random

import pytest
from chip import load_impl

impl = load_impl(__file__)
FIELDS = ["Year", "Month", "Day", "Hour", "Minute", "Second"]


@pytest.fixture
def store():
    s = impl.LogStore()
    s.put(1, "2026:09:23:02:14:05")
    s.put(2, "2026:09:23:02:59:59")
    s.put(3, "2026:09:22:23:00:00")
    s.put(4, "2025:12:31:23:59:59")
    return s


def brute_force(entries, start, end, granularity):
    # Independent reference: compare field by field as integer tuples.
    k = FIELDS.index(granularity) + 1

    def cut(ts):
        return tuple(int(x) for x in ts.split(":")[:k])

    lo, hi = cut(start), cut(end)
    return sorted(i for i, parts in entries if lo <= parts[:k] <= hi)


def test_normal_hour_range(store):
    assert store.retrieve("2026:09:23:02:00:00", "2026:09:23:02:00:00", "Hour") == [1, 2]


def test_empty_store():
    assert impl.LogStore().retrieve("2000:01:01:00:00:00", "2099:12:31:23:59:59", "Year") == []


def test_granularity_ignores_finer_fields(store):
    # start/end minutes and seconds do not matter at Day granularity.
    assert store.retrieve("2026:09:22:23:59:59", "2026:09:23:00:00:00", "Day") == [1, 2, 3]
    assert store.retrieve("2025:01:01:00:00:00", "2025:01:01:00:00:00", "Year") == [4]


def test_second_boundaries_are_inclusive(store):
    assert store.retrieve("2026:09:23:02:14:05", "2026:09:23:02:59:59", "Second") == [1, 2]
    assert store.retrieve("2026:09:23:02:14:06", "2026:09:23:02:59:58", "Second") == []


def test_incident_window_across_midnight_and_year_end(store):
    # Production flavour: an incident ran from 23:00 on New Year's Eve into January.
    store.put(10, "2025:12:31:23:30:00")
    store.put(11, "2026:01:01:00:15:00")
    store.put(12, "2026:01:01:01:00:00")
    assert store.retrieve("2025:12:31:23:00:00", "2026:01:01:00:59:59", "Minute") == [4, 10, 11]


def test_large_random_matches_brute_force():
    rng = random.Random(635)
    s = impl.LogStore()
    entries = []

    def rand_ts():
        return "%04d:%02d:%02d:%02d:%02d:%02d" % (
            rng.randint(2024, 2026), rng.randint(1, 12), rng.randint(1, 28),
            rng.randint(0, 23), rng.randint(0, 59), rng.randint(0, 59))

    for i in range(20_000):
        ts = rand_ts()
        s.put(i, ts)
        entries.append((i, tuple(int(x) for x in ts.split(":"))))  # parsed once
    for _ in range(200):
        a, b = sorted([rand_ts(), rand_ts()])
        g = rng.choice(FIELDS)
        assert s.retrieve(a, b, g) == brute_force(entries, a, b, g)
