"""Tests for DC-SEC-15 Impossible Travel Detector."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)


def brute(events: list[str]) -> list[str]:
    # Independent reference: compare every pair of events.
    rows = [e.split(",") for e in events]
    out = []
    for i, (u, t, r, c) in enumerate(rows):
        bad = int(r) > 1000 or any(
            j != i and u2 == u and c2 != c and abs(int(t2) - int(t)) <= 60
            for j, (u2, t2, _r2, c2) in enumerate(rows)
        )
        if bad:
            out.append(events[i])
    return out


def test_normal_two_cities_close_in_time():
    events = ["ana,20,100,berlin", "ana,50,100,tokyo"]
    assert impl.flag_events(events) == events


def test_empty_and_single():
    assert impl.flag_events([]) == []
    assert impl.flag_events(["ana,0,10,berlin"]) == []


def test_window_boundary_is_inclusive():
    assert impl.flag_events(["ana,0,1,berlin", "ana,60,1,tokyo"]) == ["ana,0,1,berlin", "ana,60,1,tokyo"]
    assert impl.flag_events(["ana,0,1,berlin", "ana,61,1,tokyo"]) == []


def test_risk_over_limit_alone():
    assert impl.flag_events(["bo,5,1001,oslo", "bo,6,1000,oslo"]) == ["bo,5,1001,oslo"]


def test_same_city_and_other_users_do_not_trigger():
    events = ["ana,0,1,berlin", "ana,10,1,berlin", "bo,5,1,tokyo"]
    assert impl.flag_events(events) == []


def test_production_vpn_login_burst():
    # svc-deploy logs in from Frankfurt, then from Sao Paulo 25 minutes later.
    # The Frankfurt login 3 hours earlier is clean. Output keeps input order.
    events = [
        "svc-deploy,480,120,frankfurt",
        "jo,500,50,dublin",
        "svc-deploy,660,120,frankfurt",
        "svc-deploy,685,300,saopaulo",
        "jo,900,1500,dublin",
    ]
    assert impl.flag_events(events) == [
        "svc-deploy,660,120,frankfurt",
        "svc-deploy,685,300,saopaulo",
        "jo,900,1500,dublin",
    ]


def test_large_random_matches_brute_force():
    rng = random.Random(1169)
    users = ["ana", "bo", "cy", "di"]
    cities = ["berlin", "tokyo", "lima"]
    events = [
        f"{rng.choice(users)},{rng.randint(0, 3000)},{rng.randint(0, 1100)},{rng.choice(cities)}"
        for _ in range(1_500)
    ]
    assert impl.flag_events(events) == brute(events)
