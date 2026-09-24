"""Tests for DC-REL-06 Change Impact Query."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)


def reference(n, deps, queries) -> list[bool]:
    """Independent check: Floyd-Warshall transitive closure."""
    r = [[False] * n for _ in range(n)]
    for up, down in deps:
        r[up][down] = True
    for k in range(n):
        rk = r[k]
        for i in range(n):
            if r[i][k]:
                ri = r[i]
                for j in range(n):
                    if rk[j]:
                        ri[j] = True
    return [r[u][v] for u, v in queries]


def test_direct_and_indirect_dependencies():
    # 0 -> 1 -> 2, and 3 alone
    deps = [(0, 1), (1, 2)]
    assert impl.impacts(4, deps, [(0, 1), (0, 2), (2, 0), (3, 2), (1, 2)]) == [True, True, False, False, True]


def test_single_component_and_no_queries():
    assert impl.impacts(1, [], [(0, 0)]) == [False]      # a component does not depend on itself
    assert impl.impacts(3, [(0, 1)], []) == []


def test_no_edges_nothing_depends_on_anything():
    assert impl.impacts(3, [], [(0, 1), (1, 2), (2, 0)]) == [False, False, False]


def test_direction_matters():
    deps = [(0, 1)]
    assert impl.impacts(2, deps, [(0, 1), (1, 0)]) == [True, False]


def test_shared_vpc_blast_radius():
    # Production flavour: before changing module "vpc", which stacks are affected?
    names = ["vpc", "subnets", "eks-cluster", "rds-orders", "ingress", "orders-api", "billing-api", "dns"]
    idx = {name: i for i, name in enumerate(names)}
    edges = [("vpc", "subnets"), ("subnets", "eks-cluster"), ("subnets", "rds-orders"),
             ("eks-cluster", "ingress"), ("eks-cluster", "orders-api"), ("rds-orders", "orders-api"),
             ("ingress", "orders-api"), ("dns", "ingress")]
    deps = [(idx[a], idx[b]) for a, b in edges]
    queries = [(idx["vpc"], idx[x]) for x in names]
    affected = [x for x, hit in zip(names, impl.impacts(len(names), deps, queries)) if hit]
    assert affected == ["subnets", "eks-cluster", "rds-orders", "ingress", "orders-api"]
    assert impl.impacts(len(names), deps, [(idx["dns"], idx["rds-orders"])]) == [False]


def test_large_random_matches_floyd_warshall():
    rng = random.Random(1462)
    n = 120
    labels = list(range(n))
    rng.shuffle(labels)
    deps = []
    for _ in range(600):
        i, j = sorted(rng.sample(range(n), 2))
        deps.append((labels[i], labels[j]))              # forward edges only: a DAG
    queries = [(rng.randrange(n), rng.randrange(n)) for _ in range(5_000)]
    assert impl.impacts(n, deps, queries) == reference(n, deps, queries)
