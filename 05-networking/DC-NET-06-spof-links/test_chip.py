"""Tests for DC-NET-06 Single-Point-of-Failure Links."""
from __future__ import annotations

import random
from collections import deque

from chip import load_impl

impl = load_impl(__file__)


def norm(edges) -> list[tuple[int, int]]:
    return sorted((min(a, b), max(a, b)) for a, b in edges)


def solve(n, links):
    return norm(impl.critical_links(n, links))


def components(n, links, skip: int) -> int:
    adj = [[] for _ in range(n)]
    for i, (a, b) in enumerate(links):
        if i != skip:
            adj[a].append(b)
            adj[b].append(a)
    seen, count = [False] * n, 0
    for s in range(n):
        if not seen[s]:
            count += 1
            seen[s] = True
            q = deque([s])
            while q:
                u = q.popleft()
                for v in adj[u]:
                    if not seen[v]:
                        seen[v] = True
                        q.append(v)
    return count


def brute(n, links):
    # Independent reference: remove each link and see if the component count rises.
    base = components(n, links, -1)
    return norm(links[i] for i in range(len(links)) if components(n, links, i) > base)


def test_normal_ring_with_tail():
    # 0-1-2 is a ring; 1-3 is the only way to reach 3.
    assert solve(4, [(0, 1), (1, 2), (2, 0), (1, 3)]) == [(1, 3)]


def test_single_link_and_single_device():
    assert solve(2, [(0, 1)]) == [(0, 1)]
    assert solve(1, []) == []


def test_ring_has_no_spof():
    n = 6
    assert solve(n, [(i, (i + 1) % n) for i in range(n)]) == []


def test_parallel_links_back_each_other_up():
    # Boundary: two cables between the same pair are redundant.
    assert solve(3, [(0, 1), (0, 1), (1, 2)]) == [(1, 2)]


def test_two_racks_joined_by_one_uplink():
    # Production flavour: two leaf-spine pods, each fully redundant inside,
    # joined by a single inter-pod link 3-4. That link is the SPOF.
    pod_a = [(0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3)]
    pod_b = [(4, 5), (5, 6), (6, 4), (4, 7), (5, 7), (6, 7)]
    links = pod_a + pod_b + [(3, 4)]
    assert solve(8, links) == [(3, 4)]
    # Add a second inter-pod link: the SPOF is gone.
    assert solve(8, links + [(2, 6)]) == []


def test_disconnected_network():
    assert solve(5, [(0, 1), (2, 3), (3, 4), (4, 2)]) == [(0, 1)]


def test_long_chain_no_recursion_limit():
    n = 100_000
    links = [(i, i + 1) for i in range(n - 1)]
    assert len(impl.critical_links(n, links)) == n - 1
    assert impl.critical_links(n, links + [(n - 1, 0)]) == []  # closing the ring


def test_random_matches_brute_force():
    rng = random.Random(1192)
    for _ in range(150):
        n = rng.randint(1, 40)
        m = rng.randint(0, 2 * n)
        links = [(rng.randrange(n), rng.randrange(n)) for _ in range(m)]
        links = [(a, b) for a, b in links if a != b]
        assert solve(n, links) == brute(n, links)
