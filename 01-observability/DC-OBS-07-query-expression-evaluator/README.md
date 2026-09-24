Source: New

# DC-OBS-07 · Query Expression Evaluator

## 1. Header
| | |
|---|---|
| Chip ID | DC-OBS-07 |
| Difficulty | Hard |
| Pattern | Stack |
| Track | Observability & SRE (OBS) |
| Classic pattern | LeetCode 224 |
| Premium | No |
| Time box | 40 min |
| Source | New |

## 2. The Scenario
Your team runs a small internal "SLO calculator" service. Engineers write formulas over
already-aggregated numbers, such as `(errors + timeouts) - retries`, or
`cpu_limit - (team_a + team_b) - reserved` for capacity headroom. The service fetches each
named value, then evaluates the formula. Last week someone wrote `100 - (errors - timeouts)`,
the old evaluator flipped only the first term inside the parentheses, and a dashboard showed
healthy headroom during a capacity crunch.

## 3. Why This Is DevOps
**Production reality:** Monitoring queries mix names, numbers and parentheses: error ratios,
headroom, and "good minus bad" counts. Every query engine has to turn that text into a number
without running arbitrary code. The core of that is a stack: when you open a parenthesis, save
where you were; when you close it, fold the inner result back in with the sign in front of it.

**Where you see it:** PromQL binary operators, Grafana server-side "Math" expressions
(`$A + $B`), Datadog metric arithmetic, and alert rule expressions in general.

**Reality check:** PromQL has a full parser (generated from a grammar with goyacc), operator
precedence, vector matching and more operators. This chip handles only `+`, `-`,
parentheses and names, which teaches the stack idea. DC-OBS-17 adds `*` and `/` with precedence.

**What breaks if you get it wrong:** A sign bug inside parentheses makes a headroom or error-rate
number wrong, but plausible. Nobody notices until the capacity planning or the alert decision
based on it fails.

## 4. Problem Statement
Write `evaluate(expr, values)` that returns the integer value of an expression built from:

- non-negative integers, such as `100`
- metric names matching `[A-Za-z_][A-Za-z0-9_]*`, each replaced by `values[name]`
- the binary operators `+` and `-`
- parentheses, and any number of spaces
- a unary minus, allowed only at the very start of the expression or right after `(`

Do not use `eval` or any other built-in expression evaluator. If a name is missing from
`values`, raise `KeyError`. A blank expression evaluates to `0`.

## 5. Input / Output format and Constraints
- `expr: str`, `0 <= len(expr) <= 3 * 10^5`. It is always a valid expression under the rules above.
- `values: dict[str, int]`, with each value in `[-10^9, 10^9]`.
- Parentheses can nest up to `10^5` levels deep.
- Returns `int`. Python ints do not overflow, but every intermediate result fits in 64 bits.

## 6. Examples
**Example 1**
```
evaluate("(errors + timeouts) - retries", {"errors": 42, "timeouts": 8, "retries": 11}) -> 39
```

**Example 2: minus before parentheses**
```
evaluate("100 - (errors - timeouts + retries)", {"errors": 42, "timeouts": 8, "retries": 11}) -> 55
```
The minus flips *every* term inside: 100 − 42 + 8 − 11.

**Example 3: unary minus and edge cases**
```
evaluate("-(2 + 3)", {})       -> -5
evaluate("   ", {})            -> 0
evaluate("errors + dropped", {"errors": 1})  -> raises KeyError
```

## 7. Starter Code
See [`starter.py`](starter.py): `evaluate(expr, values)` with a docstring that lists the
grammar, type hints and a TODO body.

```bash
make try CHIP=01-observability/DC-OBS-07-query-expression-evaluator
```

## 8. Hints
1. **Nudge:** Without parentheses this is easy: keep a running total and the sign of the next
   number. What do parentheses change?
2. **Pattern:** A stack. At `(`, save the running total and the sign in front of the
   parenthesis, then start fresh. At `)`, combine the inner total with what you saved.
3. **Near-solution:** Keep `result` and `sign`. An operand does `result += sign * value`. `+` and
   `-` set `sign`. `(` pushes `(result, sign)` and resets both. `)` pops `(outer, s)` and sets
   `result = outer + s * result`. Unary minus then needs no special case.

## 9. Solution
**Approach**
1. Scan left to right with `result = 0` and `sign = 1`.
2. On a number or a name, read the whole token, look names up, and add `sign * value` to `result`.
3. On `+` or `-`, set `sign` to `+1` or `-1`.
4. On `(`, push `(result, sign)` and reset `result = 0`, `sign = 1`.
5. On `)`, pop `(outer, s)` and set `result = outer + s * result`.
6. Skip spaces. At the end, `result` is the answer.

A unary minus works without special handling: at the start, or right after `(`, the running
total is `0`, so `-x` is just `0 - x`.

**Brute force:** Repeatedly find an innermost `( … )`, evaluate it, and replace it with its value
in the string. Each replacement copies the string, so deep nesting costs O(n²).

**Optimal code:** [`solution.py`](solution.py)

```python
def evaluate(expr: str, values: dict[str, int]) -> int:
    result, sign = 0, 1
    stack: list[tuple[int, int]] = []          # (total before '(', sign before '(')
    i, n = 0, len(expr)
    while i < n:
        ch = expr[i]
        if ch.isdigit() or ch.isalpha() or ch == "_":
            j = i
            if ch.isdigit():
                while j < n and expr[j].isdigit():
                    j += 1
                operand = int(expr[i:j])
            else:
                while j < n and (expr[j].isalnum() or expr[j] == "_"):
                    j += 1
                operand = values[expr[i:j]]    # unknown metric -> KeyError
            result += sign * operand
            i = j
            continue
        if ch == "+":
            sign = 1
        elif ch == "-":
            sign = -1
        elif ch == "(":
            stack.append((result, sign))
            result, sign = 0, 1
        elif ch == ")":
            outer, outer_sign = stack.pop()
            result = outer + outer_sign * result
        elif ch != " ":
            raise ValueError(f"unexpected character {ch!r} at {i}")
        i += 1
    return result
```

**Complexity**
- Time: O(n), because every character is read once and every `(` is pushed and popped once.
- Space: O(d) for the stack, where d is the deepest nesting level.

## 10. Tests
[`test_chip.py`](test_chip.py) has 8 cases: names and numbers, single operands and a blank
query, unary minus and nesting, a minus in front of parentheses, an unknown metric
(`KeyError`), a production-style capacity headroom query, 20,000 levels of nesting plus a
50,000-term sum, and 2,000 random expressions checked against Python's own evaluator.

## 11. Interview Talk Track
"The service gets formulas like `limit - (team_a + team_b) - reserved` and must never call
`eval` on user text. With only plus and minus, I keep a running total and the sign of the next
operand. Parentheses are the only hard part, and a stack solves them: at an open bracket I
push the running total and the sign in front of the bracket, then start a new level. At the
close bracket I pop and fold: outer plus sign times inner. That's why a minus in front of
brackets flips every term inside, which is the classic bug. Unary minus is free, because a new
level starts at zero. It's one pass, O(n), and the stack is only as deep as the nesting, which
I'd cap in production. Real PromQL has a generated parser with precedence; the next chip adds times and divide."

## 12. Level Up
1. **"A user sends 10 MB of nested parentheses."** That is a denial-of-service input. Cap the
   expression length and the nesting depth before evaluating, and return a clear 400 error.
   The iterative stack already avoids a recursion crash, but memory still grows with depth.
2. **"The same formula runs every 15 seconds for 5,000 series."** Parse once into a small
   program (postfix order or an AST), cache it by formula text, and run the compiled form
   against each series' values. Parsing then costs nothing per evaluation.
3. **"Values are time series, not single numbers."** Each name now means a vector per label
   set. The same stack structure evaluates it, but every `+` becomes a join on matching labels,
   which is what PromQL's vector matching (`on(...)`, `ignoring(...)`) defines.

## 13. Related Chips
- **DC-OBS-17 Query Math with Precedence**: adds `*` and `/` on top of this.
- **DC-SEC-02 Config Bracket Validator**: the same stack, only checking that brackets match.
- **DC-SEC-20 Nested Config Parser**: a stack that builds nested objects instead of a number.
