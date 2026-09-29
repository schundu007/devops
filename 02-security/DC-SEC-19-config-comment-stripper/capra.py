"""Capra Playground export for DC-SEC-19 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "strip_comments", "params": ["lines"], "types": {}, "ret": "value", "cmp": "exact"}

EXAMPLES = [
    {"args": {"lines": ['resource "aws_s3_bucket" "logs" { // audit bucket',
                        '  /* versioning is',
                        '     required by policy */',
                        '  versioning = true',
                        '}']},
     "explanation": "The // comment ends its line. The two-line block comment removes those lines entirely.",
     "why": {"t": "Line and block comments", "d": "Both comment styles in one HCL-style block."}},
    {"args": {"lines": ["port = 80/* old: 8080", "*/80"]},
     "explanation": "A block comment spanning lines joins the text before it with the text after it: 'port = 8080'.",
     "why": {"t": "Joined lines", "d": "Text around a multi-line block comment becomes one line."}},
]


def _large():
    rng = random.Random(722)
    lines = []
    for i in range(1500):
        r = rng.random()
        if r < 0.2:
            lines.append(f"key_{i} = {i} // note {i}")
        elif r < 0.3:
            lines.append(f"/* block {i} */ key_{i} = true")
        elif r < 0.35:
            lines.append(f"x_{i} = 1 /* open")
            lines.append("still comment */")
        else:
            lines.append(f"key_{i} = \"v{i}\"".replace('"', ""))
    return {"lines": lines}


TESTS = [
    {"args": {"lines": []}, "why": {"t": "Empty", "d": "No lines in, no lines out."}},
    {"args": {"lines": ["a = 1", "b = 2"]}, "why": {"t": "No comments", "d": "Lines pass through unchanged."}},
    {"args": {"lines": ["   ", "// only comment", ""]},
     "why": {"t": "Spaces kept", "d": "A line of spaces is not empty and is kept; a comment-only line is dropped."}},
    {"args": {"lines": ["a/*/b*/c"]}, "why": {"t": "/*/ trap", "d": "'/*/' opens a comment; it does not close itself."}},
    {"args": {"lines": ["/* // inside */x = 1"]}, "why": {"t": "// inside a block", "d": "A // inside a block comment is ignored."}},
    {"args": {"lines": ["x = 1 // a /* b", "y = 2"]}, "why": {"t": "/* after //", "d": "A /* after // is part of the line comment."}},
    {"args": {"lines": ["/*", "", "*/"]}, "why": {"t": "Whole block", "d": "Everything inside the block, blank lines too, disappears."}},
    {"args": _large(), "why": {"t": "Large input", "d": "About 1,600 lines mixing both comment styles."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Character state machine (Optimal)",
     "description": "Carry an in_block flag and a line buffer across lines. Outside a block, /* enters it and // ends the line; inside, skip to */. Emit the buffer at a line end only when outside a block, which joins text around multi-line comments.",
     "time": "O(total characters)", "space": "O(total characters)",
     "keyPoints": ["Skip 2 characters after /* so /*/ stays open", "Emit only outside a block", "Drop lines left empty"]},
]

SOLUTIONS.append(
    {"name": "Regex over the joined text",
     "description": "Join the lines with newlines and delete every // comment (up to the newline) and every /* */ comment (across newlines) with one left-to-right regex. Deleting a block comment deletes the newlines inside it, which joins the text around it. Split again and drop empty lines. An unclosed block also swallows the text before it on its line.",
     "time": "O(total characters)", "space": "O(total characters)",
     "keyPoints": ["One alternation, so whichever comment starts first wins", "Lazy .*? stops at the first */", "Handle an unclosed block at the end separately"],
     "code": '''from __future__ import annotations

import re

COMMENT = re.compile(r"//[^\\n]*|/\\*.*?(\\*/|\\Z)", re.S)


def strip_comments(lines: list[str]) -> list[str]:
    unclosed = False

    def drop(m):
        nonlocal unclosed
        if m.group(0).startswith("/*") and m.group(1) == "":
            unclosed = True
        return ""

    text = COMMENT.sub(drop, "\\n".join(lines))
    if unclosed:
        text = text[:text.rfind("\\n") + 1]
    return [line for line in text.split("\\n") if line]
'''})

WAYS_TO_SOLVE = [
    {"name": "Regex over the joined text", "idea": "Join lines, delete // and /* */ matches in one pass, split again.",
     "time": "O(total characters)", "space": "O(total characters)", "use": "Quick scripts; edge cases like an unclosed block need care."},
    {"name": "Character state machine", "idea": "One flag for 'inside a block' and a buffer that can span lines.",
     "time": "O(total characters)", "space": "O(total characters)", "use": "The standard answer; easy to extend with strings or nesting."},
]

VARIANT_TITLE = "C-style comments"
VARIANT_APPROACH = "Character state machine · O(total characters) · O(total characters)"


def _hash_large():
    rng = random.Random(7221)
    lines = []
    for i in range(1200):
        r = rng.random()
        if r < 0.25:
            lines.append(f"key_{i}=v{i}  # note {i}")
        elif r < 0.4:
            lines.append(f"url_{i}=\"http://h/#frag{i}\" # real comment")
        elif r < 0.5:
            lines.append(f"pat_{i}='a#b' \"c\\\\\"#d\" # x")
        elif r < 0.55:
            lines.append("   # indented comment")
        else:
            lines.append(f"key_{i}={i}")
    return {"lines": lines}


def _nested_large():
    rng = random.Random(7222)
    lines = []
    for i in range(1200):
        r = rng.random()
        if r < 0.2:
            lines.append(f"a_{i} = 1 /* outer /* inner */ still */ b_{i}")
        elif r < 0.3:
            lines.append(f"c_{i} = 2 /* open /* nested")
            lines.append("*/ */ tail // gone")
        elif r < 0.4:
            lines.append(f"d_{i} = 3 // /* not a comment start")
        else:
            lines.append(f"e_{i} = {i}")
    return {"lines": lines}


_HASH_FSM = '''from __future__ import annotations


def strip_hash_comments(lines: list[str]) -> list[str]:
    out = []
    for line in lines:
        buf, quote, i = [], None, 0
        while i < len(line):
            ch = line[i]
            if quote is None:
                if ch == "#":
                    break
                if ch in "'\\"":
                    quote = ch
            elif quote == '"' and ch == "\\\\" and i + 1 < len(line):
                buf.append(ch)
                i += 1
                ch = line[i]
            elif ch == quote:
                quote = None
            buf.append(ch)
            i += 1
        text = "".join(buf).rstrip()
        if text:
            out.append(text)
    return out
'''

_HASH_RESCAN = '''from __future__ import annotations


def strip_hash_comments(lines: list[str]) -> list[str]:
    def quoted_at(line, pos):
        quote, i = None, 0
        while i < pos:
            ch = line[i]
            if quote is None:
                if ch in "'\\"":
                    quote = ch
            elif quote == '"' and ch == "\\\\":
                i += 1
            elif ch == quote:
                quote = None
            i += 1
        return quote is not None or i > pos

    out = []
    for line in lines:
        cut = len(line)
        for pos, ch in enumerate(line):
            if ch == "#" and not quoted_at(line, pos):
                cut = pos
                break
        text = line[:cut].rstrip()
        if text:
            out.append(text)
    return out
'''

_NESTED_FSM = '''from __future__ import annotations


def strip_nested_comments(lines: list[str]) -> list[str]:
    out, buf, depth = [], [], 0
    for line in lines:
        i = 0
        while i < len(line):
            two = line[i:i + 2]
            if two == "/*":
                depth += 1
                i += 2
            elif depth and two == "*/":
                depth -= 1
                i += 2
            elif depth:
                i += 1
            elif two == "//":
                break
            else:
                buf.append(line[i])
                i += 1
        if not depth and buf:
            out.append("".join(buf))
            buf = []
    return out
'''

_NESTED_SPLICE = '''from __future__ import annotations


def strip_nested_comments(lines: list[str]) -> list[str]:
    text = "\\n".join(lines)
    i = 0
    while i < len(text):
        two = text[i:i + 2]
        if two == "//":
            j = text.find("\\n", i)
            text = text[:i] + (text[j:] if j != -1 else "")
        elif two == "/*":
            depth, j = 1, i + 2
            while j < len(text) and depth:
                t = text[j:j + 2]
                if t == "/*":
                    depth, j = depth + 1, j + 2
                elif t == "*/":
                    depth, j = depth - 1, j + 2
                else:
                    j += 1
            if depth:
                text = text[:text.rfind("\\n", 0, i) + 1]
                break
            text = text[:i] + text[j:]
        else:
            i += 1
    return [line for line in text.split("\\n") if line]
'''

VARIANTS = [
    {
        "key": "hash-comments-quotes",
        "title": "# comments outside quotes",
        "approach": "Per-line quote state machine · O(total characters) · O(line length)",
        "spec": {"kind": "fn", "fn": "strip_hash_comments", "params": ["lines"], "cmp": "exact"},
        "statement": "Remove `#` comments from shell, YAML and `.env` files.\n\n### Input\n- `lines`: the lines of the file\n\n### Output\n- The remaining lines in order, with comments removed, trailing whitespace stripped, and lines that end up empty dropped\n\n### Rules\n- An **unquoted** `#` starts a comment that runs to the end of the line\n- A `#` inside quotes is data: `url=\"http://h/#top\"` has no comment\n- `'...'` quotes have no escapes\n- Inside `\"...\"`, a backslash escapes the next character, so `\\\"` does not close the string\n- Quotes never span lines: an unclosed quote ends with its line",
        "examples": [
            {"args": {"lines": ["url=\"http://h/#top\"  # docs link", "# header", "mode='a#b'"]},
             "explanation": "The # inside double quotes and the one inside single quotes are data. The real comment and the comment-only line go.",
             "why": {"t": "Quoted #", "d": "A # inside either kind of quote is not a comment."}},
            {"args": {"lines": ["msg=\"say \\\"hi\\\" #1\" # end", "path=C:\\\\tmp # win"]},
             "explanation": "The escaped quotes keep the string open, so #1 is data. Outside quotes a backslash is an ordinary character.",
             "why": {"t": "Escaped quote", "d": "\\\" inside double quotes does not end the string."}},
        ],
        "constraints": ["0 ≤ lines.length ≤ 5 · 10³", "0 ≤ lines[i].length ≤ 200", "Printable ASCII"],
        "hints": [
            "Walk each line character by character, remembering which quote (if any) you are inside.",
            "Only an unquoted # matters. Inside double quotes, a backslash consumes the next character too.",
            "Reset the quote state at every new line, then strip trailing spaces and skip empty results.",
        ],
        "tests": [
            {"args": {"lines": []}, "why": {"t": "Empty", "d": "No lines in, none out."}},
            {"args": {"lines": ["", "   ", "#", "  # x"]}, "why": {"t": "Blank and comment-only", "d": "Every line ends up empty and is dropped."}},
            {"args": {"lines": ["a='it''s' # c", "b=\"x\"\"y\"#z"]}, "why": {"t": "Adjacent quotes", "d": "Back-to-back quoted strings close and reopen correctly."}},
            {"args": {"lines": ["v=\"open # not closed", "w=1 # c"]}, "why": {"t": "Unclosed quote", "d": "An open quote swallows the # to the end of its line only."}},
            {"args": {"lines": ["k='a\\' # c"]}, "why": {"t": "No escapes in single quotes", "d": "A backslash does not escape inside single quotes, so the quote closes and # starts a comment."}},
            {"args": {"lines": ["x=\"a\\\\\" # c", "y=\"\\\\\\\"#\""]}, "why": {"t": "Escaped backslash", "d": "\\\\ is one escaped backslash, so the next quote does close the string."}},
            {"args": _hash_large(), "why": {"t": "Large input", "d": "1,200 lines mixing quoted #, escapes and real comments."}},
        ],
        "solutions": [
            {"name": "Quote state machine (Optimal)",
             "description": "Scan each line once with a quote state: none, single or double. An unquoted # ends the line; inside double quotes a backslash copies the next character as well.",
             "time": "O(total characters)", "space": "O(line length)",
             "keyPoints": ["One pass per line", "Escapes only inside double quotes", "Strip trailing spaces, then drop empty lines"],
             "code": _HASH_FSM},
            {"name": "Rescan the prefix for each #", "slow": True,
             "description": "For each # in a line, rescan the line from the start to decide whether that position is inside quotes. The first unquoted # is the cut point.",
             "time": "O(L²) per line", "space": "O(L)",
             "keyPoints": ["Each check is independent and easy to test", "Quadratic on lines full of #"],
             "code": _HASH_RESCAN},
        ],
        "starter": '''from __future__ import annotations


def strip_hash_comments(lines: list[str]) -> list[str]:
    """Remove unquoted # comments, strip trailing spaces, drop empty lines."""
    # TODO
    raise NotImplementedError
''',
    },
    {
        "key": "nested-block-comments",
        "title": "Nested block comments",
        "approach": "State machine with a depth counter · O(total characters) · O(total characters)",
        "spec": {"kind": "fn", "fn": "strip_nested_comments", "params": ["lines"], "cmp": "exact"},
        "statement": "Remove comments where block comments **nest**, as in some config languages (and Rust, Swift, Kotlin).\n\n### Input\n- `lines`: the lines of the file\n\n### Output\n- The remaining lines in order; lines left empty are dropped\n\n### Rules\n- `/* a /* b */ c */` is one comment, because the inner `*/` only closes the inner `/*`; commenting out a block that already has a comment inside then works\n- Outside comments, `//` starts a line comment and `/*` opens a block\n- Inside a block, `/*` opens one more level and `*/` closes one; `//` means nothing\n- A `*/` outside any comment is ordinary text\n- As in the main problem, a block that spans lines joins the text before it with the text after it\n- Text on a line where a block never closes is dropped",
        "examples": [
            {"args": {"lines": ["x = 1 /* off: /* old */ y = 2 */ z = 3"]},
             "explanation": "The inner */ closes the inner /*, so y = 2 is still commented out. Only 'x = 1 ' and ' z = 3' remain.",
             "why": {"t": "One level of nesting", "d": "The first */ does not end the outer comment."}},
            {"args": {"lines": ["a = 1 /* start", "/* inner", "*/ still", "*/ b = 2"]},
             "explanation": "The block opens on line 1 and closes on line 4 after two */. The text around it joins into 'a = 1  b = 2'.",
             "why": {"t": "Nested across lines", "d": "Depth carries from line to line."}},
        ],
        "constraints": ["0 ≤ lines.length ≤ 5 · 10³", "0 ≤ lines[i].length ≤ 200", "Nesting depth ≤ 100"],
        "hints": [
            "Replace the in-block flag with a depth counter: /* adds one, */ takes one away while depth > 0.",
            "After matching a two-character token, skip both characters, so /*/ opens a level and does not also close it.",
            "Emit the buffered line only when depth is back to 0 at the end of a source line.",
        ],
        "tests": [
            {"args": {"lines": []}, "why": {"t": "Empty", "d": "No lines in, none out."}},
            {"args": {"lines": ["a */ b", "c"]}, "why": {"t": "Stray close", "d": "*/ with no open comment is plain text."}},
            {"args": {"lines": ["p /* /* /* deep */ */ */ q"]}, "why": {"t": "Three levels", "d": "Three opens need three closes."}},
            {"args": {"lines": ["keep /* one /* two */", "lost"]}, "why": {"t": "Never closed", "d": "Depth never returns to 0, so nothing after 'keep' is emitted, not even 'keep'."}},
            {"args": {"lines": ["a /*/ b */ c", "d // x /* y", "e"]}, "why": {"t": "/*/ and // traps", "d": "/*/ opens without closing; /* after // is inside a line comment."}},
            {"args": {"lines": ["/* // not a line comment */ v = 1", "   "]}, "why": {"t": "// inside a block", "d": "// is ignored inside a block; a line of spaces is kept."}},
            {"args": _nested_large(), "why": {"t": "Large input", "d": "About 1,300 lines with nested, multi-line and line comments."}},
        ],
        "solutions": [
            {"name": "Depth-counting state machine (Optimal)",
             "description": "The main problem's scanner with a depth counter instead of a flag. Tokens are matched two characters at a time; the line buffer is emitted only at depth 0.",
             "time": "O(total characters)", "space": "O(total characters)",
             "keyPoints": ["depth > 0 means inside a comment", "Only /* and */ matter inside a comment", "Skip both characters of a token"],
             "code": _NESTED_FSM},
            {"name": "Find and splice each comment", "slow": True,
             "description": "Join the lines, then scan for the first comment, find its matching end by counting depth, cut it out of the string, and continue from the cut. Each cut copies the rest of the text.",
             "time": "O(n · c) for c comments", "space": "O(n)",
             "keyPoints": ["Matching the close by depth is the core idea", "Every splice copies the string: quadratic in the worst case"],
             "code": _NESTED_SPLICE},
        ],
        "starter": '''from __future__ import annotations


def strip_nested_comments(lines: list[str]) -> list[str]:
    """Remove // and nested /* */ comments; drop lines left empty."""
    # TODO
    raise NotImplementedError
''',
    },
]
