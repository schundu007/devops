"""Tests for DC-OBS-08 Live Latency Percentiles.

(added) pytest wrapper. The cases themselves are the handbook's, read unchanged
from handbook.json (Source: Handbook #39 Find Median from Data Stream).
The handbook compares answers as floats within 1e-5 (spec "cmp": "float").
"""
from __future__ import annotations

import os
import random
import statistics

import pytest
from chip import case_id, handbook, handbook_solutions, load_impl, run_handbook_case

HB = handbook(__file__)
impl = load_impl(__file__)


def same(got: list, expected: list) -> bool:
    if len(got) != len(expected):
        return False
    for g, e in zip(got, expected):
        if e is None:
            if g is not None:
                return False
        elif g is None or abs(g - e) > 1e-5:
            return False
    return True


# From handbook: all cases, unchanged.
@pytest.mark.parametrize("case", HB["tests"], ids=case_id)
def test_handbook_case(case):
    assert same(run_handbook_case(impl, HB["spec"], case["args"]), case["expected"])


# Step 3 check: every Python solution copied from the handbook passes the copied cases.
@pytest.mark.skipif(os.environ.get("CHIP_TARGET") == "starter", reason="checks handbook code only")
@pytest.mark.parametrize("name,module", handbook_solutions(__file__), ids=lambda x: x if isinstance(x, str) else "")
def test_every_handbook_solution(name, module):
    for case in HB["tests"]:
        assert same(run_handbook_case(module, HB["spec"], case["args"]), case["expected"]), name


# (added) The README's second example.
def test_added_example_even_count():
    mf = impl.MedianFinder()
    for ms in (120, 80, 300, 95):
        mf.addNum(ms)
    assert abs(mf.findMedian() - 107.5) <= 1e-5


# DevOps layer (added): a latency stream with a slow tail, checked at every step.
def test_latency_stream_p50_tracks_exact_median():
    rng = random.Random(295)
    mf = impl.MedianFinder()
    seen: list[int] = []
    for i in range(3_000):
        # 95% fast requests around 40 ms, 5% slow ones from a cold cache.
        ms = rng.randint(30, 50) if rng.random() < 0.95 else rng.randint(800, 2_000)
        mf.addNum(ms)
        seen.append(ms)
        if i % 100 == 0:
            assert abs(mf.findMedian() - statistics.median(seen)) <= 1e-5
    # The slow tail barely moves the median: that is why p50 alone hides it.
    assert 30 <= mf.findMedian() <= 50
