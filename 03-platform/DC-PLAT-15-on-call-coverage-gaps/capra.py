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

VARIANT_TITLE = "Coverage gaps"
VARIANT_APPROACH = "K-way merge · O(N log k) · O(k)"


def _staff_large():
    rng = random.Random(1515)
    schedules = []
    for _ in range(20):
        t, shifts = rng.randint(0, 40), []
        for _ in range(15):
            t += rng.randint(0, 30)
            end = t + rng.randint(1, 40)
            shifts.append([t, end])
            t = end
        schedules.append(shifts)
    return {"schedules": schedules, "m": 3}


def _alerts_large():
    rng = random.Random(4040)
    schedules = []
    for _ in range(20):
        t, shifts = rng.randint(0, 100), []
        for _ in range(20):
            t += rng.randint(0, 60)
            end = t + rng.randint(1, 50)
            shifts.append([t, end])
            t = end
        schedules.append(shifts)
    return {"schedules": schedules, "alerts": [rng.randint(0, 2500) for _ in range(400)]}


def us(schedules, m, t, d):
    return {"args": {"schedules": schedules, "m": m}, "why": {"t": t, "d": d}}


def ua(schedules, alerts, t, d):
    return {"args": {"schedules": schedules, "alerts": alerts}, "why": {"t": t, "d": d}}


VARIANTS = [
    {
        "key": "understaffed",
        "title": "Two-person rule windows",
        "approach": "Sweep line over sorted start/end events · O(N log N) · O(N)",
        "spec": {"kind": "fn", "fn": "understaffed", "params": ["schedules", "m"]},
        "statement": (
            "Some teams need more than one responder: a primary and a secondary, or a two-person rule for production changes. "
            "A gap is now any time with **fewer than `m`** engineers on call.\n\n"
            "`schedules[p]` is engineer `p`'s shifts, `[start, end)` pairs sorted by start and not overlapping each other.\n\n"
            "Between the first shift start and the last shift end, return every maximal `[start, end]` window in which fewer "
            "than `m` engineers are on call, in time order. Return `[]` if nobody has shifts."
        ),
        "examples": [
            {"args": {"schedules": [[[0, 10]], [[2, 6], [8, 12]]], "m": 2},
             "explanation": "Two people are on call over 2-6 and 8-10. Below two: 0-2, 6-8 and 10-12.",
             "why": {"t": "Primary + secondary", "d": "Covered by one person still counts as understaffed."}},
        ],
        "constraints": ["0 ≤ schedules.length ≤ 50", "Total shifts N ≤ 2000", "0 ≤ start < end ≤ 10⁹", "1 ≤ m ≤ 50"],
        "hints": [
            "Turn each shift into two events: +1 at start and -1 at end.",
            "Sort the events and apply every event at the same time before looking at the count; ends are exclusive.",
            "Between two consecutive event times the count is constant, so each stretch is either fully staffed or not. Merge adjacent understaffed stretches.",
        ],
        "tests": [
            us([], 2, "No engineers", "Nothing scheduled: no range to check."),
            us([[[0, 5]]], 1, "m = 1 matches the main problem", "One engineer covers everything, no gaps."),
            us([[[0, 5]]], 2, "Never enough", "One engineer can never satisfy m = 2: the whole range."),
            us([[[0, 4]], [[4, 8]]], 1, "Handover at one instant", "End at 4 and start at 4 leave no gap."),
            us([[[0, 10]], [[0, 10]], [[5, 10]]], 3, "Duplicates", "Two identical shifts plus a late third."),
            us([[[0, 3], [6, 9]], [[1, 7]], [[2, 8]]], 2, "Several windows", "Count rises and falls; merge adjacent stretches."),
            {"args": _staff_large(), "why": {"t": "Large input", "d": "20 engineers with 15 shifts each, m = 3."}},
        ],
        "solutions": [
            {"name": "Event sweep (Optimal)",
             "description": "Sort +1/-1 events. Walk distinct times; after applying a time's events, the stretch to the next time is understaffed if the count is below m. Merge touching windows.",
             "time": "O(N log N)", "space": "O(N)",
             "keyPoints": ["Apply all events at one time together", "The count is constant between event times", "Merge touching windows"],
             "code": '''def understaffed(schedules, m):
    events = {}
    for person in schedules:
        for s, e in person:
            events[s] = events.get(s, 0) + 1
            events[e] = events.get(e, 0) - 1
    times = sorted(events)
    out = []
    on = 0
    for a, b in zip(times, times[1:]):
        on += events[a]
        if on < m:
            if out and out[-1][1] == a:
                out[-1][1] = b
            else:
                out.append([a, b])
    return out
'''},
            {"name": "Count every stretch", "slow": True,
             "description": "Collect all boundary times. For each stretch between neighbors, count the shifts covering it by scanning every shift.",
             "time": "O(N²)", "space": "O(N)",
             "keyPoints": ["No event bookkeeping", "Rescans every shift per stretch"],
             "code": '''def understaffed(schedules, m):
    shifts = [s for person in schedules for s in person]
    times = sorted({t for s in shifts for t in s})
    out = []
    for a, b in zip(times, times[1:]):
        on = sum(1 for s, e in shifts if s <= a and b <= e)
        if on < m:
            if out and out[-1][1] == a:
                out[-1][1] = b
            else:
                out.append([a, b])
    return out
'''},
        ],
        "starter": '''def understaffed(schedules, m):
    """Maximal [start, end] windows with fewer than m engineers on call."""
    pass
''',
    },
    {
        "key": "unpaged-alerts",
        "title": "Alerts that paged nobody",
        "approach": "K-way merge into covered spans, then binary search per alert · O((N + A) log N) · O(N)",
        "spec": {"kind": "fn", "fn": "unpaged_alerts", "params": ["schedules", "alerts"]},
        "statement": (
            "After an incident review, the question is not where the gaps are but which pages actually fell into them.\n\n"
            "`schedules[p]` is engineer `p`'s shifts, `[start, end)` pairs sorted by start and not overlapping each other. "
            "`alerts` is a list of alert times, in any order, possibly repeated.\n\n"
            "An alert at time `t` reaches someone if some shift has `start <= t < end`. Return the alerts that reached nobody, "
            "in their original order."
        ),
        "examples": [
            {"args": {"schedules": [[[0, 8]], [[8, 16]], [[20, 24]]], "alerts": [3, 8, 16, 18, 23]},
             "explanation": "8 is the handover instant and is covered. 16 is the end of a shift (exclusive) and 18 sits in the 16-20 gap.",
             "why": {"t": "Exclusive ends", "d": "An alert exactly at a shift's end is only covered if another shift starts then."}},
        ],
        "constraints": ["0 ≤ schedules.length ≤ 50", "Total shifts N ≤ 2000", "0 ≤ alerts.length ≤ 2000", "0 ≤ times ≤ 10⁹"],
        "hints": [
            "First merge every shift into disjoint covered spans; the per-person lists are already sorted, so heapq.merge works.",
            "Merge spans that overlap or touch, so each alert needs to look at a single span.",
            "For an alert at t, bisect the span starts for the last start <= t and check t < that span's end.",
        ],
        "tests": [
            ua([], [1, 2], "No engineers", "Every alert goes unanswered."),
            ua([[[0, 10]]], [], "No alerts", "Nothing to report."),
            ua([[[5, 10]]], [4, 5, 9, 10], "Both edges", "Just before, on the start, just before the end, on the end."),
            ua([[[0, 5]], [[5, 10]]], [11, 5, 5, 11], "Repeated alerts", "A handover at 5 covers both pages; the repeated 11 is reported twice."),
            ua([[[0, 100]], [[10, 20], [30, 40]]], [25, 99, 100], "Nested shifts", "A long shift covers the gaps between short ones."),
            ua([[[0, 1]], [[1_000_000_000, 1_000_000_001]]], [500_000_000, 1_000_000_000], "Huge times", "Epoch-sized times rule out a timeline of cells."),
            {"args": _alerts_large(), "why": {"t": "Large input", "d": "400 shifts and 400 alerts."}},
        ],
        "solutions": [
            {"name": "Merge spans + binary search (Optimal)",
             "description": "k-way merge the shifts into disjoint, non-touching covered spans. Each alert bisects the span starts and checks the one span that could hold it.",
             "time": "O(N log k + A log N)", "space": "O(N)",
             "keyPoints": ["Merge touching spans so one lookup suffices", "Ends are exclusive", "Keep the alerts' original order"],
             "code": '''import heapq
from bisect import bisect_right


def unpaged_alerts(schedules, alerts):
    starts, ends = [], []
    for s, e in heapq.merge(*schedules):
        if ends and s <= ends[-1]:
            ends[-1] = max(ends[-1], e)
        else:
            starts.append(s)
            ends.append(e)
    out = []
    for t in alerts:
        i = bisect_right(starts, t) - 1
        if i < 0 or t >= ends[i]:
            out.append(t)
    return out
'''},
            {"name": "Check every shift", "slow": True,
             "description": "For each alert, scan every shift of every engineer for one that contains it.",
             "time": "O(A · N)", "space": "O(1) extra",
             "keyPoints": ["No preprocessing", "Every alert rescans the whole rota"],
             "code": '''def unpaged_alerts(schedules, alerts):
    shifts = [s for person in schedules for s in person]
    return [t for t in alerts if not any(s <= t < e for s, e in shifts)]
'''},
        ],
        "starter": '''def unpaged_alerts(schedules, alerts):
    """Alerts (in original order) that fired while nobody was on call."""
    pass
''',
    },
]
