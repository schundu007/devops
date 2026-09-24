"""Tests for DC-NET-08 Find the Loop Link."""
from __future__ import annotations

import random
from collections import deque

from chip import load_impl

impl = load_impl(__file__)


def _is_tree(n: int, links: list[list[int]]) -> bool:
    if len(links) != n - 1:
        return False
    adj: dict[int, list[int]] = {i: [] for i in range(1, n + 1)}
    for a, b in links:
        adj[a].append(b)
        adj[b].append(a)
    seen, q = {1}, deque([1])
    while q:
        for nxt in adj[q.popleft()]:
            if nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    return len(seen) == n


def _brute(n: int, links: list[list[int]]) -> list[int]:
    # Try removing links from the last one backwards; the first that leaves a tree wins.
    for i in range(len(links) - 1, -1, -1):
        if _is_tree(n, links[:i] + links[i + 1:]):
            return links[i]
    return []


def test_smallest_triangle():
    assert impl.find_loop_link(3, [[1, 2], [1, 3], [2, 3]]) == [2, 3]


def test_loop_not_at_the_end():
    # The loop is 1-2-3-1; link [3, 4] comes after it but is not on the loop.
    assert impl.find_loop_link(4, [[1, 2], [2, 3], [3, 1], [3, 4]]) == [3, 1]


def test_last_listed_loop_link_wins():
    links = [[1, 2], [2, 3], [3, 4], [1, 4], [1, 5]]
    assert impl.find_loop_link(5, links) == [1, 4]


def test_parallel_links_between_two_switches():
    # Two cables between the same pair of switches is the shortest possible loop.
    assert impl.find_loop_link(3, [[1, 2], [2, 3], [2, 1]]) == [2, 1]


def test_access_layer_miscabling():
    # Production flavour: core sw1, distribution sw2/sw3, access sw4-sw7.
    # A technician patched sw7 to sw4 while both already reach the core.
    links = [[1, 2], [1, 3], [2, 4], [2, 5], [3, 6], [3, 7], [7, 4]]
    assert impl.find_loop_link(7, links) == [7, 4]


def test_random_trees_match_brute_force():
    rng = random.Random(684)
    for _ in range(150):
        n = rng.randint(3, 40)
        links = [[rng.randint(1, i - 1), i] for i in range(2, n + 1)]
        a, b = rng.sample(range(1, n + 1), 2)
        links.insert(rng.randint(0, len(links)), [a, b])
        assert impl.find_loop_link(n, links) == _brute(n, links)


def test_large_network():
    n = 1000
    rng = random.Random(1)
    links = [[i - 1, i] for i in range(2, n + 1)]  # a long chain
    rng.shuffle(links)
    links.append([1, n])  # closing the chain into one big ring
    assert impl.find_loop_link(n, links) == [1, n]
