Source: New

# DC-OBS-17 · Query Math with Precedence

## 1. Header
| | |
|---|---|
| Chip ID | DC-OBS-17 |
| Difficulty | Medium |
| Pattern | Stack |
| Track | Observability & SRE (OBS) |
| Classic pattern | LeetCode 227 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
You are building a small "custom stat" feature for the internal status page. Users type
formulas over already-resolved counter values, such as `37 * 100 / 1200` for the 5xx percent
of `checkout-api` in the last hour. It is a follow-on to DC-OBS-07, and this time there are no
parentheses, but `*` and `/` must run before `+` and `-`. Someone typed `37 / 1200 * 100` and
got 0, and the bug ticket asks why. Your evaluator has to get the order right every time.

## 3. Why This Is DevOps
**Production reality:** Monitoring queries do arithmetic all the time: error ratios,
percentages, bytes to megabytes, per-pod averages. `errors / total * 100` only means "percent"
if `/` and `*` go left to right and both run before any `+` or `-`. A stack handles this
in one pass. `+` and `-` push a term, while `*` and `/` immediately combine with the last term,
so they happen first. At the end, add up the stack.

**Where you see it:** PromQL binary operators (`*`, `/`, `%` bind tighter than `+`, `-`),
Grafana "Math" expressions, Datadog metric arithmetic, spreadsheet-style formulas in
alerting tools.

**Reality check:** PromQL works on 64-bit floats, so `37 / 1200 * 100` gives 3.08 there.
This chip uses integers that truncate toward zero, so the order of `*` and `/` changes the
result (0 vs 3). PromQL also has `^` (which binds tightest), comparison operators and set
operators, and it applies all of them to whole vectors of series, not single numbers.

**What breaks if you get it wrong:** An evaluator that runs `+` before `*` turns
`base + errors * 100` into the wrong value. A threshold like "page if > 5" then never fires,
or fires constantly, and nobody notices until an outage.

## 4. Problem Statement
Write `evaluate(expr)`. `expr` holds non-negative integers, the operators `+`, `-`, `*`
and `/`, and spaces. There are no parentheses.

- `*` and `/` are applied before `+` and `-`.
- Operators on the same level are applied left to right.
- Division is integer division that truncates toward zero (`7 / 2 = 3`).

The expression is always valid, never divides by zero, and every intermediate result fits in
a 32-bit signed integer. Return the result as an `int`. Do not use `eval`.

## 5. Input / Output format and Constraints
- `expr: str`, with `1 <= len(expr) <= 3 * 10^5`.
- It contains only digits, `+ - * /` and spaces, and holds at least one number.
- Every number is a non-negative integer that fits in 32 bits.
- Returns `int`.

## 6. Examples
**Example 1: precedence**
```
evaluate("3+2*2") -> 7       # 2*2 first, then 3+4
```

**Example 2: truncation (edge case)**
```
evaluate(" 3 / 2 ") -> 1
evaluate("1-7/2")   -> -2    # 7/2 = 3, then 1-3
```

**Example 3: order within a level**
```
evaluate("37 * 100 / 1200") -> 3   # (37*100)/1200
evaluate("37 / 1200 * 100") -> 0   # (37/1200)*100 = 0*100
```

## 7. Starter Code
See [`starter.py`](starter.py): `evaluate(expr)` with a docstring and type hints. The body is TODO.

```bash
make try CHIP=01-observability/DC-OBS-17-query-math-precedence
```

## 8. Hints
1. **Nudge:** Think of the answer as a sum of terms, where a term is a run of numbers joined by `*` and `/`.
2. **Pattern:** A stack of terms. `+n` pushes `n` and `-n` pushes `-n`, while `*n` and `/n` pop the last term, combine it, and push the result back.
3. **Near-solution:** Read digits into `num`, and remember the operator *before* it (start
   with `+`). When you hit the next operator or the end of the string, apply that previous
   operator to `num`, then store the new operator. The answer is `sum(stack)`. For `/`, truncate toward zero.

## 9. Solution
**Approach**
1. Scan left to right, building the current number from its digits.
2. Remember `op`, the operator in front of the current number. At the start it is `+`.
3. When the number ends (at an operator or the end of the string), apply `op`: push `num`,
   push `-num`, or replace the top with `top * num` or `top / num` (truncated).
4. Add up the stack.

**Brute force:** Repeatedly find the first `*` or `/`, compute it, and rebuild the string,
then do the same for `+` and `-`. That is O(n²) string rebuilding, and slow for 300,000
characters.

**Optimal code:** [`solution.py`](solution.py)

```python
def evaluate(expr: str) -> int:
    stack: list[int] = []
    num, op = 0, "+"                      # op = operator in front of num
    for i, ch in enumerate(expr):
        if ch.isdigit():
            num = num * 10 + int(ch)
        if (not ch.isdigit() and ch != " ") or i == len(expr) - 1:
            if op == "+":
                stack.append(num)
            elif op == "-":
                stack.append(-num)
            elif op == "*":
                stack.append(stack.pop() * num)       # * and / act on the last term now
            else:
                prev = stack.pop()
                q = abs(prev) // num                  # exact integer math, no float rounding
                stack.append(q if prev >= 0 else -q)  # truncate toward zero
            op, num = ch, 0
    return sum(stack)
```

**Complexity**
- Time: O(n), with one pass over the string and O(1) work per character.
- Space: O(n) in the worst case, for the stack of terms (for example, all `+`). Keeping only
  a running sum and the last term makes it O(1).

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: precedence, a single number and spaces,
truncation toward zero after a minus, left-to-right order within a level, multi-digit
numbers, production-style error-percentage formulas, and 300 random expressions checked
against an independent two-pass evaluator.

## 11. Interview Talk Track
"The expression is a sum of terms, where a term is numbers joined by times and divide. So I
keep a stack of terms and remember the operator in front of the number I'm reading. When a
number ends, plus pushes it, minus pushes its negative, and times or divide pop the last
term, combine, and push back. That makes multiplication and division happen before the final
sum. At the end I add the stack. It's O(n) with one pass. The trap is division: it must
truncate toward zero, so I divide the absolute values and fix the sign. That's also why
PromQL does this in floating point: in integer math, errors over total times 100 is just
zero. The same stack idea, with parentheses added, is DC-OBS-07."

## 12. Level Up
1. **"Add parentheses."** When you see `(`, push the current running state (total and sign)
   and start fresh. At `)`, finish the inner value and fold it into the saved state. Or use
   recursion: parse an expression until the matching `)`. That is DC-OBS-07, and the step
   toward a real parser.
2. **"Add `^` (power), which binds tighter than `*` and is right-associative, as in PromQL."**
   A two-level stack no longer fits. Use shunting-yard (operator precedence table plus an
   operator stack) or a recursive-descent parser with one function per precedence level.
3. **"Users submit these formulas: what can go wrong?"** Cap the input length, never call
   `eval`, guard against division by zero, and limit nesting depth once parentheses exist.
   Deep nesting can blow the stack, a similar risk to the one in DC-SEC-20.

## 13. Related Chips
- **DC-OBS-07 Query Expression Evaluator**: the same stack, with parentheses and only `+` and `-`.
- **DC-SEC-02 Config Bracket Validator**: the stack as a checker rather than a calculator.
- **DC-SEC-20 Nested Config Parser**: stack or recursion over nested input, and depth limits.
