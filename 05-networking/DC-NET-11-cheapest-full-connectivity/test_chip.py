"""Tests for DC-NET-11 Cheapest Full Connectivity."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)


def _kruskal(sites: list[list[int]]) -> int:
    # Independent reference: Kruskal over every pair, with union-find.
    n = len(sites)
    edges = sorted(
        (abs(sites[i][0] - sites[j][0]) + abs(sites[i][1] - sites[j][1]), i, j)
        for i in range(n) for j in range(i + 1, n)
    )
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    total, used = 0, 0
    for d, i, j in edges:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj
            total += d
            used += 1
            if used == n - 1:
                break
    return total


def test_five_sites():
    sites = [[0, 0], [2, 2], [3, 10], [5, 2], [7, 0]]
    assert impl.min_interconnect_cost(sites) == 20


def test_single_site_and_empty():
    assert impl.min_interconnect_cost([[4, 4]]) == 0
    assert impl.min_interconnect_cost([]) == 0


def test_two_sites():
    assert impl.min_interconnect_cost([[3, 12], [-2, 5]]) == 12


def test_sites_in_a_line():
    # Boundary: the tree is the line itself; the total is the span.
    sites = [[0, 0], [10, 0], [3, 0], [7, 0]]
    assert impl.min_interconnect_cost(sites) == 10


def test_campus_buildings():
    # Production flavour: 4 buildings at the corners of a 100 x 50 block
    # plus a data hall in the middle. Best: the two 50 m short sides, then the hall
    # joins both pairs at 75 m each (cheaper than one 100 m long side plus a 75 m hall link).
    sites = [[0, 0], [100, 0], [0, 50], [100, 50], [50, 25]]
    assert impl.min_interconnect_cost(sites) == 250


def test_random_matches_kruskal():
    rng = random.Random(1584)
    for _ in range(150):
        sites = [[rng.randint(-50, 50), rng.randint(-50, 50)] for _ in range(rng.randint(1, 25))]
        assert impl.min_interconnect_cost(sites) == _kruskal(sites)


def test_large_input():
    rng = random.Random(2)
    sites = [[rng.randint(-10**6, 10**6), rng.randint(-10**6, 10**6)] for _ in range(400)]
    assert impl.min_interconnect_cost(sites) == _kruskal(sites)
