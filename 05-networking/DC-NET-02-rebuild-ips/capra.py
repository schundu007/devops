"""Capra Playground export for DC-NET-02 (see tools/export_capra.py)."""

SPEC = {"kind": "fn", "fn": "restore_addresses", "params": ["digits"], "types": {}, "ret": "value", "cmp": "unordered"}


def c(digits, t, d):
    return {"args": {"digits": digits}, "why": {"t": t, "d": d}}


EXAMPLES = [
    {"args": {"digits": "19216811"}, "explanation": "Nine ways to place three dots give a valid address; any order is accepted.",
     "why": {"t": "Log forensics", "d": "The anchor case: a log field lost its dots."}},
    {"args": {"digits": "0000"}, "explanation": "Only 0.0.0.0: a part may be '0' but never '00'.",
     "why": {"t": "All zeros", "d": "The leading-zero rule leaves one answer."}},
    {"args": {"digits": "101023"}, "explanation": "Five candidates; '1.0.10.23' is valid but '1.01.0.23' is not.",
     "why": {"t": "Zero inside", "d": "Zeros in the middle force single-digit parts."}},
]

TESTS = [
    c("", "Empty", "No digits: no address."),
    c("123", "Too short", "Fewer than 4 digits can never make 4 parts."),
    c("1111", "Minimum length", "Exactly 4 digits: one address."),
    c("255255255255", "Maximum length", "12 digits: every part must be 3 digits."),
    c("2552552552551", "Too long", "13 digits cannot fit."),
    c("256256256256", "All parts too big", "Every 3-digit split is above 255."),
    c("010010", "Leading zeros", "Parts like '01' and '010' are rejected."),
    c("1921680114", "Private range", "A 10-digit 192.168.x.x value."),
    c("100200", "Trailing zeros", "Zeros force some splits and forbid others."),
    c("12a4", "Non-digit", "A letter in the field: no address."),
    c("1000000", "One then zeros", "No valid reading: every split leaves a part like '00' or '000'."),
    c("25525511135", "Classic", "Two valid readings."),
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Backtracking with pruning (Optimal)",
     "description": "Choose a 1-3 digit part, recurse on the rest, then undo the choice. Skip parts with a leading zero or a value above 255, and prune when the digits left cannot fill the parts left.",
     "time": "O(1)", "space": "O(1)",
     "keyPoints": ["At most 3^4 = 81 leaves", "Prune on remaining digits vs remaining parts", "'0' is a valid part, '01' is not"]},
    {"name": "Try every dot placement", "slow": True,
     "description": "Try all choices of three cut positions and keep the ones where every part is valid.",
     "time": "O(1) (at most C(11,3) = 165 placements)", "space": "O(1)",
     "keyPoints": ["Three nested loops over cut positions", "Simple to write; no pruning"],
     "code": '''def restore_addresses(digits: str) -> list[str]:
    def ok(p: str) -> bool:
        return 1 <= len(p) <= 3 and p.isascii() and p.isdigit() and (p == "0" or p[0] != "0") and int(p) <= 255

    out = []
    n = len(digits)
    for i in range(1, n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                parts = [digits[:i], digits[i:j], digits[j:k], digits[k:]]
                if all(ok(p) for p in parts):
                    out.append(".".join(parts))
    return out
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Every dot placement", "idea": "Three nested loops over the cut positions; validate the four parts.",
     "time": "O(1)", "space": "O(1)", "use": "Fixed 4 parts: simplest correct answer."},
    {"name": "Backtracking", "idea": "Choose a part, recurse, un-choose; prune impossible lengths early.",
     "time": "O(1)", "space": "O(1)", "use": "Generalises to any number of parts (e.g. IPv6 groups)."},
]
