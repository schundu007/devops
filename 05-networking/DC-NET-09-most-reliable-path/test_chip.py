"""Tests for DC-NET-09 Most Reliable Path. Floats are compared with a tolerance."""
from __future__ import annotations

import math
import random

from chip import load_impl

impl = load_impl(__file__)


def close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12)


def _bellman_ford(n, links, success, src, dst) -> float:
    # Independent reference: relax every link n-1 times.
    best = [0.0] * n
    best[src] = 1.0
    for _ in range(n - 1):
        changed = False
        for (a, b), p in zip(links, success):
            if best[a] * p > best[b]:
                best[b], changed = best[a] * p, True
            if best[b] * p > best[a]:
                best[a], changed = best[b] * p, True
        if not changed:
            break
    return best[dst]


def test_two_hops_beat_one_weak_link():
    links = [[0, 1], [1, 2], [0, 2]]
    assert close(impl.most_reliable_path(3, links, [0.5, 0.5, 0.2], 0, 2), 0.25)


def test_direct_link_wins_when_stronger():
    links = [[0, 1], [1, 2], [0, 2]]
    assert close(impl.most_reliable_path(3, links, [0.5, 0.5, 0.3], 0, 2), 0.3)


def test_unreachable_is_zero():
    assert impl.most_reliable_path(3, [[0, 1]], [0.9], 0, 2) == 0.0


def test_no_links_at_all():
    assert impl.most_reliable_path(2, [], [], 0, 1) == 0.0


def test_perfect_and_zero_links():
    # Boundary values: a link with probability 1.0 costs nothing; 0.0 is as good as no link.
    links = [[0, 1], [1, 2], [0, 2]]
    assert close(impl.most_reliable_path(3, links, [1.0, 1.0, 0.0], 0, 2), 1.0)
    assert impl.most_reliable_path(2, [[0, 1]], [0.0], 0, 1) == 0.0


def test_three_nines_across_regions():
    # Production flavour: us-east (0) -> transit (1) -> eu-west (2) at 99.9% each,
    # versus a direct but flaky backup link at 99.5%.
    links = [[0, 1], [1, 2], [0, 2]]
    got = impl.most_reliable_path(3, links, [0.999, 0.999, 0.995], 0, 2)
    assert close(got, 0.999 * 0.999)  # 0.998001: two good hops beat one flaky link


def test_random_graphs_match_bellman_ford():
    rng = random.Random(1514)
    for _ in range(200):
        n = rng.randint(2, 30)
        links, success = [], []
        for _ in range(rng.randint(0, n * 3)):
            a, b = rng.sample(range(n), 2)
            links.append([a, b])
            success.append(round(rng.random(), 3))
        src, dst = rng.sample(range(n), 2)
        assert close(
            impl.most_reliable_path(n, links, success, src, dst),
            _bellman_ford(n, links, success, src, dst),
        )


def test_large_chain():
    n = 10_000
    links = [[i, i + 1] for i in range(n - 1)]
    got = impl.most_reliable_path(n, links, [0.9999] * (n - 1), 0, n - 1)
    assert close(got, 0.9999 ** (n - 1))
