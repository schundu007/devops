"""Capra Playground export for DC-SEC-17 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "design", "fn": "SecretScanner", "params": [], "types": {}, "ret": "value", "cmp": "exact"}


def stream(patterns, text):
    return {"ops": ["SecretScanner"] + ["feed"] * len(text), "vals": [[patterns]] + [[c] for c in text]}


EXAMPLES = [
    {"args": stream(["cd", "f", "kl"], "abcdefghijkl"),
     "explanation": "True right after 'd' (cd ends), after 'f', and after 'l' (kl ends).",
     "why": {"t": "Several patterns", "d": "Matches are flagged the moment each pattern ends."}},
    {"args": stream(["AKIA", "KIA"], "xAKIAy"),
     "explanation": "After the final 'A' both AKIA and KIA end there; one True is enough.",
     "why": {"t": "Overlapping patterns", "d": "One pattern is a suffix of another."}},
]


def _large():
    rng = random.Random(1032)
    alphabet = "abc"
    patterns = sorted({"".join(rng.choice(alphabet) for _ in range(rng.randint(3, 8))) for _ in range(40)})
    text = "".join(rng.choice(alphabet) for _ in range(2500))
    return stream(patterns, text)


TESTS = [
    {"args": stream(["x"], "x"), "why": {"t": "Single character", "d": "A one-character pattern on a one-character stream."}},
    {"args": stream(["token"], "tok"), "why": {"t": "Stream too short", "d": "The stream ends before the pattern can finish."}},
    {"args": stream(["aa"], "aaaa"), "why": {"t": "Repeated characters", "d": "Every character after the first ends a match."}},
    {"args": stream(["ghp_", "secret"], "my_secret_ghp_x"), "why": {"t": "Two hits", "d": "Two different patterns in one line of log."}},
    {"args": stream(["abc"], "ababcabc"), "why": {"t": "False start", "d": "A partial match restarts correctly."}},
    {"args": stream(["=", "key="], "api_key=1"), "why": {"t": "Nested suffix", "d": "A short pattern and a longer one end at the same character."}},
    {"args": _large(), "why": {"t": "Large input", "d": "40 patterns over a 2,500-character stream."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Reverse trie (Optimal)",
     "description": "Insert every pattern reversed into a trie. Keep the last L characters (L = longest pattern) and, on each feed, walk the trie from the newest character toward older ones.",
     "time": "O(L) per feed", "space": "O(total pattern length + L)",
     "keyPoints": ["Reversed patterns let the walk start at the newest character", "Only the last L characters can complete a match", "The walk usually stops after a few steps"]},
    {"name": "endswith for every pattern", "slow": True,
     "description": "Keep the recent text and check endswith(p) for every pattern after each character.",
     "time": "O(P · L) per feed", "space": "O(L)",
     "keyPoints": ["Simple and correct", "Cost grows with the number of patterns"],
     "code": '''from __future__ import annotations


class SecretScanner:
    def __init__(self, patterns: list[str]) -> None:
        self.patterns = patterns
        self.keep = max(map(len, patterns))
        self.text = ""

    def feed(self, ch: str) -> bool:
        self.text = (self.text + ch)[-self.keep:]
        return any(self.text.endswith(p) for p in self.patterns)
'''},
]

WAYS_TO_SOLVE = [
    {"name": "endswith per pattern", "idea": "Check every pattern against the tail after each character.",
     "time": "O(P · L) per char", "space": "O(L)", "use": "A few patterns."},
    {"name": "Reverse trie", "idea": "Walk a trie of reversed patterns from the newest character.",
     "time": "O(L) per char", "space": "O(total pattern length)", "use": "Thousands of patterns on a live stream."},
]

VARIANT_TITLE = "Any pattern ends here"
VARIANT_APPROACH = "Reverse trie over the last L characters · O(L) per feed · O(total pattern length + L)"


def _which(patterns, text):
    return {"ops": ["PatternScanner"] + ["feed"] * len(text), "vals": [[patterns]] + [[c] for c in text]}


def _which_large():
    rng = random.Random(1233)
    patterns = ["".join(rng.choice("xyz") for _ in range(rng.randint(2, 6))) for _ in range(30)]
    text = "".join(rng.choice("xyz") for _ in range(1500))
    return _which(patterns, text)


def _redact_large():
    rng = random.Random(722)
    patterns = ["AKIA", "ghp_", "xoxb-", "secret", "=="]
    words = ["user=", "AKIA", "ok", "ghp_", "token", "xoxb-", "secret", "==", "log", " "]
    line = "".join(rng.choice(words) for _ in range(600))
    return {"patterns": patterns, "line": line}


VARIANTS = [
    {
        "key": "which-patterns",
        "title": "Report which rules matched",
        "approach": "Reverse trie collecting every end marker · O(L) per feed · O(total pattern length + L)",
        "spec": {"kind": "design", "fn": "PatternScanner", "params": [], "cmp": "exact"},
        "statement": (
            "A True/False flag is not enough for the incident ticket: the scanner must say **which** detection "
            "rules fired. Build `PatternScanner(patterns)` with `feed(ch)` as before, but return the **indices** "
            "of all patterns that end exactly at this character, sorted ascending (`[]` when none).\n\n"
            "- Several patterns can end at the same character when one is a suffix of another.\n"
            "- The same string can appear twice in `patterns`; report both indices."
        ),
        "examples": [
            {"args": _which(["AKIA", "KIA", "IA"], "xAKIA"),
             "explanation": "After the final A, all three rules end there: [0, 1, 2].",
             "why": {"t": "Nested suffixes", "d": "Every rule ending at the character is reported, not just the first."}},
            {"args": _which(["ab", "b", "ab"], "abb"),
             "explanation": "After the first b: rules 0, 1 and 2 (the duplicate). After the second b: only rule 1.",
             "why": {"t": "Duplicate rules", "d": "Two rules with the same text both fire."}},
        ],
        "constraints": ["1 ≤ len(patterns) ≤ 2000, each of length 1 to 200", "Up to 4 · 10^4 calls to feed"],
        "hints": [
            "Keep the reverse trie, but store a list of pattern indices at each node where a pattern ends.",
            "Do not stop at the first end marker; keep walking toward older characters to find longer patterns.",
            "Indices are collected shortest pattern first, so sort before returning.",
        ],
        "tests": [
            {"args": _which(["x"], "x"), "why": {"t": "Minimal", "d": "One rule, one character."}},
            {"args": _which(["token"], "tok"), "why": {"t": "No match", "d": "Every feed returns []."}},
            {"args": _which(["aa", "a"], "aaa"), "why": {"t": "Overlapping repeats", "d": "From the second character on, both rules fire."}},
            {"args": _which(["b", "cab", "ab"], "cab"), "why": {"t": "Sorted indices", "d": "Found as 0, 2, 1 while walking; returned as [0, 1, 2]."}},
            {"args": _which(["key=", "="], "api_key=x="), "why": {"t": "Two hits in a line", "d": "The first = fires two rules, the second = fires one."}},
            {"args": _which_large(), "why": {"t": "Large input", "d": "30 rules over a 1,500-character stream on three letters."}},
        ],
        "solutions": [
            {"name": "Reverse trie with index lists (Optimal)",
             "description": "Insert every pattern reversed; at its last node append its index. On each feed, walk from the newest character back, gathering every index list met, until the trie runs out.",
             "time": "O(L + h log h) per feed, h = matches", "space": "O(total pattern length + L)",
             "keyPoints": ["End nodes keep lists, so duplicates are natural", "The walk continues past the first match", "Sort the gathered indices"],
             "code": '''from collections import deque


class PatternScanner:
    def __init__(self, patterns):
        self.root = {}
        for i, p in enumerate(patterns):
            node = self.root
            for ch in reversed(p):
                node = node.setdefault(ch, {})
            node.setdefault(None, []).append(i)
        self.recent = deque(maxlen=max(map(len, patterns)))

    def feed(self, ch):
        self.recent.append(ch)
        node, hits = self.root, []
        for c in reversed(self.recent):
            node = node.get(c)
            if node is None:
                break
            hits.extend(node.get(None, ()))
        return sorted(hits)
'''},
            {"name": "endswith for every rule", "slow": True,
             "description": "Keep the recent text and test every rule with endswith after each character.",
             "time": "O(P · L) per feed", "space": "O(L)",
             "keyPoints": ["Indices come out sorted for free", "Cost grows with the number of rules"],
             "code": '''class PatternScanner:
    def __init__(self, patterns):
        self.patterns = patterns
        self.keep = max(map(len, patterns))
        self.text = ""

    def feed(self, ch):
        self.text = (self.text + ch)[-self.keep:]
        return [i for i, p in enumerate(self.patterns) if self.text.endswith(p)]
'''},
        ],
        "starter": '''class PatternScanner:
    def __init__(self, patterns: list[str]) -> None:
        pass

    def feed(self, ch: str) -> list[int]:
        pass
''',
    },
    {
        "key": "redact-line",
        "title": "Redact secrets in a log line",
        "approach": "Reverse trie per end position + difference array · O(n · L) · O(total pattern length + n)",
        "spec": {"kind": "fn", "fn": "redact", "params": ["patterns", "line"], "cmp": "exact"},
        "statement": (
            "Before log lines leave the host, a sidecar masks secrets. Given the `patterns` and one `line`, "
            "replace **every character covered by any occurrence** of any pattern with `*`, and return the result.\n\n"
            "- Occurrences may overlap or touch; the union of all of them is masked.\n"
            "- Characters not inside any occurrence are left as they are.\n\n"
            "Scanning the line left to right is the streaming scanner in disguise: at each position, which patterns end here?"
        ),
        "examples": [
            {"args": {"patterns": ["AKIA", "pass"], "line": "key=AKIA12 pass=ok"},
             "explanation": "AKIA (positions 4-7) and pass (11-14) are masked; everything else stays.",
             "why": {"t": "Two secrets", "d": "Each occurrence is replaced character for character."}},
            {"args": {"patterns": ["aba"], "line": "xababay"},
             "explanation": "aba occurs at 1 and 3; together they cover positions 1 to 5.",
             "why": {"t": "Overlapping occurrences", "d": "Overlaps are merged, not masked twice or skipped."}},
        ],
        "constraints": ["1 ≤ len(patterns) ≤ 200, each of length 1 to 50", "0 ≤ len(line) ≤ 10^4", "Printable ASCII"],
        "hints": [
            "At each end position, only the **longest** pattern ending there matters: shorter ones lie inside it.",
            "Walk a reverse trie from position j toward the start to find that longest match.",
            "Mark covered ranges with a difference array, then sweep once to build the output.",
        ],
        "tests": [
            {"args": {"patterns": ["x"], "line": ""}, "why": {"t": "Empty line", "d": "Nothing to mask."}},
            {"args": {"patterns": ["secret"], "line": "all clear"}, "why": {"t": "No match", "d": "The line is returned unchanged."}},
            {"args": {"patterns": ["a"], "line": "aaa"}, "why": {"t": "Everything masked", "d": "Every character is its own occurrence."}},
            {"args": {"patterns": ["ab", "bc"], "line": "abc"}, "why": {"t": "Touching patterns", "d": "Two different patterns share b."}},
            {"args": {"patterns": ["tok", "token", "en"], "line": "a token b"}, "why": {"t": "Nested patterns", "d": "Shorter matches inside a longer one change nothing."}},
            {"args": {"patterns": ["ghp_", "ghp_"], "line": "ghp_ghp_x"}, "why": {"t": "Duplicate patterns", "d": "A repeated pattern masks the same characters."}},
            {"args": _redact_large(), "why": {"t": "Large input", "d": "About 2,200 characters with five secret prefixes."}},
        ],
        "solutions": [
            {"name": "Reverse trie + difference array (Optimal)",
             "description": "For each end position, walk the reverse trie backwards to find the longest pattern ending there and mark its range in a difference array. A final sweep masks every position with positive coverage.",
             "time": "O(n · L)", "space": "O(total pattern length + n)",
             "keyPoints": ["Longest match per end position is enough", "Difference array merges overlaps in O(n)", "Same reverse trie as the scanner"],
             "code": '''def redact(patterns, line):
    root = {}
    for p in patterns:
        node = root
        for ch in reversed(p):
            node = node.setdefault(ch, {})
        node[None] = True
    n = len(line)
    diff = [0] * (n + 1)
    for j in range(n):
        node, best, i = root, 0, j
        while i >= 0:
            node = node.get(line[i])
            if node is None:
                break
            if None in node:
                best = j - i + 1
            i -= 1
        if best:
            diff[j - best + 1] += 1
            diff[j + 1] -= 1
    out, cover = [], 0
    for k, ch in enumerate(line):
        cover += diff[k]
        out.append("*" if cover > 0 else ch)
    return "".join(out)
'''},
            {"name": "find every occurrence of every pattern", "slow": True,
             "description": "For each pattern, call str.find repeatedly (advancing by one) to list every occurrence, and mark each covered character.",
             "time": "O(P · n · m)", "space": "O(n)",
             "keyPoints": ["Uses only built-in string search", "Scans the line once per pattern"],
             "code": '''def redact(patterns, line):
    masked = [False] * len(line)
    for p in patterns:
        i = line.find(p)
        while i != -1:
            for k in range(i, i + len(p)):
                masked[k] = True
            i = line.find(p, i + 1)
    return "".join("*" if m else ch for ch, m in zip(line, masked))
'''},
        ],
        "starter": '''def redact(patterns: list[str], line: str) -> str:
    pass
''',
    },
]
