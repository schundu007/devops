"""Tests for DC-SEC-10 Allow-List Range Tracker."""
from __future__ import annotations

import ipaddress
import random

from chip import load_impl

impl = load_impl(__file__)


def test_add_remove_split_and_query():
    a = impl.AllowList()
    a.add(10, 20)
    a.remove(14, 16)                       # removing from the middle splits the range
    assert a.ranges() == [(10, 14), (16, 20)]
    assert a.covers(10, 14) is True
    assert a.covers(13, 17) is False
    assert a.covers(16, 20) is True


def test_empty_and_single():
    a = impl.AllowList()
    assert a.ranges() == []
    assert a.covers(0, 1) is False
    a.remove(0, 100)                        # removing from nothing is fine
    assert a.ranges() == []
    a.add(5, 6)
    assert a.covers(5, 6) is True and a.covers(4, 6) is False


def test_half_open_boundaries_and_touching_ranges():
    a = impl.AllowList()
    a.add(10, 20)
    assert a.covers(19, 20) is True
    assert a.covers(20, 21) is False       # hi is not included
    a.add(20, 30)                           # touches: becomes one range
    assert a.ranges() == [(10, 30)]
    a.remove(10, 30)
    assert a.ranges() == []


def test_add_spanning_many_ranges():
    a = impl.AllowList()
    for lo in range(0, 100, 10):
        a.add(lo, lo + 5)
    a.add(3, 77)
    assert a.ranges() == [(0, 77), (80, 85), (90, 95)]


def test_production_port_and_ip_allow_list():
    ports = impl.AllowList()
    ports.add(8000, 8101)                   # app ports 8000-8100
    ports.remove(8080, 8082)                # close the debug ports 8080-8081
    assert ports.covers(8000, 8080) is True
    assert ports.covers(8079, 8081) is False
    assert ports.ranges() == [(8000, 8080), (8082, 8101)]
    # IP ranges as integers: allow 10.0.0.0/24, then revoke 10.0.0.128/26.
    ips = impl.AllowList()
    net = ipaddress.ip_network("10.0.0.0/24")
    bad = ipaddress.ip_network("10.0.0.128/26")
    ips.add(int(net.network_address), int(net.broadcast_address) + 1)
    ips.remove(int(bad.network_address), int(bad.broadcast_address) + 1)
    probe = int(ipaddress.ip_address("10.0.0.130"))
    assert ips.covers(probe, probe + 1) is False
    assert ips.covers(int(ipaddress.ip_address("10.0.0.200")), int(ipaddress.ip_address("10.0.0.201"))) is True
    assert len(ips.ranges()) == 2


def test_large_random_matches_set():
    rng = random.Random(715)
    a = impl.AllowList()
    allowed: set[int] = set()   # independent reference over a small universe
    for _ in range(4_000):
        lo = rng.randint(0, 300)
        hi = lo + rng.randint(1, 40)
        op = rng.random()
        if op < 0.4:
            a.add(lo, hi)
            allowed.update(range(lo, hi))
        elif op < 0.7:
            a.remove(lo, hi)
            allowed.difference_update(range(lo, hi))
        else:
            assert a.covers(lo, hi) is all(x in allowed for x in range(lo, hi))
    flat = {x for s, e in a.ranges() for x in range(s, e)}
    assert flat == allowed
    spans = a.ranges()
    assert all(spans[k][1] < spans[k + 1][0] for k in range(len(spans) - 1))  # disjoint, not touching
