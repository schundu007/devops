"""Tests for DC-NET-04 Network Delay Time."""
from __future__ import annotations

import random
from collections import deque

from chip import load_impl

impl = load_impl(__file__)
delay = impl.network_delay


def bellman_ford(links, n, source) -> int:
    # Independent reference: relax every edge until nothing changes.
    inf = float("inf")
    dist = [inf] * (n + 1)
    dist[source] = 0
    for _ in range(n):
        changed = False
        for u, v, w in links:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                changed = True
        if not changed:
            break
    worst = max(dist[1:])
    return -1 if worst == inf else int(worst)


def test_normal_flood():
    links = [(2, 1, 1), (2, 3, 1), (3, 4, 1)]
    assert delay(links, 4, 2) == 2


def test_single_router():
    assert delay([], 1, 1) == 0


def test_unreachable_router_is_partition():
    assert delay([(1, 2, 1)], 2, 2) == -1   # links are one-way
    assert delay([(1, 2, 5)], 3, 1) == -1   # router 3 has no links at all


def test_slow_direct_link_loses_to_fast_detour():
    # Boundary: the direct 10 ms link must lose to 1 + 1 + 1 ms through two hops.
    links = [(1, 4, 10), (1, 2, 1), (2, 3, 1), (3, 4, 1)]
    assert delay(links, 4, 1) == 3


def test_zero_delay_links_and_parallel_links():
    links = [(1, 2, 0), (2, 3, 0), (1, 3, 5), (1, 3, 2)]
    assert delay(links, 3, 1) == 0


def test_lsa_flood_across_two_sites():
    # Production flavour: router 1 in site A floods a link-state update.
    # Inside a site links are 1 ms; the two WAN links are 18 ms and 25 ms, both ways.
    site_a, site_b = [1, 2, 3, 4], [5, 6, 7, 8]
    links = []
    for site in (site_a, site_b):
        for a, b in zip(site, site[1:]):
            links += [(a, b, 1), (b, a, 1)]
    links += [(4, 5, 18), (5, 4, 18), (1, 8, 25), (8, 1, 25)]
    # Through WAN 1: 4 at 3 ms, 5 at 21, 6 at 22, 7 at 23, 8 at 24.
    # WAN 2 would bring 8 at 25, so it loses. The last router (8) hears at 24 ms.
    assert delay(links, 8, 1) == 24
    links.remove((4, 5, 18))
    links.remove((5, 4, 18))                  # WAN link 1 fails: only the 25 ms path is left
    assert delay(links, 8, 1) == 25 + 3        # router 5 is now 1->8->7->6->5


def test_unit_weights_match_bfs():
    rng = random.Random(7)
    n = 3_000
    links = [(rng.randint(1, n), rng.randint(1, n), 1) for _ in range(15_000)]
    links += [(i, i + 1, 1) for i in range(1, n)]  # a chain keeps everything reachable
    graph = [[] for _ in range(n + 1)]
    for u, v, _ in links:
        graph[u].append(v)
    level = {1: 0}
    queue = deque([1])
    while queue:
        u = queue.popleft()
        for v in graph[u]:
            if v not in level:
                level[v] = level[u] + 1
                queue.append(v)
    assert delay(links, n, 1) == max(level.values())


def test_large_random_matches_bellman_ford():
    rng = random.Random(743)
    for n, m in [(5, 8), (30, 60), (200, 900), (2_000, 12_000)]:
        links = [(rng.randint(1, n), rng.randint(1, n), rng.randint(0, 100)) for _ in range(m)]
        assert delay(links, n, 1) == bellman_ford(links, n, 1)
