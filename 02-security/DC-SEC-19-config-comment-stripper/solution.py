"""DC-SEC-19 Config Comment Stripper — reference solution."""
from __future__ import annotations


def strip_comments(lines: list[str]) -> list[str]:
    """Remove // and /* */ comments; drop lines left empty.

    A block comment that spans lines joins the text before it with the text after it.
    """
    out: list[str] = []
    buf: list[str] = []     # the output line being built (may span source lines)
    in_block = False
    for line in lines:
        i = 0
        while i < len(line):
            two = line[i:i + 2]
            if in_block:
                if two == "*/":
                    in_block = False
                    i += 2
                else:
                    i += 1
            elif two == "/*":
                in_block = True
                i += 2          # so "/*/" does not close itself
            elif two == "//":
                break           # rest of this line is a comment
            else:
                buf.append(line[i])
                i += 1
        # Inside a block comment the line has not ended yet: keep building.
        if not in_block and buf:
            out.append("".join(buf))
            buf = []
    return out
