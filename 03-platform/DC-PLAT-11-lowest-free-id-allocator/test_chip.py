"""Tests for DC-PLAT-11 Lowest Free ID Allocator."""
from __future__ import annotations

import random

import pytest
from chip import load_impl

impl = load_impl(__file__)


def test_hands_out_in_order_then_reuses_lowest():
    a = impl.IdAllocator(5)
    assert [a.allocate() for _ in range(3)] == [0, 1, 2]
    a.release(1)
    a.release(0)
    assert a.allocate() == 0  # lowest released first
    assert a.allocate() == 1
    assert a.allocate() == 3  # then never-used IDs


def test_empty_pool_and_single_id():
    empty = impl.IdAllocator(0)
    assert empty.allocate() is None
    one = impl.IdAllocator(1)
    assert one.allocate() == 0
    assert one.allocate() is None  # boundary: exhausted
    one.release(0)
    assert one.allocate() == 0


def test_double_release_and_foreign_id_are_rejected():
    a = impl.IdAllocator(3)
    x = a.allocate()
    a.release(x)
    with pytest.raises(ValueError):
        a.release(x)       # double release
    with pytest.raises(ValueError):
        a.release(2)       # never allocated
    with pytest.raises(ValueError):
        a.release(99)      # outside the pool


def test_exhausted_then_one_freed():
    a = impl.IdAllocator(4)
    ids = [a.allocate() for _ in range(4)]
    assert ids == [0, 1, 2, 3] and a.allocate() is None
    a.release(2)
    assert a.allocate() == 2
    assert a.allocate() is None


def test_port_pool_with_base():
    # Production flavour: an agent hands out host ports 30000-30009 to sidecars.
    ports = impl.IdAllocator(10, base=30000)
    got = [ports.allocate() for _ in range(10)]
    assert got == list(range(30000, 30010))
    assert ports.allocate() is None
    ports.release(30007)  # pod envoy-7 terminated
    ports.release(30003)  # pod envoy-3 terminated
    assert ports.allocate() == 30003
    assert ports.allocate() == 30007
    with pytest.raises(ValueError):
        ports.release(29999)


def test_large_random_matches_brute_force():
    rng = random.Random(1845)
    size = 300
    a = impl.IdAllocator(size, base=1000)
    free = set(range(1000, 1000 + size))  # reference: a plain set, min() per allocate
    used: list[int] = []
    for _ in range(10_000):
        if used and rng.random() < 0.45:
            x = used.pop(rng.randrange(len(used)))
            a.release(x)
            free.add(x)
        else:
            expected = min(free) if free else None
            assert a.allocate() == expected
            if expected is not None:
                free.remove(expected)
                used.append(expected)
