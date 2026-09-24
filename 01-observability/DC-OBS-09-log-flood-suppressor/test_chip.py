"""Tests for DC-OBS-09 Log Flood Suppressor."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)


def test_normal_sequence():
    s = impl.LogSuppressor()
    calls = [(1, "db timeout"), (2, "cache miss"), (3, "db timeout"),
             (8, "cache miss"), (10, "db timeout"), (11, "db timeout")]
    assert [s.should_print(t, m) for t, m in calls] == [True, True, False, False, False, True]


def test_first_message_always_prints():
    s = impl.LogSuppressor()
    assert s.should_print(0, "boot") is True


def test_window_edge_is_exactly_window_seconds():
    # Boundary: printed at 100, suppressed at 109, printed again at 110.
    s = impl.LogSuppressor(window=10)
    assert s.should_print(100, "disk 91% full")
    assert not s.should_print(109, "disk 91% full")
    assert s.should_print(110, "disk 91% full")


def test_suppressed_calls_do_not_extend_the_quiet_period():
    # A message repeated every second still prints once per window, not never.
    s = impl.LogSuppressor(window=10)
    printed = [t for t in range(0, 35) if s.should_print(t, "retrying upstream")]
    assert printed == [0, 10, 20, 30]


def test_same_second_burst_and_different_messages():
    # Production flavour: 5,000 identical "connection refused" lines in one second
    # from pod api-6f7c9-lq2xd, mixed with one different error.
    s = impl.LogSuppressor(window=10)
    msg = "dial tcp 10.0.12.7:5432: connect: connection refused"
    out = [s.should_print(1_700_000_000, msg) for _ in range(5_000)]
    assert out.count(True) == 1
    assert s.should_print(1_700_000_000, "OOMKilled: container api") is True


def test_large_random_matches_brute_force():
    rng = random.Random(359)
    window = rng.randint(1, 30)
    s = impl.LogSuppressor(window=window)
    last_print: dict[str, int] = {}
    t = 0
    for _ in range(100_000):
        t += rng.choice([0, 0, 1, 1, 2, 5, 13])
        msg = f"err-{rng.randint(0, 40)}"
        # Independent reference: a message may print if its last print is >= window ago.
        expected = msg not in last_print or t - last_print[msg] >= window
        if expected:
            last_print[msg] = t
        assert s.should_print(t, msg) is expected
