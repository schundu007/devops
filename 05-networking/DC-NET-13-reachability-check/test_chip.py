"""Tests for DC-NET-13 Reachability Check."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)


def _union_find(n: int, links: list[list[int]], s: int, t: int) -> bool:
    # Independent reference: union-find groups.
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in links:
        parent[find(a)] = find(b)
    return find(s) == find(t)


def test_path_through_middle_tier():
    assert impl.can_reach(3, [[0, 1], [1, 2]], 0, 2) is True


def test_two_separate_segments():
    links = [[0, 1], [0, 2], [3, 5], [5, 4], [4, 3]]
    assert impl.can_reach(6, links, 0, 5) is False


def test_single_node_reaches_itself():
    assert impl.can_reach(1, [], 0, 0) is True


def test_no_links():
    assert impl.can_reach(2, [], 0, 1) is False


def test_internet_to_database():
    # Production flavour: 0 internet, 1 ALB, 2 web tier, 3 app tier, 4 database,
    # 5 bastion. The app tier's rule to the database was removed in the last change,
    # but the bastion still has a path to the database.
    links = [[0, 1], [1, 2], [2, 3], [5, 4]]
    assert impl.can_reach(6, links, 0, 4) is False
    links.append([0, 5])  # someone opens the bastion to the internet
    assert impl.can_reach(6, links, 0, 4) is True


def test_random_graphs_match_union_find():
    rng = random.Random(1971)
    for _ in range(300):
        n = rng.randint(1, 30)
        links = [rng.sample(range(n), 2) for _ in range(rng.randint(0, n))] if n > 1 else []
        s, t = rng.randrange(n), rng.randrange(n)
        assert impl.can_reach(n, links, s, t) == _union_find(n, links, s, t)


def test_large_chain_no_recursion_limit():
    # 200,000 nodes in one long chain would overflow a recursive DFS.
    n = 200_000
    links = [[i, i + 1] for i in range(n - 1)]
    assert impl.can_reach(n, links, 0, n - 1) is True
    assert impl.can_reach(n + 1, links, 0, n) is False
