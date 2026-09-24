Source: New

# DC-SEC-03 · Nested Rule Expander

## 1. Header
| | |
|---|---|
| Chip ID | DC-SEC-03 |
| Difficulty | Medium |
| Pattern | Stack |
| Track | Cloud Security & IAM (SEC) |
| Classic pattern | LeetCode 394 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
Your platform team writes access rules in a short template language, so one line can stand
for many repeated entries: `allow:2[sqs:SendMessage,]3[vpce-a,]end`. Before a policy goes live,
the security review wants to see the **fully expanded** list, because a reviewer cannot
approve what they cannot read. A contractor also submits a 30-character template that would
expand to 10 billion characters. The expander has to refuse that one instead of eating all
the memory on the CI runner.

## 3. Why This Is DevOps
**Production reality:** Infrastructure code is full of compact, nested repetition: Helm
`range` loops, Terraform `dynamic` blocks and `for_each`, Jsonnet and CUE comprehensions.
Reviewers and policy engines need the flattened result to audit exactly what is allowed.
Expanding nested blocks is a stack problem: when a block opens, save what you have and start
fresh. When it closes, repeat the inner text and attach it to the saved outer text.

**Where you see it:** `helm template` (renders charts before review), `terraform plan`
(shows expanded `dynamic` blocks), `kustomize build`, Jsonnet and CUE evaluators.

**Reality check:** AWS IAM does not use `k[...]` syntax. The skill here is flattening nested
structures, not a real policy format. Real template engines also have variables and
conditionals, and they set limits on output size and recursion depth for the same safety reason as this chip.

**What breaks if you get it wrong:** Without an output cap, a "billion laughs" style template
(small input, nested repeats) takes down the CI runner or the admission webhook that renders
it, which is a cheap denial of service. Without correct nesting, the reviewed text differs from
what is deployed.

## 4. Problem Statement
Write `expand(template, max_output)`.

- A block is written `k[body]`: a count `k` (one or more digits) and a body in square brackets.
  It stands for `body` written `k` times in a row.
- Bodies can contain more blocks, nested to any depth.
- Every character that is not a digit or a bracket is copied as it is. Digits only appear
  as counts.
- If the expanded text, or any block while it is being expanded, would be longer than
  `max_output` characters, raise `ValueError`. (The check is conservative: `0[...]` around a
  huge block still fails, because the block is built before it is multiplied by zero.)

## 5. Input / Output format and Constraints
- `expand(template: str, max_output: int = 100_000) -> str`.
- `0 <= len(template) <= 10^4`. Every `[` has a matching `]`, and every `[` follows a count.
- `0 <= k <= 1000`. `k = 0` produces nothing.
- Literal characters are letters and `:`, `-`, `,`, `/`, `.`, `*`.

## 6. Examples
**Example 1: nested**
```
expand("2[x3[y]]")  -> "xyyyxyyy"    # inner block first: "yyy", then "x"+"yyy" twice
```

**Example 2: text around blocks**
```
expand("allow:2[sqs:SendMessage,]3[vpce-a,]end")
  -> "allow:sqs:SendMessage,sqs:SendMessage,vpce-a,vpce-a,vpce-a,end"
```

**Example 3: an expansion bomb (edge case)**
```
expand("10[10[10[10[10[10[10[10[10[10[x]]]]]]]]]]")  -> ValueError   # 10^10 characters
expand("")                                           -> ""
```

## 7. Starter Code
See [`starter.py`](starter.py): `expand` with a docstring and type hints. The body is TODO.

```bash
make try CHIP=02-security/DC-SEC-03-nested-rule-expander
```

## 8. Hints
1. **Nudge:** When you reach `[`, you don't know the body yet. What do you need to remember so you can come back?
2. **Pattern:** A stack of frames: push `(text so far, count)` on `[`, pop on `]` and attach `body * count` to the saved text.
3. **Near-solution:** Build the count digit by digit (`count = count * 10 + d`). On `[`, push `(current, count)`
   and reset both. On `]`, pop `(outer, k)` and set `current = outer + body * k`. Keep a running
   length, and raise before building anything longer than `max_output`.

## 9. Solution
**Approach**
1. Scan left to right, keeping `current` (the text of the open block) and `count`.
2. Digits build `count`. `[` pushes `(current, count)` and starts an empty `current`.
3. `]` pops `(outer, k)`, repeats the body `k` times, and appends it to `outer`.
4. Letters append to `current`. A running length checks the cap *before* building a too-long string.

**Brute force:** Find the innermost `k[...]` with a regex, replace it, and repeat. Each pass
rescans the whole string, so it is O(n × depth) scans over a string that keeps growing.

**Optimal code:** [`solution.py`](solution.py)

```python
def expand(template: str, max_output: int = 100_000) -> str:
    stack: list[tuple[list[str], int]] = []   # (text before this block, repeat count)
    current: list[str] = []
    length, lengths, count = 0, [], 0
    for ch in template:
        if ch.isdigit():
            count = count * 10 + int(ch)
        elif ch == "[":
            stack.append((current, count))
            lengths.append(length)
            current, length, count = [], 0, 0
        elif ch == "]":
            outer, k = stack.pop()
            outer_len = lengths.pop()
            body = "".join(current)
            new_len = outer_len + k * len(body)
            if new_len > max_output:                 # check before allocating
                raise ValueError("expanded output exceeds max_output")
            outer.append(body * k)
            current, length = outer, new_len
        else:
            current.append(ch)
            length += 1
            if length > max_output:
                raise ValueError("expanded output exceeds max_output")
    return "".join(current)
```

**Complexity**
- Time: O(n + L), where L is the output length (at most `max_output`): each input character is
  handled once, and building the output costs its length.
- Space: O(n + L): the stack holds at most one frame per nesting level plus the partial text.

## 10. Tests
[`test_chip.py`](test_chip.py) has 6 cases: normal and nested blocks, empty and single
input, multi-digit and zero counts, expansion bombs and the exact cap boundary, a production
policy template, and a large random check (2,000 random nested templates against an independent
innermost-first regex rewriter).

## 11. Interview Talk Track
"Reviewers need to see a policy fully expanded, so I flatten nested repeat blocks. The
nesting means I can't finish a block until I've seen its end, so I use a stack. On an opening
bracket I push the text built so far and the repeat count, then start fresh. On a closing
bracket I pop, repeat the inner text, and attach it to the outer text. It's linear in input
plus output. The part I'd call out in a security review is the output cap: a 30-character
template can mean 10 billion characters, like the old XML 'billion laughs' attack. So I keep a
running length and refuse before allocating, not after. Helm and Terraform renderers face the same problem."

## 12. Level Up
1. **"Render templates inside a Kubernetes admission webhook."** Put hard limits on output
   size, nesting depth and CPU time, and fail closed (reject the object) if a limit is hit. A
   webhook that hangs can block every deploy in the cluster.
2. **"Show reviewers where each expanded line came from."** Keep, for each output piece,
   the template position it came from, the way source maps work. The review tool can then
   link a suspicious expanded rule back to the template line that made it.
3. **"The body needs the loop index, like `3[port-{i}]`."** Push the counter with the frame
   and substitute `{i}` while repeating. At that point you have a tiny template language: add
   a depth limit and an output cap before adding anything else.

## 13. Related Chips
- **DC-SEC-20 Nested Config Parser**: a stack that builds nested objects instead of text.
- **DC-SEC-02 Config Bracket Validator**: the same bracket stack, only checking balance.
- **DC-OBS-07 Query Expression Evaluator**: a stack over nested parentheses with numbers.
