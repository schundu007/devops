Source: New

# DC-SEC-20 · Nested Config Parser

## 1. Header
| | |
|---|---|
| Chip ID | DC-SEC-20 |
| Difficulty | Medium |
| Pattern | Stack / recursion |
| Track | Cloud Security & IAM (SEC) |
| Classic pattern | LeetCode 385 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
The admission webhook `policy-gate` (running at `10.96.14.2:8443` in the cluster) receives
network-policy port groups from tenants as a compact nested value, for example
`[[80,443],[8080,[9000,9001]],[]]`. Before any rule is checked, the webhook parses that text
into real nested lists. Last week a tenant, by accident or not, submitted a value nested
100,000 levels deep, and the webhook pod crashed with a stack overflow. Every deploy in the
cluster was then blocked, because the webhook is set to fail closed.

## 3. Why This Is DevOps
**Production reality:** Policy engines, admission controllers and CI validators all start by
parsing nested data (JSON, YAML, HCL) into objects. The core of any such parser is a stack:
`[` opens a new level, `]` closes it, and values attach to whatever level is open. Because
the input often comes from users, the parser must also defend itself. Real parsers cap nesting
depth so that a tiny, deeply nested payload cannot exhaust the stack or memory.

**Where you see it:** Kubernetes admission webhooks and OPA Gatekeeper reading
`AdmissionReview` JSON, API gateways validating JSON bodies, Terraform reading JSON plans,
and JSON libraries with nesting limits (Python's `json` module fails with `RecursionError` on
extremely deep input, and many other parsers expose an explicit max-depth setting).

**Reality check:** Real formats have strings, floats, objects and escapes. This chip keeps only
integers and lists, which is enough to practise the stack. A production service would also cap the
total body size (for example at the ingress or API server) before parsing even starts.

**What breaks if you get it wrong:** A recursive parser with no depth limit turns a small
request into a crash. If that parser sits in a fail-closed admission webhook, one bad
request stops deployments for the whole cluster, which is a denial of service on your control plane.

## 4. Problem Statement
You get a string `s` that is either an integer (like `"-42"`) or a list written with `[`, `]`
and `,` (like `"[1,[2,[3]],[]]"`), with no spaces. Lists can be empty, and can hold integers
and other lists. Return the value as Python `int`s and `list`s.

Nesting **depth** is the number of lists open at the deepest point: `"5"` has depth 0, `"[1]"`
has depth 1 and `"[[1]]"` has depth 2. If the depth is greater than `max_depth`, raise
`ValueError` instead of parsing.

## 5. Input / Output format and Constraints
- `parse(s: str, max_depth: int = 64) -> int | list`
- `1 <= len(s) <= 5 * 10^5`. `s` is valid: digits, `-`, `[`, `]` and `,` only.
- Integers fit in the range `[-10^9, 10^9]`. `0 <= max_depth <= 10^5`.

## 6. Examples
**Example 1: nested lists**
```
parse("[123,[456,[789]]]")  ->  [123, [456, [789]]]
```

**Example 2: a bare integer and an empty list (edge case)**
```
parse("-7")  ->  -7
parse("[]")  ->  []
```

**Example 3: the depth limit**
```
parse("[[[1]]]", max_depth=3)  ->  [[[1]]]
parse("[[[1]]]", max_depth=2)  ->  ValueError
```

## 7. Starter Code
See [`starter.py`](starter.py): `parse(s, max_depth)` with a docstring and type hints.

```bash
make try CHIP=02-security/DC-SEC-20-nested-config-parser
```

## 8. Hints
1. **Nudge:** When you see `]`, which list is being closed? How do you get back to its parent?
2. **Pattern:** Keep a stack of the lists that are still open. `[` pushes a new list (and
   attaches it to the current top), `]` pops. The stack's size is the current depth.
3. **Near-solution:** Collect digits and `-` into a number buffer. On `,` or `]`, append the
   buffered number to the top list. Before pushing on `[`, check `len(stack) == max_depth` and
   raise if so. Use a loop, not recursion.

## 9. Solution
**Approach**
1. If `s` doesn't start with `[`, it is a plain integer: return `int(s)`.
2. Walk the characters with a stack of open lists.
3. `[`: refuse if the stack is already `max_depth` deep. Otherwise create a list, attach it to
   the current top (if any), and push it.
4. Digits and `-`: add them to the number buffer.
5. `,` or `]`: flush the number buffer into the top list. On `]`, pop. The last popped list is the result.

**Brute force:** A recursive-descent parser is the natural first try. It is O(n), but uses
the call stack for depth, so 100,000 nested `[` crashes Python with `RecursionError` unless you add
the same depth check.

**Optimal code:** [`solution.py`](solution.py)

```python
def parse(s: str, max_depth: int = 64) -> Nested:
    if s[0] != "[":
        return int(s)
    stack: list[list] = []
    num, result = "", []
    for ch in s:
        if ch == "[":
            if len(stack) == max_depth:
                raise ValueError(f"nesting deeper than {max_depth}")  # DoS guard
            new: list = []
            if stack:
                stack[-1].append(new)
            stack.append(new)
        elif ch == "-" or ch.isdigit():
            num += ch
        else:                                    # "," or "]"
            if num:
                stack[-1].append(int(num)); num = ""
            if ch == "]":
                result = stack.pop()
    return result
```

**Complexity**
- Time: O(n), one pass over the string. Each number is built from its own characters once.
- Space: O(n) for the result, and O(min(depth, max_depth)) for the stack.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: a nested list, bare integers and empty lists,
negative numbers and zero, the depth-limit boundary, a 100,000-level nesting attack (refused, while a
5,000-level input still parses with a high limit), a production policy rule tree, and 300 random
values plus a 5,000-element list checked against `json.loads`.

## 11. Interview Talk Track
"Every policy check starts by parsing nested input, and the core is a stack. `[` opens a new
list and attaches it to the current one, `]` closes it, and numbers are buffered until a comma or
a bracket. One pass, O(n). The security part: the input comes from users, so depth is attacker
controlled. A recursive parser turns 100 KB of brackets into a stack overflow, and in a fail-closed
admission webhook that blocks every deploy. So I parse iteratively and enforce a max depth before
pushing, and in production I'd also cap the body size at the ingress."

## 12. Level Up
1. **"Support objects and strings, like JSON."** Add `{` / `}` as another container type on
   the same stack, with keys, and a string state that handles escapes. The depth check stays
   the same, because both containers count as depth.
2. **"The payload is 500 MB."** Don't build the whole tree. Use a streaming (SAX-style) parser
   that emits events such as start-list, value and end-list, and check the policy as the events
   arrive, keeping only the path from the root to the current value.
3. **"Which limits should a public API enforce?"** Body size (reject before parsing), nesting
   depth, the number of elements per container, and the maximum string length. Each one blocks a
   different cheap-to-send, expensive-to-process payload. Set them at the gateway and again in the service.

## 13. Related Chips
- **DC-SEC-02 Config Bracket Validator**: checks the brackets balance before parsing.
- **DC-SEC-03 Nested Rule Expander**: another stack over nested brackets, expanding repeats.
- **DC-SEC-19 Config Comment Stripper**: the pre-processing step before the parser.
