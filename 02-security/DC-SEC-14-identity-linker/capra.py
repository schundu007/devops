"""Capra Playground export for DC-SEC-14 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "link_identities", "params": ["accounts"], "types": {}, "ret": "value", "cmp": "exact"}


def case(accounts):
    return {"accounts": accounts}


EXAMPLES = [
    {"args": case([["dana", "dana@corp.example", "dana.k@okta.example"],
                   ["dana", "dana.k@okta.example", "dk@github.example"],
                   ["lee", "lee@corp.example"]]),
     "explanation": "Dana's Okta email appears in two accounts, so they merge into one person with three emails.",
     "why": {"t": "Shared email", "d": "Two accounts linked by one email."}},
    {"args": case([["alex", "alex@a.example"], ["alex", "alex@b.example"]]),
     "explanation": "Same name, no shared email: two different people.",
     "why": {"t": "Same name, different people", "d": "Names never link accounts; only emails do."}},
]


def _large():
    rng = random.Random(14)
    accounts = []
    for i in range(400):
        name = f"user{rng.randint(0, 60)}"
        emails = [f"{name}.{rng.randint(0, 300)}@corp.example" for _ in range(rng.randint(1, 3))]
        accounts.append([name, *emails])
    return case(accounts)


TESTS = [
    {"args": case([["sam", "sam@corp.example"]]), "why": {"t": "Single account", "d": "One account, one email."}},
    {"args": case([["sam", "sam@corp.example", "sam@corp.example"]]), "why": {"t": "Duplicate email", "d": "An email listed twice appears once."}},
    {"args": case([["a", "1@x"], ["a", "2@x"], ["a", "1@x", "3@x"], ["a", "2@x", "3@x"]]),
     "why": {"t": "Chain of links", "d": "Accounts linked only through a chain of other accounts."}},
    {"args": case([["zoe", "z@x"], ["amy", "a@x"], ["amy", "b@x"]]), "why": {"t": "Row order", "d": "Rows sort by name, then first email."}},
    {"args": case([["ops", "ops@okta.example", "ops@aws.example", "ops@github.example"],
                   ["ops", "ops@aws.example"], ["ops", "oncall@corp.example"]]),
     "why": {"t": "Offboarding", "d": "Okta, AWS and GitHub accounts of one person, plus a separate shared mailbox."}},
    {"args": case([["b", "b@x", "a@x"], ["b", "c@x", "b@x"]]), "why": {"t": "Email sort", "d": "Emails inside a row are sorted."}},
    {"args": _large(), "why": {"t": "Large input", "d": "400 accounts with random overlapping emails."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Union-find by email (Optimal)",
     "description": "Union-find keyed by email. For each account, link all its emails to the first one and record each email's name. Group emails by root; each group becomes [name, *sorted emails], and rows are sorted by (name, first email).",
     "time": "O(E · α(E) + E log E)", "space": "O(E)",
     "keyPoints": ["Link emails, not names", "Every email in one account belongs to the same person", "Sort emails, then rows"]},
    {"name": "Merge overlapping sets", "slow": True,
     "description": "Keep a list of (name, email set). For each account, merge every existing set that shares an email with it into one.",
     "time": "O(A² · E)", "space": "O(E)",
     "keyPoints": ["Straightforward", "Quadratic in the number of accounts"],
     "code": '''from __future__ import annotations


def link_identities(accounts: list[list[str]]) -> list[list[str]]:
    people: list[tuple[str, set[str]]] = []
    for name, *emails in accounts:
        merged = set(emails)
        keep = []
        for other_name, other in people:
            if other & merged:
                merged |= other
            else:
                keep.append((other_name, other))
        people = keep + [(name, merged)]
    rows = [[name, *sorted(emails)] for name, emails in people]
    return sorted(rows, key=lambda r: (r[0], r[1]))
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Merge overlapping sets", "idea": "Fold each account into every existing set it overlaps.",
     "time": "O(A² · E)", "space": "O(E)", "use": "A few hundred accounts."},
    {"name": "Union-find", "idea": "Union emails within an account, then group by root.",
     "time": "O(E log E)", "space": "O(E)", "use": "Company-wide identity graphs."},
    {"name": "Graph DFS", "idea": "Emails are nodes; accounts add edges; each component is a person.",
     "time": "O(E log E)", "space": "O(E)", "use": "Same scale; explicit graph."},
]
