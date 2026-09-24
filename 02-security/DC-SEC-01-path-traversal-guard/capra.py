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
