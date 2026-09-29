"""Capra Playground export for DC-SEC-01 (see tools/export_capra.py).

Driver kind: the chip has two entry points (normalize_path and is_within_root),
and each case checks both for a list of requested paths under one root.
"""

SPEC = {"kind": "driver", "fn": "normalize_path", "params": ["root", "paths"], "types": {}, "ret": "value", "cmp": "exact"}

DRIVER = '''
def __drive(args):
    root = args["root"]
    return [{"normalized": normalize_path(p), "allowed": is_within_root(root, p)} for p in args["paths"]]
'''


def case(root, paths):
    return {"root": root, "paths": paths}


EXAMPLES = [
    {"args": case("/srv/app", ["/srv/app/../../etc/passwd", "static/logo.png", "/srv/app2/secret"]),
     "explanation": "The first path climbs out to /etc/passwd: blocked. The relative path stays under /srv/app. /srv/app2 only shares a text prefix with the root, so it is blocked too.",
     "why": {"t": "Traversal · Prefix trap", "d": "Escaping with .., and a sibling folder that shares the root's text prefix."}},
    {"args": case("/", ["/home//foo/", "/../", "/a/./b/../../c/"]),
     "explanation": "Repeated slashes collapse, .. at the top stays at /, and . is dropped. With root /, everything is allowed.",
     "why": {"t": "Normalization rules", "d": "//, trailing /, .. at the top, and . segments."}},
]

TESTS = [
    {"args": case("/srv/app", [""]), "why": {"t": "Empty path", "d": "An empty path means /, which is outside /srv/app."}},
    {"args": case("/srv/app", ["/srv/app"]), "why": {"t": "Exactly the root", "d": "The root itself is inside the root."}},
    {"args": case("/srv/app", ["/srv/app/..."]), "why": {"t": "Three dots", "d": "'...' is an ordinary name, not a parent reference."}},
    {"args": case("/srv/app", ["../app/config.yml", "../app-old/config.yml", "./a/../../b"]),
     "why": {"t": "Relative escapes", "d": "Relative requests that leave the root and come back, or don't."}},
    {"args": case("/srv/app/", ["/srv/app/uploads/./x.png", "/srv//app/uploads"]),
     "why": {"t": "Messy root", "d": "A root with a trailing slash still compares by whole segments."}},
    {"args": case("/data", ["/data/../../../../etc/shadow", "/../../data/reports"]),
     "why": {"t": "Deep climb", "d": "More .. segments than levels; the path stops at /."}},
    {"args": case("/var/www", ["/var/www/html/index.html", "html/../../log/nginx/access.log", "/var/www-backup/dump.sql"]),
     "why": {"t": "Web server request", "d": "Typical requests to a static file server, including a log-file traversal."}},
    {"args": case("/srv", ["/" + "/".join(["a", "..", "b"] * 300), "x/" * 500 + "../" * 499 + "..", "a/" * 400]),
     "why": {"t": "Large input", "d": "Long paths with hundreds of segments and .. pairs."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Stack of segments (Optimal)",
     "description": "Split on /, skip empty and . segments, pop on .., push names, then join. For the guard, join a relative request onto the root, normalize both, and compare whole segments.",
     "time": "O(n)", "space": "O(n)",
     "keyPoints": ["'..' at the top stays at /", "Compare whole segments: /srv/app2 is not inside /srv/app", "In production also resolve symlinks with realpath"]},
    {"name": "posixpath.normpath", "slow": True,
     "description": "Use the standard library's text normalizer, fix its POSIX rule that keeps a leading //, and check containment with posixpath.commonpath.",
     "time": "O(n)", "space": "O(n)",
     "keyPoints": ["An independent check of the stack version", "normpath keeps a leading '//' (POSIX allows it), so fold it to '/'"],
     "code": '''from __future__ import annotations

import posixpath


def normalize_path(path: str) -> str:
    p = posixpath.normpath("/" + path)
    return "/" + p.lstrip("/")


def is_within_root(root: str, requested: str) -> bool:
    base = normalize_path(root)
    target = normalize_path(requested if requested.startswith("/") else base + "/" + requested)
    return posixpath.commonpath([base, target]) == base
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Rewrite until stable", "idea": "Repeatedly replace //, /./ and /name/../ in the string.",
     "time": "O(n²)", "space": "O(n)", "use": "Never in a request path: slow and easy to get wrong."},
    {"name": "Stack of segments", "idea": "Split on /, push names, pop on .., join.",
     "time": "O(n)", "space": "O(n)", "use": "The standard answer; then compare whole segments with the root."},
]

import random

VARIANT_TITLE = "Path traversal guard"
VARIANT_APPROACH = "Stack of segments · O(n) · O(n)"


def _cd_large():
    rng = random.Random(1013)
    parts = ["a", "b", "logs", "..", ".", "...", "", "etc"]
    cmds = []
    for _ in range(300):
        r = rng.random()
        if r < 0.1:
            cmds.append("-")
        elif r < 0.2:
            cmds.append("~/" + "/".join(rng.choice(parts) for _ in range(rng.randint(0, 3))))
        elif r < 0.35:
            cmds.append("/" + "/".join(rng.choice(parts) for _ in range(rng.randint(0, 4))))
        else:
            cmds.append("/".join(rng.choice(parts) for _ in range(rng.randint(1, 4))))
    return {"home": "/home/deploy", "commands": cmds}


def _zip_large():
    rng = random.Random(1014)
    parts = ["a", "b", "..", ".", "etc", "passwd", "", "..."]
    entries = []
    for _ in range(400):
        name = "/".join(rng.choice(parts) for _ in range(rng.randint(1, 6)))
        r = rng.random()
        if r < 0.1:
            name = "/" + name
        elif r < 0.2:
            name = name.replace("/", "\\")
        elif r < 0.25:
            name = "C:" + name
        entries.append(name)
    return {"dest": "/tmp/extract", "entries": entries}


_CD_STACK = '''from __future__ import annotations


def pwd_after(home: str, commands: list[str]) -> list[str]:
    home_parts = [p for p in home.split("/") if p and p != "."]
    cwd: list[str] = []
    old: list[str] | None = None
    out = []
    for arg in commands:
        if arg == "-":
            if old is not None:
                cwd, old = old, cwd
            out.append("/" + "/".join(cwd))
            continue
        if arg == "~" or arg.startswith("~/"):
            new, arg = list(home_parts), arg[1:]
        elif arg.startswith("/"):
            new = []
        else:
            new = list(cwd)
        for part in arg.split("/"):
            if part == "" or part == ".":
                continue
            if part == "..":
                if new:
                    new.pop()
            else:
                new.append(part)
        old, cwd = cwd, new
        out.append("/" + "/".join(cwd))
    return out
'''

_CD_REWRITE = '''from __future__ import annotations

import re


def rewrite(path: str) -> str:
    p = "/" + path + "/"
    while True:
        q = re.sub(r"/+", "/", p).replace("/./", "/")
        q = re.sub(r"^/\\.\\./", "/", q)
        q = re.sub(r"/(?!\\.\\./)[^/]+/\\.\\./", "/", q, count=1)
        if q == p:
            break
        p = q
    return "/" + p.strip("/")


def pwd_after(home: str, commands: list[str]) -> list[str]:
    cwd, old, out = "/", None, []
    for arg in commands:
        if arg == "-":
            if old is not None:
                cwd, old = old, cwd
            out.append(cwd)
            continue
        if arg == "~" or arg.startswith("~/"):
            full = home + "/" + arg[1:]
        elif arg.startswith("/"):
            full = arg
        else:
            full = cwd + "/" + arg
        old, cwd = cwd, rewrite(full)
        out.append(cwd)
    return out
'''

_ZIP_DEPTH = '''from __future__ import annotations

import re


def safe_targets(dest: str, entries: list[str]) -> list[str | None]:
    base = "/" + "/".join(p for p in dest.split("/") if p and p != ".")
    out: list[str | None] = []
    for entry in entries:
        name = entry.replace("\\\\", "/")
        if name.startswith("/") or re.match(r"[A-Za-z]:", name):
            out.append(None)
            continue
        stack: list[str] = []
        escaped = False
        for part in name.split("/"):
            if part == "" or part == ".":
                continue
            if part == "..":
                if not stack:
                    escaped = True  # it climbed above dest, even if it comes back later
                    break
                stack.pop()
            else:
                stack.append(part)
        if escaped or not stack:
            out.append(None)
        else:
            out.append(base.rstrip("/") + "/" + "/".join(stack))
    return out
'''

_ZIP_PREFIXES = '''from __future__ import annotations

import posixpath


def safe_targets(dest: str, entries: list[str]) -> list[str | None]:
    base = "/" + posixpath.normpath("/" + dest).lstrip("/")
    out: list[str | None] = []
    for entry in entries:
        name = entry.replace("\\\\", "/")
        if name.startswith("/") or (len(name) >= 2 and name[1] == ":" and name[0].isascii() and name[0].isalpha()):
            out.append(None)
            continue
        parts = name.split("/")
        rel = "."
        for k in range(1, len(parts) + 1):
            rel = posixpath.normpath("/".join(parts[:k]) or ".")
            if rel == ".." or rel.startswith("../"):
                break
        if rel == "." or rel == ".." or rel.startswith("../"):
            out.append(None)
        else:
            out.append(base.rstrip("/") + "/" + rel)
    return out
'''

VARIANTS = [
    {
        "key": "shell-cd",
        "title": "Track the working directory",
        "approach": "Stack of segments per cd · O(total characters) · O(depth)",
        "spec": {"kind": "fn", "fn": "pwd_after", "params": ["home", "commands"], "cmp": "exact"},
        "statement": "Replay the `cd` commands from a shell history to learn which directory each later command ran in.\n\n### Input\n- `home`: the home directory\n- `commands`: each entry is the argument to one `cd`\n\n### Output\n- The working directory after each command\n\n### Rules\n- The shell starts at `/`\n- An argument is an absolute path (`/var/log`) or a path relative to the current directory (`../etc`)\n- `~` is the `home` directory, and `~/x` is a path under it\n- `-` returns to the **previous** directory and swaps, so `cd -` twice comes back; before any other `cd` it stays put\n- Paths use the main problem's text rules: `.` is dropped, `..` removes a name and stays at `/` at the top, repeated slashes collapse\n- Every directory exists",
        "examples": [
            {"args": {"home": "/home/deploy", "commands": ["/var/log", "../lib/./docker", "-", "~/releases//v2", ".."]},
             "explanation": "/var/log, then /var/lib/docker, back to /var/log, then /home/deploy/releases/v2, then up to /home/deploy/releases.",
             "why": {"t": "Every form", "d": "Absolute, relative, -, ~ and .. in one session."}},
            {"args": {"home": "/root", "commands": ["..", "-", "-"]},
             "explanation": "cd .. at / stays at /. The previous directory is also /, so cd - does not move.",
             "why": {"t": "Top of the tree", "d": ".. at / stays at /."}},
        ],
        "constraints": ["0 ≤ commands.length ≤ 10³", "0 ≤ commands[i].length ≤ 200", "home is an absolute path"],
        "hints": [
            "Keep the current directory as a list of segments, not a string, so a relative cd only touches the new segments.",
            "An absolute path starts from an empty list, ~ from the home segments, anything else from a copy of the current list.",
            "Save the old list before every cd so that cd - can swap back.",
        ],
        "tests": [
            {"args": {"home": "/home/a", "commands": []}, "why": {"t": "No commands", "d": "Nothing replayed, nothing returned."}},
            {"args": {"home": "/home/a", "commands": ["-"]}, "why": {"t": "cd - first", "d": "No previous directory yet: stay at /."}},
            {"args": {"home": "/home/a", "commands": ["x", "y", "-", "-", "-"]}, "why": {"t": "Swap back and forth", "d": "cd - keeps toggling between the last two directories."}},
            {"args": {"home": "/home/a", "commands": ["~", "~/", "~/../b", "..."]}, "why": {"t": "Home forms", "d": "~, ~/ and ~/.. resolve against home; '...' is an ordinary name."}},
            {"args": {"home": "/", "commands": ["~/etc", "/../../tmp//x/./", "../../../.."]}, "why": {"t": "Deep climb", "d": "More .. than levels stops at /; home can be / itself."}},
            {"args": {"home": "/home/a", "commands": ["", ".", "//"]}, "why": {"t": "Empty and dot", "d": "An empty relative path and . stay put; // is the root."}},
            {"args": _cd_large(), "why": {"t": "Large input", "d": "300 random cd commands of every form."}},
        ],
        "solutions": [
            {"name": "Segment stack per command (Optimal)",
             "description": "Hold the working directory as a list of segments. Pick the starting list (empty, home or current), apply the argument's segments with push and pop, and keep the old list for cd -.",
             "time": "O(total characters)", "space": "O(depth)",
             "keyPoints": ["Start list decides absolute, relative or home", "Only the new argument is scanned", "Swap current and old for cd -"],
             "code": _CD_STACK},
            {"name": "Rewrite the full path until stable", "slow": True,
             "description": "Glue the argument onto the current path as text and keep applying regex rewrites for //, /./ and /name/../ until nothing changes.",
             "time": "O(L²) per command", "space": "O(L)",
             "keyPoints": ["Each rewrite pass copies the string", "Easy to get the '...' and top-level .. cases wrong"],
             "code": _CD_REWRITE},
        ],
        "starter": '''from __future__ import annotations


def pwd_after(home: str, commands: list[str]) -> list[str]:
    """Return the working directory after each cd argument, starting from /."""
    # TODO
    raise NotImplementedError
''',
    },
    {
        "key": "zip-slip",
        "title": "Zip Slip extraction guard",
        "approach": "Depth counter over the entry's segments · O(total characters) · O(depth)",
        "spec": {"kind": "fn", "fn": "safe_targets", "params": ["dest", "entries"], "cmp": "exact"},
        "statement": "Check each archive entry before a CI job unpacks it; entry names are attacker-controlled (the **Zip Slip** bug).\n\n### Input\n- `dest`: the directory the archive is unpacked into\n- `entries`: the archive entry names\n\n### Output\n- For each entry, the path it would be written to, or `null` to refuse it\n- The path is the normalized `dest` plus the entry's normalized segments\n\n### Rules\n- Backslashes are separators too (archives built on Windows)\n- Refuse absolute names: a leading `/` or `\\`, or a drive like `C:`\n- Refuse any entry whose `..` would climb **above** `dest` at any point, even if later segments come back in (`../dest/x` is refused), as Go's `filepath.IsLocal` does\n- Refuse an entry that resolves to `dest` itself (`.`, `a/..`, empty)",
        "examples": [
            {"args": {"dest": "/tmp/extract", "entries": ["app/bin/run.sh", "../../etc/cron.d/x", "docs/../README.md", "..\\..\\evil.dll"]},
             "explanation": "The first and third stay inside. The second climbs out. The fourth climbs out with Windows separators.",
             "why": {"t": "Classic Zip Slip", "d": "Traversal with both separator styles."}},
            {"args": {"dest": "/srv/app", "entries": ["../app/config.yml", "/etc/passwd", "C:/Windows/x", "a/.."]},
             "explanation": "../app/config.yml would land back inside, but it leaves dest on the way, so it is refused. The next two are absolute. a/.. names dest itself.",
             "why": {"t": "Strict rules", "d": "Leaving and re-entering, absolute names and the dest itself are all refused."}},
        ],
        "constraints": ["0 ≤ entries.length ≤ 10³", "0 ≤ entries[i].length ≤ 300", "dest is an absolute path"],
        "hints": [
            "You do not need to normalize dest + entry together. Walk only the entry's segments with a stack.",
            "A .. on an empty stack is the moment the entry leaves dest: refuse it right there.",
            "Check the separator and the absolute forms before walking, and refuse an empty stack at the end.",
        ],
        "tests": [
            {"args": {"dest": "/out", "entries": []}, "why": {"t": "Empty archive", "d": "No entries in, none out."}},
            {"args": {"dest": "/out", "entries": ["", ".", "./", "x/.."]}, "why": {"t": "Names for dest", "d": "Every one of these resolves to dest itself."}},
            {"args": {"dest": "/out/", "entries": ["a//b/./c", "...", "a\\b\\..\\c"]}, "why": {"t": "Normalization", "d": "Messy but safe names; dest has a trailing slash."}},
            {"args": {"dest": "/out", "entries": ["\\abs", "c:rel", "Z:\\x", "1:x"]}, "why": {"t": "Absolute forms", "d": "Backslash root and drive letters are refused; '1:' is not a drive."}},
            {"args": {"dest": "/", "entries": ["etc/hosts", "../etc/hosts"]}, "why": {"t": "Root destination", "d": "Even with dest /, climbing above it is refused."}},
            {"args": {"dest": "/out", "entries": ["a/b/../../c", "a/b/../../../c"]}, "why": {"t": "Exactly back to dest", "d": "Climbing back to dest's level is fine; one more .. is not."}},
            {"args": _zip_large(), "why": {"t": "Large input", "d": "400 random entries mixing separators, drives and traversal."}},
        ],
        "solutions": [
            {"name": "Depth counter on the entry (Optimal)",
             "description": "Swap backslashes for slashes and refuse absolute names. Walk the entry's segments with a stack; a .. on an empty stack means it escaped. Refuse an empty result, otherwise join it under dest.",
             "time": "O(total characters)", "space": "O(depth)",
             "keyPoints": ["Check every prefix, not just the final path", "Treat \\ as a separator", "Refuse drive letters and names that equal dest"],
             "code": _ZIP_DEPTH},
            {"name": "Normalize every prefix", "slow": True,
             "description": "For each prefix of the entry's segments, normalize it with posixpath.normpath and refuse the entry as soon as a prefix starts with '..'.",
             "time": "O(k²) per entry of k segments", "space": "O(k)",
             "keyPoints": ["Uses the standard normalizer", "Renormalizes the whole prefix at every step"],
             "code": _ZIP_PREFIXES},
        ],
        "starter": '''from __future__ import annotations


def safe_targets(dest: str, entries: list[str]) -> list[str | None]:
    """Return the target path for each archive entry, or None if it is unsafe."""
    # TODO
    raise NotImplementedError
''',
    },
]
