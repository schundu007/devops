Source: New

# DC-SEC-08 · IAM Wildcard Matcher ★

## 1. Header
| | |
|---|---|
| Chip ID | DC-SEC-08 ★ Start here |
| Difficulty | Hard |
| Pattern | DP / greedy two pointers |
| Track | Cloud Security & IAM (SEC) |
| Classic pattern | LeetCode 44 |
| Premium | No |
| Time box | 40 min |
| Source | New |

## 2. The Scenario
You are building a pre-deploy policy linter. A new role for the log-shipping service has this
statement: `Allow` actions `s3:Get*` and `s3:List*` on
`arn:aws:s3:::logs-*/2026/*`. The linter replays last week's 40,000 access requests from
CloudTrail against the draft policy to show what would be allowed. For each request, it must
decide whether the action and the resource ARN match the policy's wildcard patterns. If the
matcher is wrong, the linter's report is wrong, and a reviewer approves the wrong access.

## 3. Why This Is DevOps
**Production reality:** IAM policies match actions and ARNs with wildcards. In an ARN,
`*` matches any run of characters and `?` matches exactly one, and for S3 object ARNs `*` also
matches `/`, so `logs-*/2026/*` covers every key under 2026 in every `logs-` bucket. The
policy engine must decide, for every request, whether the pattern matches. The classic
wildcard-matching algorithm is exactly this decision.

**Where you see it:** AWS IAM `Action`, `Resource` and `StringLike` conditions, S3 bucket
policies, and Kubernetes RBAC (which uses a single `*` for "all", a simpler case). Shell
globs (`fnmatch`) follow the same `*` and `?` rules.

**Reality check:** Matching is one step. The real IAM evaluation also combines identity and
resource policies, gives an explicit `Deny` priority over any `Allow`, handles `NotAction` and
`NotResource`, and fills in policy variables such as `${aws:username}`. Action names are
case-insensitive, while most ARN parts are case-sensitive, so the caller decides whether to
lowercase first.

**What breaks if you get it wrong:** A matcher that treats `s3:Get*` as a prefix check but
forgets to anchor the end lets `s3:GetObject` pass for a pattern like `s3:Get`. One that is not
anchored at the start matches `billing-logs-prod` against `logs-*`. Both silently grant access.
Going the other way and blocking valid requests takes down the log pipeline.

## 4. Problem Statement
Write `matches(pattern, value)`. It returns `True` if the **whole** of `value` matches the
**whole** of `pattern`:

- `*` matches any sequence of characters, including an empty one, and including `:` and `/`.
- `?` matches exactly one character.
- Every other character matches only itself, case-sensitive.

## 5. Input / Output format and Constraints
- `matches(pattern: str, value: str) -> bool`.
- `0 <= len(pattern), len(value) <= 2000`.
- Characters are printable ASCII. `*` and `?` are always wildcards (there is no escaping).

## 6. Examples
**Example 1: an S3 resource ARN**
```
matches("arn:aws:s3:::logs-*/2026/*", "arn:aws:s3:::logs-prod/2026/03/14/app.log")  -> True
matches("arn:aws:s3:::logs-*/2026/*", "arn:aws:s3:::logs-prod/2025/12/31/app.log")  -> False
```

**Example 2: whole-string match (edge case)**
```
matches("s3:Get", "s3:GetObject")   -> False   # no '*': the value must end where the pattern ends
matches("*", "")                    -> True    # '*' may match nothing
matches("?", "")                    -> False   # '?' needs exactly one character
```

**Example 3: `?`**
```
matches("ec2:Describe?nstances", "ec2:DescribeInstances") -> True
```

## 7. Starter Code
See [`starter.py`](starter.py): `matches` with a docstring and type hints. The body is TODO.

```bash
make try CHIP=02-security/DC-SEC-08-iam-wildcard-matcher
```

## 8. Hints
1. **Nudge:** Without `*`, this is a simple walk with two pointers. What choice does a `*` force on you?
2. **Pattern:** A `*` can take 0, 1, 2… characters. Either a DP over (pattern index, value index), or a greedy walk that
   remembers only the **last** `*` and backtracks to it on a mismatch.
3. **Near-solution:** Walk both strings. On `?` or an equal character, advance both. On `*`, save `(star, star_v)` and
   advance the pattern only. On a mismatch with a saved star, set `star_v += 1`, `v = star_v`, `p = star + 1`.
   At the end, skip trailing `*`s and check that the pattern is used up.

## 9. Solution
**Approach (greedy, two pointers)**
1. Keep pointers `p` (pattern) and `v` (value).
2. If `pattern[p]` is `?` or equals `value[v]`, advance both.
3. If `pattern[p]` is `*`, remember its position and where it started in the value. First, let it match nothing.
4. On a mismatch, go back to the last `*` and let it swallow one more character.
5. If there is no `*` to go back to, fail. When the value is used up, the rest of the pattern must be only `*`s.

Only the **last** `*` needs remembering: an earlier `*` could only absorb more of what the later one already can.

**Brute force:** Recursively try every length for every `*`. With k stars this is exponential,
and a hostile pattern like `*a*a*a…b` would hang the policy engine. That is a denial-of-service
risk in anything that matches untrusted patterns.

**DP alternative:** `dp[i][j]` = "the first i pattern characters match the first j value characters".
`*`: `dp[i][j] = dp[i-1][j] or dp[i][j-1]`. `?` or equal: `dp[i][j] = dp[i-1][j-1]`. O(n·m) time and space.

**Optimal code:** [`solution.py`](solution.py)

```python
def matches(pattern: str, value: str) -> bool:
    p = v = 0
    star, star_v = -1, 0          # last '*' in pattern, and where it began in value
    while v < len(value):
        if p < len(pattern) and (pattern[p] == "?" or pattern[p] == value[v]):
            p += 1
            v += 1
        elif p < len(pattern) and pattern[p] == "*":
            star, star_v = p, v   # try matching nothing first
            p += 1
        elif star != -1:
            star_v += 1           # let the last '*' swallow one more character
            v = star_v
            p = star + 1
        else:
            return False
    while p < len(pattern) and pattern[p] == "*":
        p += 1
    return p == len(pattern)
```

**Complexity**
- Time: O(n·m) in the worst case (each backtrack moves `star_v` forward, and each retry scans at
  most the pattern), and close to O(n + m) on typical policies.
- Space: O(1): four integers. The DP version needs O(n·m), or O(m) with a rolling row.

## 10. Tests
[`test_chip.py`](test_chip.py) has 10 cases: five normal patterns, empty and single-character
inputs, whole-string anchoring, a production S3 log-bucket policy (with `*` spanning `/`, an empty
`*`, start anchoring and lowercase actions), a large random check (3,000 random pairs against
`fnmatch.fnmatchcase` as an independent reference), and a many-star worst case that must not hang.

## 11. Interview Talk Track
"IAM matches actions and ARNs with `*` and `?`, so the policy engine needs a correct, fast
wildcard matcher. The hard part is `*`, because it can take any number of characters. Pure
recursion is exponential, which is a denial-of-service risk if patterns come from users. I'd use
a greedy two-pointer walk: match `?` and literal characters directly, and when I see a `*`,
remember it and first let it match nothing. On a mismatch, I go back to the last star and let it
eat one more character. Only the last star matters, because earlier stars can't do anything the
last one can't. That's O(1) memory and O(n·m) worst case. The security details are anchoring,
because the whole value must match, not a prefix, and case: action names are case-insensitive, ARNs mostly aren't."

## 12. Level Up
1. **"Check 40,000 requests against 500 statements."** Don't run every pattern for every request.
   Index statements by their literal prefix before the first wildcard (`s3:Get`, `arn:aws:s3:::logs-`)
   in a trie, and only run the matcher on statements whose prefix fits. Cache results per
   (pattern, value), since CloudTrail traffic repeats a lot.
2. **"Is policy A broader than policy B?"** Matching single values doesn't answer that. You need
   to compare pattern languages: build a small automaton for each pattern and check containment.
   AWS's policy analysis (IAM Access Analyzer) uses automated reasoning for questions like this,
   rather than testing samples.
3. **"Why not just use a regex?"** Translating patterns into regexes invites escaping bugs (`.`
   in an ARN is a literal, not "any character") and some regex engines backtrack exponentially on
   nested quantifiers. A purpose-built matcher with a known worst case is safer on untrusted input.

## 13. Related Chips
- **DC-SEC-11 Redundant Prefix Grant Cleaner**: deciding when one grant already covers another.
- **DC-SEC-17 Streaming Secret Scanner**: matching many patterns against text as it arrives.
- **DC-SEC-01 Path Traversal Guard**: another security check where a wrong edge case means access.
