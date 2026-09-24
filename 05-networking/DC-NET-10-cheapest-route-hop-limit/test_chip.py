"""Tests for DC-NET-10 Cheapest Route Within Hop Limit."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)


def _brute(n, routes, src, dst, max_transit) -> int:
    # Independent reference: DFS over every walk with at most max_transit + 1 hops.
    adj: dict[int, list[tuple[int, int]]] = {i: [] for i in range(n)}
    for a, b, p in routes:
        adj[a].append((b, p))
    best = float("inf")

    def dfs(node: int, hops: int, total: int) -> None:
        nonlocal best
        if node == dst:
            best = min(best, total)
            return
        if hops == max_transit + 1:
            return
        for nxt, p in adj[node]:
            dfs(nxt, hops + 1, total + p)

    dfs(src, 0, 0)
    return -1 if best == float("inf") else best


def test_cheaper_path_is_too_long():
    routes = [[0, 1, 100], [1, 2, 100], [2, 3, 100], [0, 3, 800], [1, 3, 600]]
    assert impl.cheapest_route(4, routes, 0, 3, 1) == 700  # 0->1->3
    assert impl.cheapest_route(4, routes, 0, 3, 2) == 300  # 0->1->2->3


def test_zero_transit_means_direct_only():
    routes = [[0, 1, 100], [1, 2, 100], [0, 2, 500]]
    assert impl.cheapest_route(3, routes, 0, 2, 0) == 500


def test_unreachable_and_no_routes():
    assert impl.cheapest_route(3, [[0, 1, 5]], 0, 2, 5) == -1
    assert impl.cheapest_route(2, [], 0, 1, 1) == -1


def test_routes_are_one_way():
    assert impl.cheapest_route(2, [[1, 0, 5]], 0, 1, 3) == -1


def test_hop_limit_boundary():
    # A chain of 5 hops needs exactly 4 transit regions.
    routes = [[i, i + 1, 10] for i in range(5)]
    assert impl.cheapest_route(6, routes, 0, 5, 4) == 50
    assert impl.cheapest_route(6, routes, 0, 5, 3) == -1


def test_egress_cost_between_regions():
    # Production flavour: 0 = us-east-1, 1 = us-west-2, 2 = eu-central-1, 3 = ap-south-1.
    # Prices are cents per GB-batch (fake). A TTL-style limit allows one transit region.
    routes = [[0, 3, 900], [0, 2, 200], [2, 3, 300], [0, 1, 100], [1, 2, 50], [1, 3, 800]]
    assert impl.cheapest_route(4, routes, 0, 3, 1) == 500  # via eu-central-1
    assert impl.cheapest_route(4, routes, 0, 3, 2) == 450  # via us-west-2 then eu-central-1


def test_random_graphs_match_brute_force():
    rng = random.Random(787)
    for _ in range(200):
        n = rng.randint(2, 7)
        routes = []
        for _ in range(rng.randint(0, 12)):
            a, b = rng.sample(range(n), 2)
            routes.append([a, b, rng.randint(1, 100)])
        src, dst = rng.sample(range(n), 2)
        k = rng.randint(0, 3)
        assert impl.cheapest_route(n, routes, src, dst, k) == _brute(n, routes, src, dst, k)


def test_large_dense_graph():
    rng = random.Random(1)
    n = 100
    routes = [[a, b, rng.randint(1, 10_000)] for a in range(n) for b in range(n) if a != b]
    got = impl.cheapest_route(n, routes, 0, n - 1, n - 2)
    direct = next(p for a, b, p in routes if a == 0 and b == n - 1)
    assert 0 < got <= direct
