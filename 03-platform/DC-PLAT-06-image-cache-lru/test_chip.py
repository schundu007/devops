"""Tests for DC-PLAT-06 Image Cache with LRU Eviction.

(added) pytest wrapper. The cases themselves are the handbook's, read unchanged
from handbook.json (Source: Handbook #88 LRU Cache).
"""
from __future__ import annotations

import os
import random
from collections import OrderedDict

import pytest
from chip import case_id, handbook, handbook_solutions, load_impl, run_handbook_case

HB = handbook(__file__)
impl = load_impl(__file__)


# From handbook: all cases, unchanged.
@pytest.mark.parametrize("case", HB["tests"], ids=case_id)
def test_handbook_case(case):
    assert run_handbook_case(impl, HB["spec"], case["args"]) == case["expected"]


# Step 3 check: every Python solution copied from the handbook passes the copied cases.
@pytest.mark.skipif(os.environ.get("CHIP_TARGET") == "starter", reason="checks handbook code only")
@pytest.mark.parametrize("name,module", handbook_solutions(__file__), ids=lambda x: x if isinstance(x, str) else "")
def test_every_handbook_solution(name, module):
    for case in HB["tests"]:
        assert run_handbook_case(module, HB["spec"], case["args"]) == case["expected"], name


class ReferenceLRU:
    """Independent check built on OrderedDict."""

    def __init__(self, capacity: int) -> None:
        self.capacity, self.data = capacity, OrderedDict()

    def get(self, key: int) -> int:
        if key not in self.data:
            return -1
        self.data.move_to_end(key)
        return self.data[key]

    def put(self, key: int, value: int) -> None:
        self.data[key] = value
        self.data.move_to_end(key)
        if len(self.data) > self.capacity:
            self.data.popitem(last=False)


# DevOps layer (added): the node image cache from the README.
# Image IDs: 1 = nginx:1.27, 2 = redis:7.2, 3 = app:v142, 4 = app:v143. Value = size in MiB.
def test_node_keeps_recently_used_images():
    cache = impl.LRUCache(3)
    cache.put(1, 190)
    cache.put(2, 140)
    cache.put(3, 610)
    assert cache.get(1) == 190   # a pod restart just used nginx
    cache.put(4, 615)            # deploy v143: the disk is full, evict the least recently used
    assert cache.get(2) == -1    # redis was idle longest, so it went
    assert cache.get(1) == 190 and cache.get(3) == 610 and cache.get(4) == 615


def test_capacity_one():
    cache = impl.LRUCache(1)
    cache.put(3, 610)
    cache.put(4, 615)
    assert cache.get(3) == -1 and cache.get(4) == 615


def test_re_pull_updates_value_and_recency():
    cache = impl.LRUCache(2)
    cache.put(1, 190)
    cache.put(2, 140)
    cache.put(1, 195)            # re-pulled with a new layer: a use, and a new value
    cache.put(3, 610)            # evicts 2, not 1
    assert cache.get(1) == 195 and cache.get(2) == -1


def test_large_random_matches_reference():
    rng = random.Random(146)
    cap = 50
    cache, ref = impl.LRUCache(cap), ReferenceLRU(cap)
    for _ in range(50_000):
        key = rng.randint(0, 200)
        if rng.random() < 0.5:
            assert cache.get(key) == ref.get(key)
        else:
            v = rng.randint(0, 10**5)
            cache.put(key, v)
            ref.put(key, v)
