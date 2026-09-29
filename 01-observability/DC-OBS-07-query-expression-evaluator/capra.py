"""Capra Playground export for DC-OBS-07 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "evaluate", "params": ["expr", "values"], "types": {}, "ret": "value", "cmp": "exact"}

V = {"errors": 42, "timeouts": 8, "retries": 11}

EXAMPLES = [
    {"args": {"expr": "(errors + timeouts) - retries", "values": V},
     "explanation": "(42 + 8) - 11 = 39.",
     "why": {"t": "Parentheses", "d": "Metric names inside parentheses."}},
    {"args": {"expr": "100 - (errors - timeouts + retries)", "values": V},
     "explanation": "The minus flips every term inside: 100 − 42 + 8 − 11 = 55.",
     "why": {"t": "Minus before parentheses", "d": "A leading minus negates the whole group."}},
    {"args": {"expr": "-(2 + 3)", "values": {}},
     "explanation": "A unary minus in front of a group.",
     "why": {"t": "Unary minus", "d": "An expression that starts with minus."}},
]


def _large():
    rng = random.Random(224)
    names = [f"m{i}" for i in range(20)]
    values = {n: rng.randint(0, 1000) for n in names}

    def expr(depth):
        parts = []
        for i in range(rng.randint(2, 4)):
            op = "" if i == 0 else rng.choice([" + ", " - "])
            if depth and rng.random() < 0.35:
                term = ("-" if i == 0 and rng.random() < 0.3 else "") + "(" + expr(depth - 1) + ")"  # unary minus only first
            else:
                term = rng.choice(names) if rng.random() < 0.6 else str(rng.randint(0, 99))
            parts.append(op + term)
        return "".join(parts)

    return {"expr": " + ".join(expr(4) for _ in range(40)), "values": values}


TESTS = [
    {"args": {"expr": "   ", "values": {}},
     "why": {"t": "Only spaces", "d": "An empty expression evaluates to 0."}},
    {"args": {"expr": "7", "values": {}},
     "why": {"t": "Single number", "d": "A lone integer."}},
    {"args": {"expr": "http_5xx_total", "values": {"http_5xx_total": 17}},
     "why": {"t": "Single metric", "d": "A lone name with underscores and digits."}},
    {"args": {"expr": "1-(2-(3-(4-5)))", "values": {}},
     "why": {"t": "Deep nesting, no spaces", "d": "Signs alternate through four levels: 1-2+3-4+5 = 3."}},
    {"args": {"expr": "((((errors))))", "values": V},
     "why": {"t": "Redundant parentheses", "d": "Parentheses around a single operand change nothing."}},
    {"args": {"expr": "1000 - 999", "values": {}},
     "why": {"t": "Multi-digit", "d": "Numbers with several digits are read whole."}},
    {"args": {"expr": "(requests - (errors_5xx + errors_4xx)) - (canary_errors - canary_retries)",
              "values": {"requests": 12000, "errors_5xx": 140, "errors_4xx": 310, "canary_errors": 45, "canary_retries": 30}},
     "why": {"t": "Dashboard query", "d": "Good requests minus the net canary errors."}},
    {"args": _large(),
     "why": {"t": "Large input", "d": "A long random expression with nested groups."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "One pass with a stack (Optimal)",
     "description": "Keep a running result and the sign of the next operand. On '(' push (result, sign) and start fresh; on ')' pop and combine: outer + outer_sign * inner.",
     "time": "O(n)", "space": "O(d) for nesting depth d",
     "keyPoints": ["Only + and -, so a running total and a sign are enough", "The stack saves the outer total and the sign in front of each group", "Metric names are looked up in values"]},
    {"name": "Innermost group first", "slow": True,
     "description": "Repeatedly find an innermost ( ... ), evaluate that flat expression, and splice its value back into the text.",
     "time": "O(n²)", "space": "O(n)",
     "keyPoints": ["Simple string rewriting", "Rescans the text once per group"],
     "code": '''from __future__ import annotations
import re


def _flat(expr: str, values: dict[str, int]) -> int:
    """Evaluate an expression with no parentheses. Signs multiply, so 1--5 is 6."""
    total, sign = 0, 1
    for tok in re.findall(r"\\d+|[A-Za-z_][A-Za-z0-9_]*|[+-]", expr):
        if tok == "-":
            sign = -sign
        elif tok != "+":
            total += sign * (int(tok) if tok.isdigit() else values[tok])
            sign = 1
    return total


def evaluate(expr: str, values: dict[str, int]) -> int:
    expr = expr.replace(" ", "")
    while "(" in expr:
        m = re.search(r"\\(([^()]*)\\)", expr)   # an innermost group
        expr = expr[:m.start()] + str(_flat(m.group(1), values)) + expr[m.end():]
    return _flat(expr, values)
'''},
]

VARIANT_TITLE = "Metric math with parentheses"
VARIANT_APPROACH = "One pass with a stack · O(n) · O(d)"


def _big_rule():
    rng = random.Random(1106)
    names = [f"a{i}" for i in range(15)]
    alerts = {n: rng.random() < 0.5 for n in names}

    def rule(depth):
        if depth == 0 or rng.random() < 0.25:
            return rng.choice(names)
        op = rng.choice("&|!")
        if op == "!":
            return "!(" + rule(depth - 1) + ")"
        return op + "(" + ",".join(rule(depth - 1) for _ in range(rng.randint(2, 4))) + ")"

    return {"rule": "|(" + ",".join(rule(5) for _ in range(12)) + ")", "alerts": alerts}


def _big_spec():
    rng = random.Random(726)
    names = ["web", "api", "envoy", "log-agent", "redis", "worker", "cron", "db"]

    def group(depth):
        items = []
        for _ in range(rng.randint(1, 4)):
            if depth and rng.random() < 0.4:
                items.append("(" + group(depth - 1) + ")" + str(rng.randint(1, 5)))
            else:
                k = rng.randint(1, 4)
                items.append(rng.choice(names) + (str(k) if k > 1 else ""))
        return " ".join(items)

    return {"spec": " ".join(group(4) for _ in range(25))}


VARIANTS = [
    {
        "key": "alert-rule",
        "title": "Composite alert rule",
        "approach": "Stack of operators and operands · O(n) · O(n)",
        "spec": {"kind": "fn", "fn": "eval_rule", "params": ["rule", "alerts"], "ret": "value", "cmp": "exact"},
        "statement": """A composite alert fires from other alerts. Its rule is written in prefix form.

### Input
- `rule`: the composite rule, built from:
  - an alert name matching `[a-z_][a-z0-9_]*`, true if `alerts[name]` is firing
  - `!(x)`: not x
  - `&(x,y,...)`: every argument is true
  - `|(x,y,...)`: at least one argument is true
- `alerts`: whether each alert is firing

### Output
- Whether the composite alert fires

### Rules
- There are no spaces""",
        "examples": [
            {"args": {"rule": "&(cpu_high,|(disk_full,!(maintenance)))", "alerts": {"cpu_high": True, "disk_full": False, "maintenance": False}},
             "explanation": "Not in maintenance, so the | is true, and CPU is high: the rule fires.",
             "why": {"t": "Nested operators", "d": "All three operators in one rule."}},
            {"args": {"rule": "!(|(a,b,c))", "alerts": {"a": False, "b": False, "c": True}},
             "explanation": "c fires, so the | is true and its negation is false.",
             "why": {"t": "Negated group", "d": "! around a whole group."}},
        ],
        "constraints": ["1 ≤ rule.length ≤ 2 · 10^4", "The rule is always valid", "Every name in the rule is a key of alerts"],
        "hints": [
            "Push each operator and each '(' as you meet them; push each name's value.",
            "On ')', pop values back to the '(' and apply the operator just below it.",
            "Commas only separate arguments; skip them.",
        ],
        "tests": [
            {"args": {"rule": "up", "alerts": {"up": True}}, "why": {"t": "Single name", "d": "No operators at all."}},
            {"args": {"rule": "!(up)", "alerts": {"up": True}}, "why": {"t": "Single negation", "d": "The smallest group."}},
            {"args": {"rule": "&(a)", "alerts": {"a": False}}, "why": {"t": "One argument", "d": "& and | with a single argument return it."}},
            {"args": {"rule": "|(a,a,a)", "alerts": {"a": False}}, "why": {"t": "Duplicates", "d": "The same name repeated."}},
            {"args": {"rule": "!(!(!(!(x))))", "alerts": {"x": True}}, "why": {"t": "Deep nesting", "d": "Four negations cancel out."}},
            {"args": {"rule": "&(|(p99_slow,err_rate),!(deploying),|(region_eu,region_us))",
                      "alerts": {"p99_slow": False, "err_rate": True, "deploying": False, "region_eu": False, "region_us": True}},
             "why": {"t": "Page rule", "d": "Page when latency or errors are bad, outside a deploy, in a paged region."}},
            {"args": _big_rule(), "why": {"t": "Large input", "d": "Twelve random rules, five levels deep, joined by |."}},
        ],
        "solutions": [
            {"name": "Stack of operators and operands (Optimal)",
             "description": "Scan once. Push operators, '(' markers and alert values. On ')', pop values to the marker, pop the operator under it, and push the result.",
             "time": "O(n)", "space": "O(n)",
             "keyPoints": ["The operator sits just below its '('", "Names are read whole", "Each token is pushed and popped once"],
             "code": '''def eval_rule(rule, alerts):
    stack = []
    i, n = 0, len(rule)
    while i < n:
        ch = rule[i]
        if ch in "&|!(":
            stack.append(ch)
        elif ch == ")":
            vals = []
            while stack[-1] != "(":
                vals.append(stack.pop())
            stack.pop()
            op = stack.pop()
            if op == "!":
                stack.append(not vals[0])
            elif op == "&":
                stack.append(all(vals))
            else:
                stack.append(any(vals))
        elif ch != ",":
            j = i
            while j < n and (rule[j].isalnum() or rule[j] == "_"):
                j += 1
            stack.append(bool(alerts[rule[i:j]]))
            i = j
            continue
        i += 1
    return stack[0]
'''},
            {"name": "Innermost group first", "slow": True,
             "description": "Replace every name by T or F, then repeatedly find an innermost op(...) group, evaluate it and splice the letter back in.",
             "time": "O(n²)", "space": "O(n)",
             "keyPoints": ["Plain string rewriting", "Rescans the rule once per group"],
             "code": '''import re


def eval_rule(rule, alerts):
    rule = re.sub(r"[a-z_][a-z0-9_]*", lambda m: "T" if alerts[m.group(0)] else "F", rule)
    pat = re.compile(r"([!&|])\\(([TF,]*)\\)")
    while len(rule) > 1:
        m = pat.search(rule)
        args = m.group(2).split(",")
        op = m.group(1)
        if op == "!":
            val = args[0] == "F"
        elif op == "&":
            val = all(a == "T" for a in args)
        else:
            val = any(a == "T" for a in args)
        rule = rule[:m.start()] + ("T" if val else "F") + rule[m.end():]
    return rule == "T"
'''},
        ],
        "starter": '''def eval_rule(rule: str, alerts: dict[str, bool]) -> bool:
    pass
''',
    },
    {
        "key": "replica-count",
        "title": "Count containers in a nested replica spec",
        "approach": "Stack of counters · O(n · d) · O(n)",
        "spec": {"kind": "fn", "fn": "count_containers", "params": ["spec"], "ret": "value", "cmp": "exact"},
        "statement": """A compact deploy spec lists containers and repeated groups. For capacity planning, count how many of each container it will start.

### Input
- `spec`: items separated by spaces, each a container or a group

### Output
- `[name, count]` pairs sorted by name

### Rules
- A container is a name matching `[a-z][a-z-]*`, optionally followed by a count: `api3` is three `api` containers
- A group is `( ... )`, optionally followed by a count that multiplies everything inside
- A missing count means `1`""",
        "examples": [
            {"args": {"spec": "(web2 (envoy log-agent))3 db"},
             "explanation": "The outer group has web ×2, envoy and log-agent; ×3 gives web 6, envoy 3, log-agent 3. db appears once.",
             "why": {"t": "Nested groups", "d": "A multiplier outside a group reaches every level inside."}},
            {"args": {"spec": "redis redis2 (redis)2"},
             "explanation": "1 + 2 + 2 = 5 redis containers.",
             "why": {"t": "Same name, three ways", "d": "Counts for one name add up across items."}},
        ],
        "constraints": ["1 ≤ spec.length ≤ 10^4", "Counts are 1 to 1000", "The spec is always valid and names at least one container"],
        "hints": [
            "Keep a stack of dicts. '(' pushes a new empty dict.",
            "On ')', read the count after it, multiply the popped dict and add it into the dict below.",
            "Read a name, then any digits right after it, as one item.",
        ],
        "tests": [
            {"args": {"spec": "api"}, "why": {"t": "Single container", "d": "No count means 1."}},
            {"args": {"spec": "api1000"}, "why": {"t": "Largest count", "d": "A multi-digit count."}},
            {"args": {"spec": "((((cron))))"}, "why": {"t": "Redundant groups", "d": "Groups with no count multiply by 1."}},
            {"args": {"spec": "((a2)3)4"}, "why": {"t": "Stacked multipliers", "d": "2 × 3 × 4 = 24."}},
            {"args": {"spec": "b a c a"}, "why": {"t": "Output order", "d": "Sorted by name, duplicates merged."}},
            {"args": {"spec": "(api2 (envoy otel-collector))4 (worker5 redis)2 postgres"},
             "why": {"t": "Service stack", "d": "Sidecars inside each API pod, a worker pool, one database."}},
            {"args": _big_spec(), "why": {"t": "Large input", "d": "Twenty-five random groups nested up to four levels."}},
        ],
        "solutions": [
            {"name": "Stack of counters (Optimal)",
             "description": "Scan once. A name adds its count to the top dict. '(' pushes a new dict; ')' pops it, multiplies by the count that follows, and merges it into the dict below.",
             "time": "O(n · d)", "space": "O(n)",
             "keyPoints": ["One tally per open group", "Read the count right after ')'", "Sort only at the end"],
             "code": '''def count_containers(spec):
    stack = [{}]
    i, n = 0, len(spec)

    def read_count(j):
        k = j
        while k < n and spec[k].isdigit():
            k += 1
        return (int(spec[j:k]) if k > j else 1), k

    while i < n:
        ch = spec[i]
        if ch == "(":
            stack.append({})
            i += 1
        elif ch == ")":
            inner = stack.pop()
            mult, i = read_count(i + 1)
            top = stack[-1]
            for name, c in inner.items():
                top[name] = top.get(name, 0) + c * mult
        elif ch.isalpha():
            j = i
            while j < n and (spec[j].isalpha() or spec[j] == "-"):
                j += 1
            name = spec[i:j]
            c, i = read_count(j)
            stack[-1][name] = stack[-1].get(name, 0) + c
        else:
            i += 1
    return [[name, stack[0][name]] for name in sorted(stack[0])]
'''},
            {"name": "Expand innermost groups", "slow": True,
             "description": "Repeatedly find an innermost group with its count, multiply the counts inside, and splice the flat items back into the text.",
             "time": "O(n²)", "space": "O(n)",
             "keyPoints": ["Rewrites the text until no groups remain", "Each pass rescans the whole spec"],
             "code": '''import re

ITEM = re.compile(r"([a-z][a-z-]*)(\\d*)")


def _flat(text):
    counts = {}
    for name, num in ITEM.findall(text):
        counts[name] = counts.get(name, 0) + (int(num) if num else 1)
    return counts


def count_containers(spec):
    pat = re.compile(r"\\(([^()]*)\\)(\\d*)")
    while "(" in spec:
        m = pat.search(spec)
        mult = int(m.group(2)) if m.group(2) else 1
        flat = " ".join(f"{k}{v * mult}" for k, v in _flat(m.group(1)).items())
        spec = spec[:m.start()] + " " + flat + " " + spec[m.end():]
    counts = _flat(spec)
    return [[k, counts[k]] for k in sorted(counts)]
'''},
        ],
        "starter": '''def count_containers(spec: str) -> list[list]:
    pass
''',
    },
]
