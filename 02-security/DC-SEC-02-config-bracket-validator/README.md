Source: Handbook #16 Valid Parentheses — `apps/camora/src/data/capra/top100/16.json` (copied unchanged as `handbook.json`)

# DC-SEC-02 · Config Bracket Validator

## 1. Header `DevOps layer`
| | |
|---|---|
| Chip ID | DC-SEC-02 |
| Difficulty | Easy |
| Pattern | Stack |
| Track | Cloud Security & IAM (SEC) |
| Classic pattern | LeetCode 20 |
| Premium | No |
| Time box | 15 min |
| Source | Handbook #16 Valid Parentheses |

## 2. The Scenario `DevOps layer`
A pull request changes `modules/network/security_groups.tf`. Someone deleted a `]` after
`cidr_blocks = ["10.0.0.0/16", "192.0.2.0/24"`. `terraform validate` would catch it, but only
after a 90-second `terraform init` in CI. Your team wants a pre-commit check that runs in
milliseconds: strip out everything except brackets (ignoring those inside quoted strings)
and fail fast if any `{`, `[` or `(` is not closed in the right order.

**Mapping: DevOps term → handbook name**

| DevOps term | Handbook name |
|---|---|
| the bracket skeleton of a JSON/HCL file | `s` |
| block `{ }`, list `[ ]`, call `( )` | the three bracket types |
| "file is structurally balanced" | `isValid(s) == True` |
| the open blocks you are currently inside | the stack |

## 3. Why This Is DevOps `DevOps layer`
**Production reality:** Config files for Terraform, Kubernetes (JSON), CloudFormation and
CI pipelines are nested blocks. A single missing bracket breaks the whole file, and the full
tool often reports it far from the real mistake, or only after slow setup steps. A stack-based
bracket check finds the first mismatch in one linear pass, so a pre-commit hook or the first CI
step can fail early with a clear line number.

**Where you see it:** pre-commit hooks, editor bracket matching, `jq` and JSON parsers
reporting "unexpected end of input", `terraform fmt` and `terraform validate`.

**Reality check:** Real parsers do much more: they track strings, escapes, comments and
the grammar itself. Brackets inside quoted strings must be ignored (this chip's DevOps test
does that with a small pre-filter). The bracket stack is the lint core, not a full parser.

**What breaks if you get it wrong:** A check that only counts brackets (equal numbers of
`[` and `]`) accepts `[{]}`. The broken file reaches the apply stage, and a pipeline that
applies modules one by one can leave the environment half-changed.

## 4. Problem Statement `From handbook`
You are given a string `s` made up only of the bracket characters `(`, `)`, `{`, `}`, `[` and `]`. Decide whether it is **valid**.

A string is valid when every opening bracket is closed by a bracket of the same type, brackets are closed in the correct order (the most recently opened one closes first), and every closing bracket has a matching opener. Return `true` or `false`.

## 5. Input / Output format and Constraints
**Input / Output format `(added)`:** `isValid(s: str) -> bool`, a plain function (the handbook's code has no `Solution` class).

**Constraints `From handbook`**
- 1 ≤ s.length ≤ 10⁴
- `s` consists of parentheses only: '()[]{}'.

## 6. Examples `From handbook`
**Example 1 — Answer exists**
```
Input:  s = "()"
Output: true
```

**Example 2 — Answer exists**
```
Input:  s = "()[]{}"
Output: true
```
Three independent pairs, each closed properly.

**Example 3 — No answer**
```
Input:  s = "(]"
Output: false
```
`(` is closed by the wrong type.

**Example 4 — Answer exists**
```
Input:  s = "([])"
Output: true
```
The inner pair closes before the outer one.

## 7. Starter Code `(added)`
The handbook builds its starter from the problem's function signature and stores no starter file. See
[`starter.py`](starter.py): the same `isValid` signature, with a TODO body.

```bash
make try CHIP=02-security/DC-SEC-02-config-bracket-validator
```

## 8. Hints `From handbook`
1. The bracket that must close next is always the most recently opened one.
2. That last-in, first-out behavior is exactly a stack.
3. Push openers; on a closer, the stack must be non-empty and its top must be the matching opener (pop it). At the end, the stack must be empty.

## 9. Solution `From handbook`
#### Brute Force (String Replace)
Replace matching pairs repeatedly until no more matches are found.

- Repeatedly remove matching pairs
- Simple but inefficient
- Creates new strings each iteration

Time: O(n²) · Space: O(n)

```python
def isValid(s):
    while '()' in s or '[]' in s or '{}' in s:
        s = s.replace('()', '').replace('[]', '').replace('{}', '')
    return s == ''
```

#### Stack (Optimal)
Use a stack: push opening brackets, pop and match for closing brackets.

- Stack LIFO matches bracket nesting
- Map closing to opening brackets
- Stack must be empty at end

Time: O(n) · Space: O(n)

```python
def isValid(s):
    stack = []
    mapping = {')': '(', ']': '[', '}': '{'}
    for char in s:
        if char in mapping:
            if not stack or stack[-1] != mapping[char]:
                return False
            stack.pop()
        else:
            stack.append(char)
    return len(stack) == 0
```

`solution.py` is the handbook's optimal Python solution (Stack), copied unchanged. The
handbook's Java, C++, Go, JavaScript and Bash versions are in `handbook.json` → `solutions[].code`.

## 10. Tests
**From handbook:** 29 cases in `handbook.json` → `tests`, run unchanged by `test_chip.py`.

**`(added)`** [`test_chip.py`](test_chip.py) wraps those cases in pytest. It also runs
**every** Python solution from the handbook against them (the Step 3 check), and adds two
DevOps-layer cases: a Terraform security-group block (with brackets inside a quoted string
that must be ignored) and the same block with a deleted `]`, plus large inputs (100,000-deep
nesting and 500 random strings checked against a repeated-removal reference).

## 11. Interview Talk Track `DevOps layer`
"This is the core of a config lint: are the blocks balanced? I walk the characters once. An
opening bracket goes on a stack. A closing bracket must match the top of the stack, or the file
is broken right there, which also gives me the exact position for the error message. At the
end, the stack must be empty, or something was never closed. It's O(n) time and O(n) space
in the worst case. In a real pre-commit hook I'd skip characters inside quoted strings and
comments first, because `description = "(beta]"` is valid HCL. And I'd report the line and
column of the first mismatch, since that's what saves the engineer time."

## 12. Level Up `DevOps layer`
1. **"Report where the error is."** Push `(char, line, column)` instead of just the char. On a
   mismatch, report both the closing position and the unmatched opener's position. At the end,
   the leftover top of the stack is the block that was never closed.
2. **"Someone commits a 2 GB generated JSON file."** The check streams: read in chunks and keep
   only the stack, so memory is O(depth), not O(file size). Also cap the depth (for example
   512). Deep nesting is a known way to crash recursive parsers (see DC-SEC-20).
3. **"Quotes, escapes and comments."** Put a small state machine in front: normal, in-string,
   escape, line comment, block comment. Only emit brackets in the normal state. That is the
   same state machine DC-SEC-19 builds to strip comments.

## 13. Related Chips `DevOps layer`
- **DC-SEC-20 Nested Config Parser**: goes from "is it balanced?" to building the nested structure.
- **DC-SEC-19 Config Comment Stripper**: the pre-filter that removes comments before this check.
- **DC-SEC-01 Path Traversal Guard**: the same push and pop stack, on path segments.
