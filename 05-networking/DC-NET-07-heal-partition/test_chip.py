"""Tests for DC-NET-07 Heal a Network Partition."""
from __future__ import annotations

import random
from collections import deque

from chip import load_impl

impl = load_impl(__file__)
moves = impl.min_link_moves


def brute(n, links) -> int:
    # Independent reference: BFS component count, plus the edge-count rule.
    if len(links) < n - 1:
        return -1
    adj = [[] for _ in range(n)]
    for a, b in links:
        adj[a].append(b)
        adj[b].append(a)
    seen, comps = [False] * n, 0
    for s in range(n):
        if seen[s]:
            continue
        comps += 1
        seen[s] = True
        q = deque([s])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if not seen[v]:
                    seen[v] = True
                    q.append(v)
    return comps - 1


def test_normal_one_move():
    # 0-1-2 has a spare loop link; device 3 is cut off.
    assert moves(4, [(0, 1), (0, 2), (1, 2)]) == 1


def test_not_enough_links():
    assert moves(6, [(0, 1), (0, 2), (0, 3), (1, 2)]) == -1


def test_single_device_and_already_connected():
    assert moves(1, []) == 0
    assert moves(3, [(0, 1), (1, 2)]) == 0


def test_boundary_exactly_n_minus_1_links():
    # n - 1 links, but one of them is a spare loop link: still solvable.
    assert moves(4, [(0, 1), (1, 2), (2, 0)]) == 1
    # n - 1 links forming a tree: already connected.
    assert moves(4, [(0, 1), (1, 2), (2, 3)]) == 0


def test_duplicate_links_are_spares():
    assert moves(3, [(0, 1), (0, 1)]) == 1


def test_switch_reboot_partition():
    # Production flavour: after a core switch reboot, 12 access switches sit in
    # 3 segments. Segment A has 2 redundant uplinks that can be re-patched.
    seg_a = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]   # 4 devices, 5 links (2 spare)
    seg_b = [(4, 5), (5, 6), (6, 7)]                   # 4 devices, a line
    seg_c = [(8, 9), (9, 10), (10, 11)]                # 4 devices, a line
    assert moves(12, seg_a + seg_b + seg_c) == 2       # 3 segments -> 2 moves
    assert moves(12, seg_a[:3] + seg_b + seg_c) == -1  # no spares: 9 links < 11


def test_large_random_matches_bfs():
    rng = random.Random(1319)
    for n, m in [(10, 12), (500, 520), (100_000, 100_500)]:
        links = [(rng.randrange(n), rng.randrange(n)) for _ in range(m)]
        links = [(a, b) for a, b in links if a != b]
        assert moves(n, links) == brute(n, links)
