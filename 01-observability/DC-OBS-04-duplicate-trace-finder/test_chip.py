"""Tests for DC-OBS-04 Duplicate Stack Trace Finder."""
from __future__ import annotations

import random
from collections import Counter

from chip import load_impl

impl = load_impl(__file__)
F = impl.Frame


def brute_force(root) -> list[str]:
    # Independent reference: render every subtree in full and count the strings.
    seen: Counter[str] = Counter()

    def walk(node):
        seen[impl.render(node)] += 1
        for c in node.children:
            walk(c)

    if root is not None:
        walk(root)
    return sorted(s for s, n in seen.items() if n >= 2)


def test_empty_and_single():
    assert impl.find_duplicate_subtrees(None) == []
    assert impl.find_duplicate_subtrees(F("main")) == []


def test_two_identical_leaves():
    root = F("handler", [F("db.query"), F("db.query")])
    assert impl.find_duplicate_subtrees(root) == ["db.query"]


def test_nested_duplicates_report_every_shape_once():
    retry = lambda: F("retry", [F("http.get", [F("dns.resolve")])])  # noqa: E731
    root = F("main", [retry(), retry(), retry()])
    assert impl.find_duplicate_subtrees(root) == [
        "dns.resolve",
        "http.get(dns.resolve)",
        "retry(http.get(dns.resolve))",
    ]


def test_same_names_different_shape_are_not_duplicates():
    # Boundary: same set of frames, but call order differs, so the traces differ.
    root = F("main", [F("a", [F("b"), F("c")]), F("a", [F("c"), F("b")])])
    assert impl.find_duplicate_subtrees(root) == ["b", "c"]


def test_outage_traces_group_into_one_issue():
    # Production flavour: 3 workers of payments-worker hit the same timeout path,
    # one hit a different error. The repeated path is one fingerprint.
    def timeout_path():
        return F("charge", [F("stripe.client.post", [F("socket.recv"), F("raise TimeoutError")])])

    root = F("payments-worker", [
        timeout_path(),
        timeout_path(),
        F("charge", [F("stripe.client.post", [F("raise KeyError")])]),
        timeout_path(),
    ])
    dups = impl.find_duplicate_subtrees(root)
    assert "charge(stripe.client.post(socket.recv,raise TimeoutError))" in dups
    assert not any("KeyError" in d for d in dups)


def test_very_deep_trace_does_not_overflow():
    # A 20,000-frame recursive trace (think runaway recursion) with two leaves "g".
    deep = F("f")
    node = deep
    for _ in range(20_000):
        nxt = F("f")
        node.children.append(nxt)
        node = nxt
    root = F("main", [deep, F("g"), F("g")])
    assert impl.find_duplicate_subtrees(root) == ["g"]


def test_random_trees_match_brute_force():
    rng = random.Random(652)
    names = ["a", "b", "c"]
    for _ in range(50):
        nodes = [F(rng.choice(names))]
        for _ in range(rng.randint(1, 300)):
            child = F(rng.choice(names))
            rng.choice(nodes).children.append(child)
            nodes.append(child)
        assert impl.find_duplicate_subtrees(nodes[0]) == brute_force(nodes[0])
