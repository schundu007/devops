"""Capra Playground export for DC-SEC-08 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "matches", "params": ["pattern", "value"], "types": {}, "ret": "value", "cmp": "exact"}


def case(pattern, value):
    return {"pattern": pattern, "value": value}


EXAMPLES = [
    {"args": case("s3:Get*", "s3:GetObject"),
     "explanation": "`*` swallows `Object`, so the whole action matches.",
     "why": {"t": "Trailing star", "d": "The most common IAM action pattern."}},
    {"args": case("arn:aws:s3:::logs-*/2026/*", "arn:aws:s3:::logs-prod/2025/01/app.log"),
     "explanation": "The bucket part matches, but the object key starts with 2025, not 2026.",
     "why": {"t": "Star in the middle", "d": "A star inside an ARN must not let a later literal part slip."}},
    {"args": case("s3:?etObject", "s3:GetObject"),
     "explanation": "`?` matches exactly one character: `G`.",
     "why": {"t": "Single-character wildcard", "d": "`?` stands for exactly one character."}},
]


def _large():
    rng = random.Random(8)
    value = "".join(rng.choice("ab") for _ in range(1500)) + "c"
    pattern = "*" + "*".join("ab" for _ in range(40)) + "*c"
    return case(pattern, value)


TESTS = [
    {"args": case("", ""), "why": {"t": "Both empty", "d": "An empty pattern matches only the empty value."}},
    {"args": case("*", ""), "why": {"t": "Star matches nothing", "d": "`*` can match an empty run."}},
    {"args": case("?", ""), "why": {"t": "Question mark needs a character", "d": "`?` cannot match an empty value."}},
    {"args": case("", "s3:GetObject"), "why": {"t": "Empty pattern", "d": "An empty pattern grants nothing."}},
    {"args": case("s3:GetObject", "s3:getobject"), "why": {"t": "Case-sensitive", "d": "Actions are compared case-sensitively here."}},
    {"args": case("s3:*", "s3:PutObject/../../iam"), "why": {"t": "Star crosses separators", "d": "`*` matches `:` and `/` too, as in IAM."}},
    {"args": case("arn:aws:s3:::logs-*/2026/*", "arn:aws:s3:::logs-prod/2026/01/app.log"),
     "why": {"t": "ARN match", "d": "Two stars, each matching part of the resource."}},
    {"args": case("s3:Get*Tagging", "s3:GetObjectTaggingX"), "why": {"t": "Suffix after star", "d": "The text after the star must end the value."}},
    {"args": case("***", "iam:PassRole"), "why": {"t": "Repeated stars", "d": "Several stars in a row act like one."}},
    {"args": case("a*b*c", "abcbc"), "why": {"t": "Backtracking", "d": "The first guess for a star is wrong and must be retried."}},
    {"args": case("?*?", "x"), "why": {"t": "Too short", "d": "Two `?` need at least two characters."}},
    {"args": case("s3:GetObject", "s3:GetObject"), "why": {"t": "Exact literal", "d": "No wildcards: the strings must be equal."}},
    {"args": _large(), "why": {"t": "Large input", "d": "A 1,500-character value against a pattern with 41 stars."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Greedy two pointers (Optimal)",
     "description": "Walk pattern and value together. On `*`, remember where it is and let it match nothing first. On a mismatch, go back to the last `*` and let it swallow one more character. When the value is used up, only `*`s may remain.",
     "time": "O(n·m) worst case, near-linear in practice", "space": "O(1)",
     "keyPoints": ["Only the most recent `*` ever needs to be retried", "Match `?` or an equal character by advancing both pointers", "Trailing stars can match nothing"]},
    {"name": "Dynamic programming", "slow": True,
     "description": "dp[i][j] is True when the first i pattern characters match the first j value characters. A `*` takes dp[i-1][j] (matches nothing) or dp[i][j-1] (matches one more character).",
     "time": "O(n·m)", "space": "O(n·m)",
     "keyPoints": ["Easy to prove correct", "Uses a full table; a rolling row brings space to O(m)"],
     "code": '''from __future__ import annotations


def matches(pattern: str, value: str) -> bool:
    n, m = len(pattern), len(value)
    dp = [[False] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = True
    for i in range(1, n + 1):
        if pattern[i - 1] == "*":
            dp[i][0] = dp[i - 1][0]
    for i in range(1, n + 1):
        p = pattern[i - 1]
        for j in range(1, m + 1):
            if p == "*":
                dp[i][j] = dp[i - 1][j] or dp[i][j - 1]
            elif p == "?" or p == value[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
    return dp[n][m]
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Dynamic programming", "idea": "Table of prefix matches; `*` extends from the left or from above.",
     "time": "O(n·m)", "space": "O(n·m) or O(m)", "use": "Easiest to reason about and to prove."},
    {"name": "Greedy two pointers", "idea": "Remember only the last `*` and backtrack to it on a mismatch.",
     "time": "O(n·m) worst, fast in practice", "space": "O(1)", "use": "Policy engines evaluating millions of requests."},
]
