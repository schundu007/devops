"""Capra Playground export for DC-PLAT-15 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "coverage_gaps", "params": ["schedules"], "types": {}, "ret": "value", "cmp": "exact"}

EXAMPLES = [
    {"args": {"schedules": [[[1, 2], [5, 6]], [[1, 3]], [[4, 10]]]},
     "explanation": "Shifts cover 1-3 and 4-10, so nobody is on call between 3 and 4.",
     "why": {"t": "One gap", "d": "Coverage from three engineers leaves one hole."}},
    {"args": {"schedules": [[[1, 3], [6, 7]], [[2, 4]], [[2, 5], [9, 12]]]},
     "explanation": "Coverage runs 1-5, 6-7 and 9-12, leaving two gaps: 5-6 and 7-9.",
     "why": {"t": "Two gaps", "d": "Several holes between the first start and the last end."}},
]


def _large():
    rng = random.Random(759)
    schedules = []
    for _ in range(25):
        t, shifts = rng.randint(0, 50), []
        for _ in range(20):
            t += rng.randint(0, 40)
            end = t + rng.randint(1, 30)
            shifts.append([t, end])
            t = end
        schedules.append(shifts)
    return {"schedules": schedules}


TESTS = [
    {"args": {"schedules": []},
     "why": {"t": "No engineers", "d": "Nothing scheduled means no range to check."}},
    {"args": {"schedules": [[], []]},
     "why": {"t": "Empty schedules", "d": "Engineers with no shifts contribute nothing."}},
    {"args": {"schedules": [[[0, 5], [5, 9]]]},
     "why": {"t": "Touching shifts", "d": "A shift ending at 5 and one starting at 5 leave no gap (ends are exclusive)."}},
    {"args": {"schedules": [[[0, 100]], [[10, 20], [30, 40]]]},
     "why": {"t": "Nested shifts", "d": "A long shift covers the short ones inside it."}},
    {"args": {"schedules": [[[0, 8], [16, 24], [32, 40]]]},
     "why": {"t": "Single engineer", "d": "One person on call alone leaves every off-shift hour uncovered."}},
    {"args": {"schedules": [[[0, 10]], [[0, 10]], [[0, 10]]]},
     "why": {"t": "Duplicates", "d": "Identical shifts from several people cover the same span."}},
    {"args": {"schedules": [[[0, 9], [24, 33]], [[8, 17], [32, 41]], [[16, 25], [40, 48]]]},
     "why": {"t": "Follow-the-sun", "d": "Three regions hand over with an hour of overlap: no gaps."}},
    {"args": {"schedules": [[[0, 1]], [[1_000_000_000, 1_000_000_001]]]},
     "why": {"t": "Huge times", "d": "Epoch-sized times: a timeline of cells would be impossible."}},
    {"args": _large(),
     "why": {"t": "Large input", "d": "25 engineers with 20 shifts each."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "K-way merge (Optimal)",
     "description": "Each engineer's shifts are already sorted, so merge them with heapq.merge. Track covered_until, the latest end so far; a shift starting after it reveals a gap.",
     "time": "O(N log k)", "space": "O(k) plus the output",
     "keyPoints": ["Each list is sorted already: merge, don't re-sort", "Gap only when start > covered_until (ends are exclusive)", "Extend covered_until with max"]},
    {"name": "Sort all shifts",
     "description": "Flatten every shift into one list, sort by start, and sweep with covered_until.",
     "time": "O(N log N)", "space": "O(N)",
     "keyPoints": ["Simplest to write", "Ignores that each engineer's list is already sorted"],
     "code": '''from __future__ import annotations


def coverage_gaps(schedules: list[list[list[int]]]) -> list[list[int]]:
    shifts = sorted(s for person in schedules for s in person)
    gaps: list[list[int]] = []
    if not shifts:
        return gaps
    covered = shifts[0][1]
    for start, end in shifts[1:]:
        if start > covered:
            gaps.append([covered, start])
        covered = max(covered, end)
    return gaps
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Timeline cells", "idea": "Mark every minute covered, then read off unmarked runs.",
     "time": "O(time span)", "space": "O(time span)", "use": "Tiny ranges only; impossible with epoch times."},
    {"name": "Sort all shifts", "idea": "Flatten, sort by start, sweep.",
     "time": "O(N log N)", "space": "O(N)", "use": "When the per-person lists are not sorted."},
    {"name": "K-way merge", "idea": "Merge the already-sorted lists with a heap of size k.",
     "time": "O(N log k)", "space": "O(k)", "use": "Many shifts, few engineers."},
]
