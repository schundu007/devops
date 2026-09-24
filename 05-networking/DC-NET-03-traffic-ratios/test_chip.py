"""Tests for DC-NET-03 Capacity & Traffic Ratio Calculator."""
from __future__ import annotations

import math
import random

from chip import load_impl

impl = load_impl(__file__)


def close(got: list[float], want: list[float]) -> bool:
    return len(got) == len(want) and all(math.isclose(g, w, rel_tol=1e-9) for g, w in zip(got, want))


def test_capacity_chain_and_inverse():
    facts = [("cluster", "node"), ("node", "pod")]
    got = impl.calc_ratios(facts, [20.0, 30.0], [
        ("cluster", "pod"), ("pod", "cluster"), ("node", "cluster"), ("pod", "node"),
    ])
    assert close(got, [600.0, 1 / 600, 1 / 20, 1 / 30])


def test_unknown_units_and_self_queries():
    facts = [("cluster", "node")]
    got = impl.calc_ratios(facts, [20.0], [("node", "node"), ("vm", "vm"), ("vm", "node")])
    assert close(got, [1.0, -1.0, -1.0])


def test_empty_facts():
    assert impl.calc_ratios([], [], [("a", "a"), ("a", "b")]) == [-1.0, -1.0]
    assert impl.calc_ratios([("a", "b")], [2.0], []) == []


def test_disconnected_groups():
    # Compute and storage are both known, but nothing links them.
    facts = [("rack", "server"), ("array", "disk")]
    got = impl.calc_ratios(facts, [40.0, 24.0], [("rack", "disk"), ("server", "rack")])
    assert close(got, [-1.0, 1 / 40])


def test_mesh_traffic_weights_multiply():
    # Production flavour: 50% of ingress goes to "checkout", and 20% of checkout
    # goes to "checkout-canary". What fraction of ingress hits the canary?
    facts = [("ingress", "checkout"), ("checkout", "checkout-canary")]
    got = impl.calc_ratios(facts, [0.5, 0.2], [("ingress", "checkout-canary")])
    assert close(got, [0.1])


def test_boundary_single_fact_both_directions():
    got = impl.calc_ratios([("a", "b")], [4.0], [("a", "b"), ("b", "a")])
    assert close(got, [4.0, 0.25])


def test_large_random_tree_matches_potentials():
    # Independent reference: give every unit a "potential" relative to its tree root
    # with one DFS; then (x, y) = pot[y] / pot[x]. The solution does a BFS per query.
    rng = random.Random(399)
    n = 2_000
    names = [f"u{i}" for i in range(n)]
    facts, values = [], []
    pot = {names[0]: 1.0, names[1_000]: 1.0}  # two separate trees
    for i in range(1, n):
        if i == 1_000:
            continue
        parent = rng.randrange(1_000 if i > 1_000 else 0, i)  # stay inside this tree
        v = rng.uniform(0.5, 2.0)
        if rng.random() < 0.5:
            facts.append((names[parent], names[i])); values.append(v)   # 1 parent = v child
            pot[names[i]] = pot[names[parent]] * v
        else:
            facts.append((names[i], names[parent])); values.append(v)   # 1 child = v parent
            pot[names[i]] = pot[names[parent]] / v
    queries = [(rng.choice(names), rng.choice(names)) for _ in range(300)]
    want = []
    for x, y in queries:
        same_tree = (int(x[1:]) < 1_000) == (int(y[1:]) < 1_000)
        want.append(pot[y] / pot[x] if same_tree else -1.0)
    got = impl.calc_ratios(facts, values, queries)
    assert all(
        (w == -1.0 and g == -1.0) or math.isclose(g, w, rel_tol=1e-6) for g, w in zip(got, want)
    )
