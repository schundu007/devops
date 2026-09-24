Source: New

# DC-REL-01 · Find the Breaking Commit ★

## 1. Header
| | |
|---|---|
| Chip ID | DC-REL-01 ★ (start here) |
| Difficulty | Easy |
| Pattern | Binary search |
| Track | Release & CI/CD (REL) |
| Classic pattern | LeetCode 278 |
| Premium | No |
| Time box | 15 min |
| Source | New |

## 2. The Scenario
Release `v1.28.0` of `payments-svc` is blocked. The integration suite passed on tag
`v1.27.3` and fails on `main`, and 40 commits landed in between. One full CI run takes 18
minutes. Testing all 40 commits one by one would take 12 hours. You need the first commit
that broke the suite, using as few CI runs as possible.

## 3. Why This Is DevOps
**Production reality:** When a regression shows up between a known good build and a known
bad build, the history between them splits into two parts: good commits, then bad ones.
Finding the boundary is a binary search. Test the middle commit, keep the half that
contains the change from good to bad, and repeat. `git bisect` does exactly this: you mark
one good and one bad commit, and it checks out the commit in the middle for you to test.
`git bisect run ./test.sh` automates the loop with a script's exit code.

**Where you see it:** `git bisect` (and `git bisect run`), Mercurial `hg bisect`, CI
"culprit finder" jobs that bisect nightly failures, performance-regression bots.

**Reality check:** Real history is a graph with merges, not a straight line. `git bisect`
picks commits that split the remaining candidates roughly in half, and lets you `skip`
commits that do not build (exit code 125 in `git bisect run`). A flaky test breaks the
"all bad after the first bad" rule, so the answer can be wrong.

**What breaks if you get it wrong:** An off-by-one blames the commit next to the real one.
The wrong change gets reverted, the release still fails, and the team loses another half day.

## 4. Problem Statement
Commits are numbered `1..n` in history order. Some commit broke the build, and every commit
from that one onward is bad. Every commit before it is good. Commit `n` (HEAD) is known
to be bad.

You get `is_bad(commit)`, which runs the full CI suite on one commit and returns `True` if
it fails. Return the number of the first bad commit, calling `is_bad` as few times as
possible.

## 5. Input / Output format and Constraints
- `first_bad_commit(n: int, is_bad: Callable[[int], bool]) -> int`
- `1 <= n <= 2^31 - 1`
- `is_bad` is monotonic: `False` for commits before the answer, `True` from it onward.
- Commit `n` is bad, so an answer always exists.
- Target: at most `ceil(log2 n)` calls to `is_bad`.

## 6. Examples
**Example 1**
```
n = 5, commits 4 and 5 fail
first_bad_commit(5, is_bad) -> 4
```
Test 3 (good), then 4 (bad), and the range shrinks to just commit 4.

**Example 2: a single commit (edge case)**
```
n = 1
first_bad_commit(1, is_bad) -> 1
```
HEAD is known to be bad and there is nothing else, so no CI run is needed at all.

**Example 3: the very first commit**
```
n = 10, all commits fail
first_bad_commit(10, is_bad) -> 1
```

## 7. Starter Code
See [`starter.py`](starter.py): `first_bad_commit(n, is_bad)` with a docstring and type hints.

```bash
make try CHIP=04-release/DC-REL-01-breaking-commit
```

## 8. Hints
1. **Nudge:** If you test commit 20 and it passes, what do you now know about commits 1–19?
2. **Pattern:** The answers form `good…good bad…bad`. Binary search for the first `True`.
3. **Near-solution:** Keep `lo = 1, hi = n`. While `lo < hi`: `mid = lo + (hi - lo) // 2`. If
   `is_bad(mid)`, set `hi = mid`, else `lo = mid + 1`. Return `lo`.

## 9. Solution
**Approach**
1. The first bad commit is always inside `[lo, hi]`. Start with `[1, n]`, because `n` is bad.
2. Test the middle commit.
3. If it is bad, the answer is it or earlier: `hi = mid`.
4. If it is good, the answer is later: `lo = mid + 1`.
5. Stop when `lo == hi`. That commit is the answer.

**Brute force:** Test commits 1, 2, 3… until one fails. That is O(n) CI runs: 40 runs of 18
minutes for this release, and billions for a large `n`.

**Optimal code:** [`solution.py`](solution.py)

```python
def first_bad_commit(n: int, is_bad: Callable[[int], bool]) -> int:
    lo, hi = 1, n  # the answer is always inside [lo, hi]
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if is_bad(mid):
            hi = mid          # mid is bad: the first bad one is mid or earlier
        else:
            lo = mid + 1      # mid is good: the first bad one is after it
    return lo
```

`hi = mid` (not `mid - 1`) keeps a bad `mid` inside the range, because it may be the first
bad one. `lo + (hi - lo) // 2` avoids overflow in languages with fixed-size integers.

**Complexity**
- Time: O(log n) calls to `is_bad`, because every call halves the range.
- Space: O(1), because only two bounds are stored.

## 10. Tests
[`test_chip.py`](test_chip.py) has 6 tests. A fake CI object counts every `is_bad` call, so
the tests check the run count as well as the answer. They cover a normal case, a single
commit, the first and last commits, `n = 2^31 - 1` in at most 31 runs, the 40-commit
release scenario in at most 6 runs, and 300 random cases against a linear scan.

## 11. Interview Talk Track
"This is `git bisect`. I know one good commit and one bad one, and the history between them
is good commits followed by bad commits, so the first bad commit is a boundary I can binary
search. I test the middle. If it fails, the culprit is there or earlier. If it passes, it's
later. Every CI run halves the range, so 40 commits take at most 6 runs instead of 40, and a
million commits take 20. Two details matter. When `mid` is bad I keep it in the range,
because it might be the first bad one. And in practice history has merges and flaky tests,
so `git bisect` lets you skip commits that don't build, and I'd rerun a flaky test before
trusting its result."

## 12. Level Up
1. **"Some commits don't compile, so you can't test them."** Mark them as skipped and test a
   commit next to them instead. If the skipped ones sit right at the boundary, report a
   small range of possible culprits, not one commit. This is `git bisect skip`.
2. **"Each run is 18 minutes, but you have 8 CI runners."** Test 7 evenly spaced commits in
   parallel. The results split the range into 8 parts and you keep one, so each round divides
   the range by 8 instead of 2. That is about log₈ n rounds of wall-clock time.
3. **"The test is flaky: it fails 5% of the time on good commits."** One false "bad" sends the
   search into the wrong half for good. Rerun each result a few times and take the majority, or
   rerun whenever a result disagrees with its neighbours. The goal is to make each answer
   reliable before you narrow the range.

## 13. Related Chips
- **DC-REL-08 Versioned Config Store**: binary search over snapshot IDs.
- **DC-CAP-01 Backlog Drain Rate**: binary search on the answer, the same "first value that works" boundary.
- **DC-OBS-01 Metric Point-in-Time Lookup**: binary search for the last sample at or before a time.
