Source: New

# DC-SEC-19 · Config Comment Stripper

## 1. Header
| | |
|---|---|
| Chip ID | DC-SEC-19 |
| Difficulty | Medium |
| Pattern | String state machine |
| Track | Cloud Security & IAM (SEC) |
| Classic pattern | LeetCode 722 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
The platform team keeps service settings in JSONC files (JSON that allows comments), for
example `staging/payments.jsonc`. The policy checker in CI only understands plain JSON, and the
config-drift report diffs files line by line. Someone commented out `"debug": true` with a
`/* ... */` block spanning three lines, and added a `// was us-east-1` note on the region line.
Before either tool runs, a pre-processor must remove every comment and keep the real settings exactly as written.

## 3. Why This Is DevOps
**Production reality:** Many config formats allow comments that strict parsers and policy
tools reject: JSONC (VS Code settings, `tsconfig.json`), HCL (Terraform, which allows `//`, `#`
and `/* */`), and many YAML-adjacent formats. Pipelines strip comments before validating,
diffing or hashing a config, so that a comment-only change does not look like a real one. Doing
this correctly means reading character by character and remembering whether you are inside a comment.

**Where you see it:** VS Code and TypeScript reading JSONC, Terraform's HCL parser, config
linters in CI, drift detection that hashes a normalised config.

**Reality check:** This chip's input has **no string literals**. Real configs do:
`"url": "https://api.example.com"` contains `//` inside quotes, and a naive stripper would cut the
line there and break the config. A real stripper also tracks quote state (and escaped quotes)
and ignores comment markers inside strings. Real stripping would also trim or drop lines that are
left with only spaces, while this chip keeps them.

**What breaks if you get it wrong:** If `/*/` is treated as open-and-close, the commented-out
`"debug": true` comes back to life and ships to staging. If the stripper ignores strings, every
URL in the file is cut in half and the deploy fails the validation step.

## 4. Problem Statement
You get the lines of a config file. Remove comments using these rules:
- `//` starts a line comment. Everything from it to the end of that line is removed.
- `/*` starts a block comment. Everything up to and including the next `*/` is removed, even
  if that is on a later line. The characters right after `/*` cannot close it: `/*/` does not end the block.
- Whichever marker appears first wins. `//` inside a block comment is just comment text, and so
  is `/*` after a `//`.
- When a block comment spans lines, the text before it and the text after it join into **one** line.

Return the remaining lines in order, dropping lines that are empty (`""`). Every `/*` is closed
by the end of the input. There are no string literals.

## 5. Input / Output format and Constraints
- `strip_comments(lines: list[str]) -> list[str]`
- `0 <= len(lines) <= 10^4`, each line has 0–200 printable ASCII characters, with no `"` characters.
- Every block comment is closed. A line made only of spaces is not empty and is kept.

## 6. Examples
**Example 1: both kinds of comment**
```
["a = 1 // set a", "/* header */", "b = 2"]  ->  ["a = 1 ", "b = 2"]
```

**Example 2: a block that spans lines**
```
["a/*comment", "line", "more*/b"]  ->  ["ab"]
```
The text before `/*` and the text after `*/` join.

**Example 3: `/*/` does not close itself (edge case)**
```
["x/*/y*/z"]  ->  ["xz"]
```

## 7. Starter Code
See [`starter.py`](starter.py): `strip_comments(lines)` with a docstring that lists the rules, and type hints.

```bash
make try CHIP=02-security/DC-SEC-19-config-comment-stripper
```

## 8. Hints
1. **Nudge:** You need to remember one thing between characters, and even between lines. What is it?
2. **Pattern:** A two-state machine (inside a block comment, or not) that reads two characters
   at a time to spot `//`, `/*` and `*/`.
3. **Near-solution:** Keep an output buffer across lines. Outside a block: `//` breaks out of
   the line, `/*` enters a block (skip both characters), anything else is copied. Inside a block:
   look only for `*/`. At the end of each line, if you are not inside a block and the buffer is
   non-empty, emit it and clear it.

## 9. Solution
**Approach**
1. Carry an `in_block` flag and a line buffer across the whole input.
2. Scan each line by index, looking at the next two characters.
3. Inside a block: skip characters until `*/`, then leave the block.
4. Outside: `/*` enters a block and skips 2 characters (so `/*/` stays open). `//` ends the line.
   Any other character goes into the buffer.
5. At the end of a line, only emit the buffer if you are outside a block. Otherwise the next
   line keeps adding to it, which is what joins the text around a multi-line block.

**Brute force:** Join everything into one string and repeatedly find the earliest `//` or
`/*` with `str.find`, cutting out comments. It is correct, but each cut rebuilds the string, so
it is O(n²) in the worst case on a large file full of comments.

**Optimal code:** [`solution.py`](solution.py) (key part)

```python
for line in lines:
    i = 0
    while i < len(line):
        two = line[i:i + 2]
        if in_block:
            if two == "*/": in_block = False; i += 2
            else: i += 1
        elif two == "/*": in_block = True; i += 2     # "/*/" stays open
        elif two == "//": break                        # rest is a comment
        else: buf.append(line[i]); i += 1
    if not in_block and buf:
        out.append("".join(buf)); buf = []
```

**Complexity**
- Time: O(total characters), because each character is looked at a constant number of times.
- Space: O(total characters) for the output.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: line and block comments, empty and single inputs,
a multi-line block that joins lines, `/*/`, "first marker wins", a production JSONC settings
file, and 300 random inputs plus a 20,000-line file checked against a `str.find` whole-text brute force.

## 11. Interview Talk Track
"Before a policy check or a drift diff, I strip comments from config. It's a small state
machine: I'm either inside a block comment or not, and I read two characters at a time to spot
the markers. Line comments end the line. Block comments can span lines, so I keep an output
buffer across lines and only emit it when I'm outside a block, which joins the text around the
comment. It's one pass, O(n). The classic bug is `/*/`: after `/*` I skip both characters, so it
can't close itself. The big real-world gap is strings: `https://` contains `//`, so a production
stripper also tracks quote state and escapes."

## 12. Level Up
1. **"Support string literals."** Add a third state, *inside a string*. Enter it on `"` when
   outside a comment, and leave it on an unescaped `"`, tracking `\` escapes. Comment markers
   are ignored inside strings. This is the minimum for real JSONC or HCL.
2. **"Keep line numbers stable for error messages."** Instead of deleting comment text, replace
   it with spaces and keep every newline. The policy checker's "line 42, column 7" then points
   to the right place in the original file.
3. **"HCL also has `#` comments and heredocs."** Add `#` as a line-comment marker, and a
   *heredoc* state that starts at `<<EOF` and ends at a line that is exactly `EOF`, inside which
   nothing is a comment. At that point, use the real HCL parser instead of growing your own.

## 13. Related Chips
- **DC-SEC-02 Config Bracket Validator**: the next CI check after stripping comments.
- **DC-SEC-20 Nested Config Parser**: parsing the cleaned config into nested values.
- **DC-SEC-17 Streaming Secret Scanner**: another character-by-character scan.
