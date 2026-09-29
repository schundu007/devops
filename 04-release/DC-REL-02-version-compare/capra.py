"""Capra Playground export for DC-REL-02 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "compare_versions", "params": ["a", "b"], "types": {}, "ret": "value", "cmp": "exact"}


def case(a, b):
    return {"a": a, "b": b}


EXAMPLES = [
    {"args": case("1.27.10", "1.27.9"),
     "explanation": "Compare part by part as numbers: 10 > 9, so a is newer. A plain string compare gets this wrong ('1' < '9').",
     "why": {"t": "Multi-digit part", "d": "The classic string-compare trap."}},
    {"args": case("1.0", "1.0.0"),
     "explanation": "A missing part counts as 0, so 1.0 and 1.0.0 are the same release.",
     "why": {"t": "Different lengths", "d": "Trailing zero parts do not change the version."}},
    {"args": case("2.01", "2.1"),
     "explanation": "Leading zeros are ignored: 01 and 1 are both 1.",
     "why": {"t": "Leading zeros", "d": "Parts compare as integers, not strings."}},
]


def _large():
    rng = random.Random(165)
    parts = [str(rng.randint(0, 999)) for _ in range(400)]
    b = parts[:]
    b[-1] = str(int(b[-1]) + 1)
    return case(".".join(parts), ".".join(b))


TESTS = [
    {"args": case("1", "1"), "why": {"t": "Single part · equal", "d": "One-part versions that match."}},
    {"args": case("0.1", "1.1"), "why": {"t": "First part decides", "d": "Older major version."}},
    {"args": case("1.2", "1.10"), "why": {"t": "Minor 2 vs 10", "d": "Numeric compare on the second part."}},
    {"args": case("1.0.1", "1"), "why": {"t": "Longer is newer", "d": "Extra non-zero part makes a newer version."}},
    {"args": case("1.0.0.0.0", "1"), "why": {"t": "Many trailing zeros", "d": "All trailing parts are zero."}},
    {"args": case("7.5.2.4", "7.5.3"), "why": {"t": "Decided before the end", "d": "Part 3 differs before the longer list runs out."}},
    {"args": case("1.001", "1.01"), "why": {"t": "Leading zeros both sides", "d": "001 and 01 are both 1."}},
    {"args": case("1.28.0", "1.27.15"), "why": {"t": "Kubernetes upgrade check", "d": "Is the cluster's 1.28.0 newer than the fixed-in version 1.27.15?"}},
    {"args": case("3.10.2", "3.9.18"), "why": {"t": "Python CVE check", "d": "Installed 3.10.2 vs fixed-in 3.9.18."}},
    {"args": _large(), "why": {"t": "Large input", "d": "400-part versions that differ only in the last part."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Split and compare as integers (Optimal)",
     "description": "Split both versions on dots. Walk the longer list; a missing part counts as 0. Compare each pair as integers and return at the first difference.",
     "time": "O(len(a) + len(b))", "space": "O(len(a) + len(b))",
     "keyPoints": ["int() drops leading zeros", "A missing part is 0", "Return at the first differing part"]},
    {"name": "Pad and compare tuples",
     "description": "Turn each version into a list of integers, pad the shorter one with zeros, then let Python compare the two lists.",
     "time": "O(len(a) + len(b))", "space": "O(len(a) + len(b))",
     "keyPoints": ["Python compares lists element by element", "Padding makes 1.0 equal 1.0.0"],
     "code": '''from __future__ import annotations


def compare_versions(a: str, b: str) -> int:
    x = [int(p) for p in a.split(".")]
    y = [int(p) for p in b.split(".")]
    width = max(len(x), len(y))
    x += [0] * (width - len(x))
    y += [0] * (width - len(y))
    return (x > y) - (x < y)
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Split and compare", "idea": "Split on dots and compare part by part as integers, treating a missing part as 0.",
     "time": "O(n)", "space": "O(n)", "use": "The standard answer; easy to explain."},
    {"name": "Pad and compare lists", "idea": "Convert to integer lists, pad with zeros, compare the lists.",
     "time": "O(n)", "space": "O(n)", "use": "Shortest code in languages with list comparison."},
    {"name": "Two pointers, no split", "idea": "Scan both strings, building one number at a time up to the next dot.",
     "time": "O(n)", "space": "O(1)", "use": "When memory matters or versions are huge."},
]

VARIANT_TITLE = "Compare two versions"
VARIANT_APPROACH = "Split and compare as integers · O(n) · O(n)"


def _sort_large():
    rng = random.Random(1650)
    out = []
    for _ in range(250):
        parts = [str(rng.randint(0, 12)) for _ in range(rng.randint(1, 4))]
        if rng.random() < 0.2:
            parts.append("0")
        out.append(".".join(parts))
    return {"versions": out}


def _safe_large():
    rng = random.Random(4242)
    avail = [f"{rng.randint(1, 3)}.{rng.randint(0, 30)}.{rng.randint(0, 20)}" for _ in range(300)]
    banned = rng.sample(sorted(set(avail)), 25)
    return {"available": avail, "minimum": "2.10", "banned": banned}


VARIANTS = [
    {
        "key": "sort-releases",
        "title": "Order a release list",
        "approach": "Sort by normalized integer tuple · O(n log n · L) · O(n · L)",
        "spec": {"kind": "fn", "fn": "sort_versions", "params": ["versions"]},
        "statement": (
            "The release page lists tags in the order they were pushed. Show them oldest to newest instead.\n\n"
            "Versions follow the same rules as the main problem: parts compare as integers, leading zeros are "
            "ignored and missing parts count as `0`. Versions that are equal (like `1.2` and `1.2.0`) keep their "
            "original relative order.\n\n"
            "Return the sorted list of the original strings."
        ),
        "examples": [
            {"args": {"versions": ["1.10", "1.9", "1.2.0", "1.2"]},
             "explanation": "1.2.0 and 1.2 are equal and stay in input order; 1.9 comes before 1.10.",
             "why": {"t": "Stable ties", "d": "Equal versions keep their original order."}},
        ],
        "constraints": ["0 ≤ len(versions) ≤ 10^4", "Each version is 1 to 500 characters of digits and dots, no empty parts", "Every part fits in a 32-bit signed integer"],
        "hints": [
            "Turn each version into a tuple of integers, then drop trailing zeros so 1.2 and 1.2.0 get the same key.",
            "Python's sort is stable, so equal keys keep input order for free.",
        ],
        "tests": [
            {"args": {"versions": []}, "why": {"t": "Empty", "d": "No tags."}},
            {"args": {"versions": ["3"]}, "why": {"t": "Single tag", "d": "Already sorted."}},
            {"args": {"versions": ["1.0.0", "1", "1.0", "01"]}, "why": {"t": "All equal", "d": "Four spellings of the same release keep their order."}},
            {"args": {"versions": ["2.0", "1.10.1", "1.2.10", "1.2.9", "0.9"]}, "why": {"t": "Multi-digit parts", "d": "The string-sort trap on several parts."}},
            {"args": {"versions": ["1.28.0", "1.27.15", "1.29", "1.27.9", "1.28"]}, "why": {"t": "Kubernetes tags", "d": "Patch releases across three minors."}},
            {"args": _sort_large(), "why": {"t": "Large input", "d": "250 random versions with duplicates and trailing zeros."}},
        ],
        "solutions": [
            {"name": "Normalized key + stable sort (Optimal)",
             "description": "Map each version to its integer parts with trailing zeros removed and sort by that tuple.",
             "time": "O(n log n · L)", "space": "O(n · L)",
             "keyPoints": ["Stripping trailing zeros makes equal versions equal keys", "Each key is built once, not per comparison", "Stable sort keeps ties in input order"],
             "code": '''def sort_versions(versions):
    def key(v):
        parts = [int(p) for p in v.split(".")]
        while parts and parts[-1] == 0:
            parts.pop()
        return parts

    return sorted(versions, key=key)
'''},
            {"name": "Insertion sort with compare", "slow": True,
             "description": "Insert each version into the result, walking left past every strictly newer version using the main problem's compare.",
             "time": "O(n² · L)", "space": "O(n)",
             "keyPoints": ["Reuses compare_versions directly", "Re-parses on every comparison", "Stops at equal versions, so it is stable"],
             "code": '''def compare(a, b):
    x = [int(p) for p in a.split(".")]
    y = [int(p) for p in b.split(".")]
    w = max(len(x), len(y))
    x += [0] * (w - len(x))
    y += [0] * (w - len(y))
    return (x > y) - (x < y)


def sort_versions(versions):
    out = []
    for v in versions:
        i = len(out)
        while i > 0 and compare(out[i - 1], v) > 0:
            i -= 1
        out.insert(i, v)
    return out
'''},
        ],
        "starter": '''def sort_versions(versions: list[str]) -> list[str]:
    """Oldest to newest; equal versions keep input order."""
    raise NotImplementedError
''',
    },
    {
        "key": "latest-safe-version",
        "title": "Newest safe upgrade target",
        "approach": "One pass with normalized tuples + banned set · O((n + b) · L) · O(b · L)",
        "spec": {"kind": "fn", "fn": "latest_safe", "params": ["available", "minimum", "banned"]},
        "statement": (
            "A dependency bot picks the upgrade target for a service. It must be at least `minimum` (the first "
            "release with the security fix) and must not be any release in `banned` (known-bad builds).\n\n"
            "Compare versions as in the main problem, so `1.2` and `1.2.0` are the same release (and both are banned "
            "if either is listed).\n\n"
            "Return the newest acceptable string from `available`. If several spellings of that release exist, "
            "return the first one in `available`. If nothing qualifies, return `\"\"`."
        ),
        "examples": [
            {"args": {"available": ["1.27.9", "1.28.3", "1.28.4", "1.27.15"], "minimum": "1.27.10", "banned": ["1.28.4"]},
             "explanation": "1.28.4 is banned, so 1.28.3 is the newest release at or above 1.27.10.",
             "why": {"t": "Skip a banned build", "d": "The newest release is known-bad."}},
            {"args": {"available": ["2.0", "1.9"], "minimum": "2.0.1", "banned": []},
             "explanation": "Nothing reaches the fixed-in version 2.0.1.",
             "why": {"t": "None qualifies", "d": "Return an empty string."}},
        ],
        "constraints": ["0 ≤ len(available), len(banned) ≤ 10^4", "Versions are 1 to 500 characters of digits and dots, no empty parts"],
        "hints": [
            "Normalize every version once: integer parts, trailing zeros removed. Equal releases get equal tuples.",
            "Put the normalized banned versions in a set for O(1) lookups.",
            "Scan once, keeping the best tuple; replace only when strictly newer so the first spelling wins.",
        ],
        "tests": [
            {"args": {"available": [], "minimum": "1", "banned": []}, "why": {"t": "Nothing available", "d": "Empty list."}},
            {"args": {"available": ["1.0"], "minimum": "1", "banned": []}, "why": {"t": "Exactly the minimum", "d": "The minimum itself is allowed."}},
            {"args": {"available": ["3.1", "3.1.0", "3.0"], "minimum": "3", "banned": ["3.01.0"]}, "why": {"t": "Banned by another spelling", "d": "3.01.0 bans 3.1 and 3.1.0."}},
            {"args": {"available": ["2.1.0", "2.1", "2.0"], "minimum": "1", "banned": []}, "why": {"t": "Two spellings of the newest", "d": "The first one listed wins."}},
            {"args": {"available": ["5", "4", "3"], "minimum": "1", "banned": ["5", "4", "3"]}, "why": {"t": "All banned", "d": "Nothing left."}},
            {"args": {"available": ["3.10.2", "3.9.18", "3.11.0", "3.12.1"], "minimum": "3.10", "banned": ["3.12.1", "3.11"]}, "why": {"t": "Python runtime pick", "d": "Two newer builds are banned."}},
            {"args": _safe_large(), "why": {"t": "Large input", "d": "300 versions and 25 banned ones."}},
        ],
        "solutions": [
            {"name": "Normalize once, single pass (Optimal)",
             "description": "Normalize the minimum and every banned version into a set. Scan available once, keeping the newest normalized tuple that passes both checks.",
             "time": "O((n + b) · L)", "space": "O(b · L)",
             "keyPoints": ["Normalization makes set lookup match equal releases", "Strictly-newer replacement keeps the first spelling", "No sorting needed for a maximum"],
             "code": '''def latest_safe(available, minimum, banned):
    def norm(v):
        parts = [int(p) for p in v.split(".")]
        while parts and parts[-1] == 0:
            parts.pop()
        return tuple(parts)

    low = norm(minimum)
    bad = {norm(v) for v in banned}
    best, best_key = "", None
    for v in available:
        k = norm(v)
        if k >= low and k not in bad and (best_key is None or k > best_key):
            best, best_key = v, k
    return best
'''},
            {"name": "Sort, then check every ban", "slow": True,
             "description": "Sort available newest first with the pairwise compare, then walk down and compare each candidate against the minimum and every banned version.",
             "time": "O(n log n · L + n · b · L)", "space": "O(n)",
             "keyPoints": ["Reuses compare_versions for every check", "Ban check is a linear scan per candidate"],
             "code": '''from functools import cmp_to_key


def compare(a, b):
    x = [int(p) for p in a.split(".")]
    y = [int(p) for p in b.split(".")]
    w = max(len(x), len(y))
    x += [0] * (w - len(x))
    y += [0] * (w - len(y))
    return (x > y) - (x < y)


def latest_safe(available, minimum, banned):
    for v in sorted(available, key=cmp_to_key(compare), reverse=True):
        if compare(v, minimum) >= 0 and all(compare(v, b) != 0 for b in banned):
            return v
    return ""
'''},
        ],
        "starter": '''def latest_safe(available: list[str], minimum: str, banned: list[str]) -> str:
    """Newest available version >= minimum and not banned, or ""."""
    raise NotImplementedError
''',
    },
]
