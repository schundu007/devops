"""Tests for DC-OBS-14 Multi-Node Log Timeline Merge.

(added) pytest wrapper. The cases themselves are the handbook's, read unchanged
from handbook.json (Source: Handbook #24 Merge K Sorted Lists).

Local adapter: the handbook's code uses a `ListNode` class that the handbook's
runner provides, and its test cases store linked lists as plain arrays. The adapter
below does the same job as that runner (`apps/camora/src/lib/top100Runner.ts`):
it defines ListNode, turns each array into a linked list, and turns the result back.
"""
from __future__ import annotations

import heapq
import os
import random
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from chip import case_id, handbook

HB = handbook(__file__)
HERE = Path(__file__).parent


class ListNode:
    def __init__(self, val: int = 0, next: "ListNode | None" = None) -> None:
        self.val = val
        self.next = next


def to_linked(values: list[int]) -> ListNode | None:
    dummy = tail = ListNode()
    for v in values:
        tail.next = ListNode(v)
        tail = tail.next
    return dummy.next


def from_linked(head: Any) -> list[int]:
    out = []
    while head is not None:
        out.append(head.val)
        head = head.next
    return out


def load_source(code: str, name: str) -> ModuleType:
    module = ModuleType(name)
    module.ListNode = ListNode  # what the handbook runner's prelude provides
    exec(code, module.__dict__)
    return module


def entry(module: ModuleType):
    if hasattr(module, "Solution"):
        return module.Solution().mergeKLists
    return module.mergeKLists


def merge(module: ModuleType, lists: list[list[int]]) -> list[int]:
    return from_linked(entry(module)([to_linked(l) for l in lists]))


TARGET = os.environ.get("CHIP_TARGET", "solution")
impl = load_source((HERE / f"{TARGET}.py").read_text(), f"obs14_{TARGET}")


# From handbook: all cases, unchanged.
@pytest.mark.parametrize("case", HB["tests"], ids=case_id)
def test_handbook_case(case):
    assert merge(impl, case["args"]["lists"]) == case["expected"]


# Step 3 check: every Python solution copied from the handbook passes the copied cases.
@pytest.mark.skipif(TARGET == "starter", reason="checks handbook code only")
@pytest.mark.parametrize("sol", HB["solutions"], ids=lambda s: s["name"])
def test_every_handbook_solution(sol):
    for case in HB["tests"]:
        module = load_source(sol["code"]["python"], "hb_solution")
        assert merge(module, case["args"]["lists"]) == case["expected"], sol["name"]


# (added) The min-heap k-way merge in solution_heap.py passes the same cases.
@pytest.mark.skipif(TARGET == "starter", reason="checks reference code only")
def test_added_heap_solution():
    module = load_source((HERE / "solution_heap.py").read_text(), "heap_solution")
    for case in HB["tests"]:
        assert merge(module, case["args"]["lists"]) == case["expected"]


# DevOps layer (added): three nodes' logs merged into one incident timeline.
def test_incident_timeline_from_three_nodes():
    node_a = [1_700_000_000, 1_700_000_004, 1_700_000_009]   # ip-10-0-1-11
    node_b = [1_700_000_002, 1_700_000_004]                   # ip-10-0-2-12
    node_c: list[int] = []                                    # ip-10-0-3-13, silent
    assert merge(impl, [node_a, node_b, node_c]) == [
        1_700_000_000, 1_700_000_002, 1_700_000_004, 1_700_000_004, 1_700_000_009,
    ]


# DevOps layer (added): large-input sanity check against sort, and against heapq.merge.
def test_large_random_matches_sorted():
    rng = random.Random(23)
    lists = [sorted(rng.randint(0, 10**6) for _ in range(rng.randint(0, 60))) for _ in range(300)]
    expected = sorted(v for l in lists for v in l)
    assert expected == list(heapq.merge(*lists))
    assert merge(impl, lists) == expected
