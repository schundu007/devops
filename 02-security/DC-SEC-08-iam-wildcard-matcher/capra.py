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

VARIANT_TITLE = "Match one pattern"
VARIANT_APPROACH = "Greedy two pointers · O(n·m) worst, near-linear in practice · O(1)"

_EVAL_FAST = '''def _match(p: str, s: str) -> bool:
    i = j = 0
    star, mark = -1, 0
    while j < len(s):
        if i < len(p) and (p[i] == "?" or p[i] == s[j]):
            i += 1
            j += 1
        elif i < len(p) and p[i] == "*":
            star, mark = i, j
            i += 1
        elif star >= 0:
            i = star + 1
            mark += 1
            j = mark
        else:
            return False
    while i < len(p) and p[i] == "*":
        i += 1
    return i == len(p)


def evaluate(allow: list[str], deny: list[str], action: str) -> str:
    if any(_match(p, action) for p in deny):
        return "Deny"
    if any(_match(p, action) for p in allow):
        return "Allow"
    return "ImplicitDeny"
'''

_EVAL_SLOW = '''def _match(p: str, s: str) -> bool:
    n, m = len(p), len(s)
    dp = [[False] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = True
    for i in range(1, n + 1):
        for j in range(0, m + 1):
            if p[i - 1] == "*":
                dp[i][j] = dp[i - 1][j] or (j > 0 and dp[i][j - 1])
            elif j > 0 and (p[i - 1] == "?" or p[i - 1] == s[j - 1]):
                dp[i][j] = dp[i - 1][j - 1]
    return dp[n][m]


def evaluate(allow: list[str], deny: list[str], action: str) -> str:
    denied = [p for p in deny if _match(p, action)]
    allowed = [p for p in allow if _match(p, action)]
    if denied:
        return "Deny"
    return "Allow" if allowed else "ImplicitDeny"
'''

_GLOB_FAST = '''def glob_match(pattern: str, path: str) -> bool:
    toks = []
    i = 0
    while i < len(pattern):
        if pattern[i] == "*":
            j = i
            while j < len(pattern) and pattern[j] == "*":
                j += 1
            toks.append("**" if j - i >= 2 else "*")
            i = j
        else:
            toks.append(pattern[i])
            i += 1
    m = len(path)
    prev = [False] * (m + 1)
    prev[0] = True
    for t in toks:
        cur = [False] * (m + 1)
        if t == "**":
            cur[0] = prev[0]
            for j in range(1, m + 1):
                cur[j] = prev[j] or cur[j - 1]
        elif t == "*":
            cur[0] = prev[0]
            for j in range(1, m + 1):
                cur[j] = prev[j] or (cur[j - 1] and path[j - 1] != "/")
        else:
            for j in range(1, m + 1):
                c = path[j - 1]
                cur[j] = prev[j - 1] and (c == t if t != "?" else c != "/")
        prev = cur
    return prev[m]
'''

_GLOB_SLOW = '''import re


def glob_match(pattern: str, path: str) -> bool:
    out = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == "*":
            j = i
            while j < len(pattern) and pattern[j] == "*":
                j += 1
            out.append(".*" if j - i >= 2 else "[^/]*")
            i = j
            continue
        out.append("[^/]" if c == "?" else re.escape(c))
        i += 1
    return re.fullmatch("".join(out), path, flags=re.S) is not None
'''


def _ev(allow, deny, action, t, d):
    return {"args": {"allow": allow, "deny": deny, "action": action}, "why": {"t": t, "d": d}}


def _gl(pattern, path, t, d):
    return {"args": {"pattern": pattern, "path": path}, "why": {"t": t, "d": d}}


_rg = random.Random(88)
_BIG_ALLOW = ["s3:%s*" % _rg.choice(["Get", "List", "Put", "Delete"]) + "".join(_rg.choice("ab") for _ in range(3)) for _ in range(60)] + ["ec2:Describe*"]
_BIG_DENY = ["s3:Delete*", "iam:*", "*:*Policy*"]
_BIG_PATH = "services/" + "/".join("mod%d" % i for i in range(60)) + "/internal/handler_test.go"

VARIANTS = [
    {
        "key": "policy-evaluation",
        "title": "Allow, deny, implicit deny",
        "approach": "Greedy matcher per statement, deny first · O(P · n·m) worst · O(1)",
        "spec": {"kind": "fn", "fn": "evaluate", "params": ["allow", "deny", "action"], "cmp": "exact"},
        "statement": (
            "Decide one request against an IAM policy's `Allow` and `Deny` statements.\n"
            "\n"
            "### Input\n"
            "- `allow`: the action patterns of the `Allow` statements\n"
            "- `deny`: the action patterns of the `Deny` statements\n"
            "- `action`: the requested action\n"
            "\n"
            "### Output\n"
            "- `\"Deny\"` if **any** deny pattern matches: an explicit deny always wins\n"
            "- Otherwise `\"Allow\"` if any allow pattern matches\n"
            "- Otherwise `\"ImplicitDeny\"`: nothing granted it\n"
            "\n"
            "### Rules\n"
            "- `*` matches any run, including an empty one; `?` matches exactly one character\n"
            "- Matching is case-sensitive and covers the whole action, as in the main problem"
        ),
        "examples": [
            {"args": {"allow": ["s3:*"], "deny": ["s3:Delete*"], "action": "s3:DeleteBucket"},
             "explanation": "Both lists match, and the explicit deny wins.",
             "why": {"t": "Deny beats allow", "d": "The core IAM evaluation rule."}},
            {"args": {"allow": ["ec2:Describe*"], "deny": [], "action": "ec2:RunInstances"},
             "explanation": "No statement matches, so the request is implicitly denied.",
             "why": {"t": "Implicit deny", "d": "Access is never granted by default."}},
        ],
        "constraints": ["0 ≤ allow.length, deny.length ≤ 100", "each pattern and the action ≤ 128 characters"],
        "hints": [
            "Reuse the matcher from the main problem for every statement.",
            "Check deny statements first: one match ends the evaluation.",
        ],
        "tests": [
            _ev([], [], "s3:GetObject", "Empty policy", "Nothing granted: ImplicitDeny."),
            _ev(["*"], [], "iam:PassRole", "Admin wildcard", "`*` allows every action."),
            _ev(["*"], ["*"], "s3:GetObject", "Deny everything", "A global deny overrides a global allow."),
            _ev(["s3:GetObject"], [], "s3:getobject", "Case-sensitive", "A different case is not a match."),
            _ev(["s3:Get*"], ["s3:GetObjectAcl"], "s3:GetObject", "Narrow deny misses", "The deny names a different action."),
            _ev(["s3:?etObject", "s3:Get*"], ["s3:Put*"], "s3:GetObject", "Several allows", "More than one allow matching changes nothing."),
            _ev(["iam:*"], ["iam:*Policy*"], "iam:AttachUserPolicy", "Star in the middle of a deny", "A deny with inner stars."),
            _ev(_BIG_ALLOW, _BIG_DENY, "s3:PutBucketPolicy", "Large input", "61 allow and 3 deny statements."),
        ],
        "solutions": [
            {"name": "Greedy matcher, deny first (Optimal)",
             "description": "Run the two-pointer matcher over the deny list and stop at the first hit, then over the allow list.",
             "time": "O(P · n·m) worst case", "space": "O(1)",
             "keyPoints": ["Explicit deny short-circuits", "any() stops at the first match", "O(1) extra space per match"],
             "code": _EVAL_FAST},
            {"name": "DP matcher over every statement", "slow": True,
             "description": "Evaluate every statement with a full DP table, collect the matches, then apply the precedence rules.",
             "time": "O(P · n·m)", "space": "O(n·m)",
             "keyPoints": ["Easy to prove correct", "Never short-circuits"],
             "code": _EVAL_SLOW},
        ],
        "starter": "def evaluate(allow: list[str], deny: list[str], action: str) -> str:\n    pass\n",
    },
    {
        "key": "codeowners-glob",
        "title": "Path glob with ** (CODEOWNERS)",
        "approach": "Token DP with a rolling row · O(n·m) · O(m)",
        "spec": {"kind": "fn", "fn": "glob_match", "params": ["pattern", "path"], "cmp": "exact"},
        "statement": (
            "Ownership and branch-protection rules match file paths with globs where `/` is special.\n"
            "\n"
            "### Input\n"
            "- `pattern`: the glob\n"
            "- `path`: the file path\n"
            "\n"
            "### Output\n"
            "- Whether `pattern` matches the whole `path`\n"
            "\n"
            "### Rules\n"
            "- `?` matches exactly one character other than `/`\n"
            "- `*` matches any run of characters (possibly empty) **not** containing `/`\n"
            "- `**` (two or more stars in a row) matches any run, including `/`\n"
            "- Every other character matches itself\n"
            "- Unlike IAM, a single `*` stops at a directory boundary"
        ),
        "examples": [
            {"args": {"pattern": "docs/*.md", "path": "docs/guide/setup.md"},
             "explanation": "A single `*` cannot cross the `/` between guide and setup.md.",
             "why": {"t": "Star stops at /", "d": "The key difference from IAM matching."}},
            {"args": {"pattern": "src/**/test_*.py", "path": "src/api/v2/test_auth.py"},
             "explanation": "`**` covers api/v2 and `*` covers auth.",
             "why": {"t": "Double star", "d": "`**` crosses directories."}},
        ],
        "constraints": ["0 ≤ pattern.length ≤ 200", "0 ≤ path.length ≤ 600"],
        "hints": [
            "Tokenize the pattern first: runs of two or more stars become one `**` token.",
            "dp[j] = the pattern tokens so far match the first j path characters. `*` extends from dp[j-1] only when path[j-1] is not `/`.",
            "Each token needs only the previous row, so keep one rolling row.",
        ],
        "tests": [
            _gl("", "", "Both empty", "An empty pattern matches only the empty path."),
            _gl("*", "", "Star matches nothing", "`*` can match an empty run."),
            _gl("*", "a/b", "Star vs slash", "`*` cannot cover a `/`."),
            _gl("**", "a/b/c", "Double star alone", "`**` matches any path."),
            _gl("a?c", "a/c", "Question mark vs slash", "`?` never matches `/`."),
            _gl("***/x", "p/q/x", "Triple star", "Three stars act as `**`."),
            _gl("src/**/*.go", "src/main.go", "Literal slashes still count", "The pattern has two literal `/`; src/main.go has one, so `**` cannot absorb the second."),
            _gl("*.tf", "modules/vpc/main.tf", "Root-only rule", "A top-level `*.tf` does not reach into subdirectories."),
            _gl("services/**/internal/*_test.go", _BIG_PATH, "Large input", "A 60-level deep path against a two-star rule."),
        ],
        "solutions": [
            {"name": "Token DP, rolling row (Optimal)",
             "description": "Collapse star runs into `*` or `**` tokens, then fill one DP row per token. `**` extends freely; `*` and `?` refuse `/`.",
             "time": "O(n·m)", "space": "O(m)",
             "keyPoints": ["Two kinds of star need a DP, not one saved pointer", "Tokenize star runs first", "One rolling row is enough"],
             "code": _GLOB_FAST},
            {"name": "Translate to a regular expression", "slow": True,
             "description": "Rewrite `**` as `.*`, `*` as `[^/]*` and `?` as `[^/]`, escape everything else and call re.fullmatch.",
             "time": "Exponential worst case (backtracking engine)", "space": "O(n)",
             "keyPoints": ["Short and readable", "A backtracking regex can blow up on many stars"],
             "code": _GLOB_SLOW},
        ],
        "starter": "def glob_match(pattern: str, path: str) -> bool:\n    pass\n",
    },
]
