"""Tests for DC-SEC-16 Brute-Force Burst Alert."""
from __future__ import annotations

import random
from itertools import combinations

from chip import load_impl

impl = load_impl(__file__)


def brute(names: list[str], times: list[str]) -> list[str]:
    # Independent reference: try every triple of one name's uses.
    def mins(s: str) -> int:
        return int(s[:2]) * 60 + int(s[3:])
    out = set()
    for name in set(names):
        ts = [mins(t) for n, t in zip(names, times) if n == name]
        if any(max(c) - min(c) <= 60 for c in combinations(ts, 3)):
            out.add(name)
    return sorted(out)


def test_normal_three_in_an_hour():
    names = ["svc-ci"] * 3 + ["bo"] * 2
    times = ["10:00", "10:40", "10:59", "09:00", "09:05"]
    assert impl.burst_alerts(names, times) == ["svc-ci"]


def test_empty_and_single():
    assert impl.burst_alerts([], []) == []
    assert impl.burst_alerts(["ana"], ["00:00"]) == []


def test_one_hour_boundary():
    assert impl.burst_alerts(["a"] * 3, ["10:00", "10:30", "11:00"]) == ["a"]
    assert impl.burst_alerts(["a"] * 3, ["10:00", "10:30", "11:01"]) == []


def test_unsorted_input_and_duplicate_times():
    assert impl.burst_alerts(["a"] * 3, ["23:59", "23:59", "23:10"]) == ["a"]


def test_spread_out_uses_do_not_alert():
    names = ["a"] * 4
    times = ["01:00", "01:50", "02:51", "03:40"]  # every triple spans > 60 min
    assert impl.burst_alerts(names, times) == []


def test_production_password_spray():
    # Failed logins per account in the auth log; only admin gets 3 inside an hour.
    names = ["admin", "backup", "admin", "deploy", "admin", "backup", "backup"]
    times = ["02:10", "02:11", "02:40", "02:12", "03:05", "05:00", "07:30"]
    assert impl.burst_alerts(names, times) == ["admin"]


def test_large_random_matches_brute_force():
    rng = random.Random(1604)
    names = [rng.choice(["ana", "bo", "cy", "di", "ed", "fi"]) for _ in range(240)]
    times = [f"{rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}" for _ in names]
    assert impl.burst_alerts(names, times) == brute(names, times)
    big_names = [f"u{i % 5000}" for i in range(100_000)]
    big_times = [f"{rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}" for _ in big_names]
    # Independent check at scale: count uses in [t, t + 60] with bisect.
    from bisect import bisect_right
    per: dict[str, list[int]] = {}
    for n, t in zip(big_names, big_times):
        per.setdefault(n, []).append(int(t[:2]) * 60 + int(t[3:]))
    want = []
    for n, ts in per.items():
        ts.sort()
        if any(bisect_right(ts, x + 60) - i >= 3 for i, x in enumerate(ts)):
            want.append(n)
    want.sort()
    assert impl.burst_alerts(big_names, big_times) == want
