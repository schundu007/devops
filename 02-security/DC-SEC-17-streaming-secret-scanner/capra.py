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
