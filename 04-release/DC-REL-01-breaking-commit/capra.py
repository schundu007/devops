"""Capra Playground export for DC-REL-01 (see tools/export_capra.py).

The user's first_bad_commit(n, is_bad) receives a callback, so a driver builds
a fake CI that counts runs. It returns the answer and whether the number of CI
runs stayed within ceil(log2 n), the bound git bisect meets.
"""

SPEC = {"kind": "driver", "fn": "first_bad_commit", "params": ["n", "first_bad"], "types": {}, "ret": "value", "cmp": "exact"}

DRIVER = '''
def __drive(args):
    n, first_bad = args["n"], args["first_bad"]
    runs = [0]

    def is_bad(commit):
        runs[0] += 1
        if not 1 <= commit <= n:
            raise ValueError("is_bad(%r): commits are numbered 1..%d" % (commit, n))
        return commit >= first_bad

    answer = first_bad_commit(n, is_bad)
    limit = (n - 1).bit_length()  # ceil(log2 n)
    return {"first_bad": answer, "ci_runs_within_limit": runs[0] <= limit, "limit": limit}
'''


def case(n, first_bad):
    return {"n": n, "first_bad": first_bad}


EXAMPLES = [
    {"args": case(5, 4),
     "explanation": "Commits 1-3 pass and 4-5 fail, so the first bad commit is 4. Binary search needs at most ceil(log2 5) = 3 CI runs.",
     "why": {"t": "Middle commit", "d": "The break sits in the middle of the range."}},
    {"args": case(1, 1),
     "explanation": "Only one commit, and it is known to be bad: no CI run is needed at all.",
     "why": {"t": "Single commit", "d": "The smallest range: the answer is known without testing."}},
    {"args": case(40, 23),
     "explanation": "40 commits between tag v1.27.3 and HEAD; the 23rd broke the suite. At most 6 CI runs are allowed.",
     "why": {"t": "Release regression", "d": "A realistic bisect between two release tags."}},
]

TESTS = [
    {"args": case(10, 1), "why": {"t": "First commit bad", "d": "The very first commit already broke it."}},
    {"args": case(10, 10), "why": {"t": "Only HEAD bad", "d": "The last commit is the first bad one."}},
    {"args": case(2, 1), "why": {"t": "Two commits · first bad", "d": "Smallest range with a choice to make."}},
    {"args": case(2, 2), "why": {"t": "Two commits · last bad", "d": "Smallest range, break at the end."}},
    {"args": case(1024, 513), "why": {"t": "Power of two", "d": "Exactly 10 runs allowed for 1024 commits."}},
    {"args": case(1025, 1025), "why": {"t": "Just past a power of two", "d": "1025 commits allow 11 runs."}},
    {"args": case(2**31 - 1, 1_000_003), "why": {"t": "Huge range · overflow", "d": "2^31 - 1 commits: lo + (hi - lo) // 2 avoids overflow in fixed-width languages; at most 31 runs."}},
    {"args": case(2**31 - 1, 2**31 - 1), "why": {"t": "Huge range · last bad", "d": "The break is at HEAD of a huge range."}},
    {"args": case(2**31 - 1, 1), "why": {"t": "Huge range · first bad", "d": "The break is at the first of a huge range."}},
    {"args": case(1000, 999), "why": {"t": "Near the end", "d": "One before HEAD."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Binary search (Optimal)",
     "description": "Keep the answer inside [lo, hi]. Test the middle commit: if it is bad, the first bad one is mid or earlier (hi = mid); otherwise it is after mid (lo = mid + 1). Stop when lo == hi.",
     "time": "O(log n) calls to is_bad", "space": "O(1)",
     "keyPoints": ["Commits are good then bad: a sorted, monotone predicate", "hi = mid keeps a bad mid as a candidate", "mid = lo + (hi - lo) // 2 avoids overflow in fixed-width languages"]},
]

WAYS_TO_SOLVE = [
    {"name": "Linear scan", "idea": "Test commits 1, 2, 3, ... until one fails.",
     "time": "O(n) CI runs", "space": "O(1)", "use": "Never for real builds: 40 commits could mean 40 builds."},
    {"name": "Binary search (git bisect)", "idea": "Halve the good/bad range with every CI run.",
     "time": "O(log n) CI runs", "space": "O(1)", "use": "Always: this is what git bisect does."},
]
