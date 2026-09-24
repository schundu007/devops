"""Tests for DC-OBS-13 Hop-to-Hop Average Latency."""
from __future__ import annotations

import random

import pytest
from chip import load_impl

impl = load_impl(__file__)


@pytest.fixture
def h():
    return impl.HopLatency()


def test_normal_average(h):
    h.enter("r1", "gateway", 3)
    h.enter("r2", "gateway", 8)
    h.exit("r1", "orders", 15)   # 12
    h.exit("r2", "orders", 20)   # 12
    assert h.average("gateway", "orders") == pytest.approx(12.0)
    h.enter("r3", "gateway", 21)
    h.exit("r3", "orders", 39)   # 18
    assert h.average("gateway", "orders") == pytest.approx(14.0)


def test_single_hop(h):
    h.enter("a", "cart", 100)
    h.exit("a", "payments", 101)
    assert h.average("cart", "payments") == pytest.approx(1.0)


def test_direction_matters(h):
    h.enter("a", "x", 0)
    h.exit("a", "y", 10)
    h.enter("b", "y", 0)
    h.exit("b", "x", 30)
    assert h.average("x", "y") == pytest.approx(10.0)
    assert h.average("y", "x") == pytest.approx(30.0)


def test_request_id_reused_after_exit(h):
    # Boundary: the same id can start a new hop once the old one closes.
    h.enter("r", "a", 1)
    h.exit("r", "b", 5)
    h.enter("r", "b", 10)
    h.exit("r", "c", 13)
    assert h.average("a", "b") == pytest.approx(4.0)
    assert h.average("b", "c") == pytest.approx(3.0)


def test_open_hops_do_not_count(h):
    h.enter("done", "api", 0)
    h.exit("done", "db", 7)
    h.enter("stuck", "api", 1)  # never exits (a hung request)
    assert h.average("api", "db") == pytest.approx(7.0)


def test_trace_spans_between_services(h):
    # Production flavour: spans from checkout -> inventory, timed in ms.
    spans = [("t-01", 1000, 1042), ("t-02", 1003, 1051), ("t-03", 1010, 1290), ("t-04", 1011, 1050)]
    for trace, start, end in spans:
        h.enter(trace, "checkout", start)
    for trace, start, end in reversed(spans):  # exits arrive out of order
        h.exit(trace, "inventory", end)
    assert h.average("checkout", "inventory") == pytest.approx((42 + 48 + 280 + 39) / 4)


def test_large_random_matches_brute_force(h):
    rng = random.Random(1396)
    services = [f"svc-{i}" for i in range(6)]
    done: dict[tuple[str, str], list[int]] = {}
    open_: dict[str, tuple[str, int]] = {}
    t = 0
    for i in range(30_000):
        t += rng.randint(0, 3)
        rid = f"r{rng.randint(0, 500)}"
        if rid in open_:
            s, t0 = open_.pop(rid)
            e = rng.choice(services)
            h.exit(rid, e, t + 1)
            done.setdefault((s, e), []).append(t + 1 - t0)
        else:
            s = rng.choice(services)
            h.enter(rid, s, t)
            open_[rid] = (s, t)
    for (s, e), durations in done.items():
        assert h.average(s, e) == pytest.approx(sum(durations) / len(durations))
