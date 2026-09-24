"""Tests for DC-CAP-03 Balanced Shard Split."""
from __future__ import annotations

import random
from functools import lru_cache

from chip import load_impl

impl = load_impl(__file__)


def _dp(loads: list[int], workers: int) -> int:
    # Independent reference: dynamic programming over (start index, workers left).
    n = len(loads)
    prefix = [0]
    for x in loads:
        prefix.append(prefix[-1] + x)

    @lru_cache(maxsize=None)
    def best(i: int, k: int) -> int:
        if k == 1:
            return prefix[n] - prefix[i]
        ans = prefix[n] - prefix[i]  # using fewer workers is allowed
        for j in range(i + 1, n):
            ans = min(ans, max(prefix[j] - prefix[i], best(j, k - 1)))
        return ans

    return best(0, min(workers, n))


def test_five_shards_two_workers():
    assert impl.min_busiest_worker_load([7, 2, 5, 10, 8], 2) == 18


def test_single_shard():
    assert impl.min_busiest_worker_load([42], 3) == 42


def test_one_worker_takes_everything():
    assert impl.min_busiest_worker_load([1, 2, 3, 4, 5], 1) == 15


def test_one_worker_per_shard():
    # Boundary: as many workers as shards, so the hottest shard is the answer.
    assert impl.min_busiest_worker_load([1, 4, 4], 3) == 4


def test_zero_load_shards():
    assert impl.min_busiest_worker_load([0, 0, 5, 0, 0], 2) == 5


def test_hot_tenant_range():
    # Production flavour: 8 key ranges of a user table (writes/sec, fake) across
    # 3 consumers. One hot range dominates; the answer can never go below it.
    loads = [120, 90, 1_400, 60, 300, 250, 80, 700]
    got = impl.min_busiest_worker_load(loads, 3)
    assert got == _dp(loads, 3)
    assert got >= 1_400


def test_random_matches_dp():
    rng = random.Random(410)
    for _ in range(200):
        loads = [rng.randint(0, 50) for _ in range(rng.randint(1, 14))]
        k = rng.randint(1, 6)
        assert impl.min_busiest_worker_load(loads, k) == _dp(loads, k)


def test_large_input():
    rng = random.Random(4)
    loads = [rng.randint(0, 10**6) for _ in range(100_000)]
    got = impl.min_busiest_worker_load(loads, 50)
    assert max(loads) <= got <= sum(loads)
    # Recheck feasibility at the answer and infeasibility just below it.
    def runs(limit: int) -> int:
        r, cur = 1, 0
        for x in loads:
            if cur + x > limit:
                r, cur = r + 1, 0
            cur += x
        return r
    assert runs(got) <= 50 < runs(got - 1)
