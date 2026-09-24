"""Capra Playground export for DC-OS-01 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "design", "fn": "FileSystem", "params": [], "types": {}, "ret": "value", "cmp": "exact"}


def ops(*calls):
    return {"ops": ["FileSystem"] + [c[0] for c in calls], "vals": [[]] + [list(c[1:]) for c in calls]}


EXAMPLES = [
    {"args": ops(("mkdir", "/a/b/c"), ("ls", "/"), ("ls", "/a/b")),
     "explanation": "mkdir creates every missing parent, like mkdir -p.",
     "why": {"t": "Build and list", "d": "Nested directories in one call."}},
    {"args": ops(("mkdir", "/a/b/c"), ("write", "/a/b/c/d", "hello"), ("write", "/a/b/c/d", " world"),
                 ("read", "/a/b/c/d"), ("ls", "/a/b/c/d")),
     "explanation": "write appends. ls on a file returns just its own name.",
     "why": {"t": "Append and read", "d": "Two writes to one file."}},
    {"args": ops(("ls", "/")),
     "explanation": "A new file system has an empty root.",
     "why": {"t": "Empty root", "d": "ls on an empty file system."}},
]


def _large():
    rng = random.Random(588)
    calls = []
    dirs = ["/etc", "/etc/kubernetes", "/var/log", "/srv/app", "/srv/app/config"]
    for d in dirs:
        calls.append(("mkdir", d))
    for i in range(250):
        d = rng.choice(dirs)
        calls.append(("write", f"{d}/f{i % 40}.txt", f"line{i};"))
    for d in dirs:
        calls.append(("ls", d))
    for i in range(0, 40, 4):
        calls.append(("read", f"/etc/f{i}.txt") if any(c[0] == "write" and c[1] == f"/etc/f{i}.txt" for c in calls) else ("ls", "/"))
    return ops(*calls)


TESTS = [
    {"args": ops(("mkdir", "/x"), ("mkdir", "/x"), ("ls", "/")),
     "why": {"t": "mkdir twice", "d": "Creating an existing directory changes nothing."}},
    {"args": ops(("mkdir", "/b"), ("mkdir", "/a"), ("mkdir", "/c"), ("write", "/B", "x"), ("ls", "/")),
     "why": {"t": "Sorted listing", "d": "ls sorts names in plain string order: uppercase before lowercase."}},
    {"args": ops(("write", "/deep/nested/path/file.log", "data"), ("ls", "/deep/nested"), ("read", "/deep/nested/path/file.log")),
     "why": {"t": "write creates parents", "d": "Writing a file creates missing directories."}},
    {"args": ops(("write", "/f", ""), ("read", "/f"), ("ls", "/")),
     "why": {"t": "Empty content", "d": "A file can exist with no content."}},
    {"args": ops(("mkdir", "/a"), ("write", "/a/f1", "1"), ("mkdir", "/a/d1"), ("ls", "/a"), ("ls", "/a/f1"), ("ls", "/a/d1")),
     "why": {"t": "Files and dirs together", "d": "A directory holding both, and an empty sub-directory."}},
    {"args": ops(("mkdir", "/etc/kubernetes/manifests"), ("write", "/etc/kubernetes/manifests/kube-apiserver.yaml", "apiVersion: v1\n"),
                 ("write", "/etc/kubernetes/manifests/kube-apiserver.yaml", "kind: Pod\n"),
                 ("write", "/etc/kubernetes/admin.conf", "clusters: []\n"),
                 ("ls", "/etc/kubernetes"), ("read", "/etc/kubernetes/manifests/kube-apiserver.yaml")),
     "why": {"t": "Static pod manifests", "d": "A fake /etc/kubernetes tree for a CI test."}},
    {"args": _large(),
     "why": {"t": "Large input", "d": "About 280 calls across five directories."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Tree of path segments (Optimal)",
     "description": "Each path segment is a node with a children map; one _walk(path, create) helper serves all four operations. Files keep content as appended chunks, joined on read.",
     "time": "O(L) mkdir/write, O(L + content) read, O(L + c log c) ls", "space": "O(distinct segments + content)",
     "keyPoints": ["One walk helper, optionally creating nodes", "A file lists as its own name", "Chunks make appends O(1)"]},
    {"name": "Flat dict of full paths", "slow": True,
     "description": "Store a dict from full path to content and a set of directory paths. ls scans every stored path for the prefix.",
     "time": "O(total paths) per ls", "space": "O(total path characters + content)",
     "keyPoints": ["Simple to write", "ls is a full scan"],
     "code": '''from __future__ import annotations


class FileSystem:
    def __init__(self) -> None:
        self.files: dict[str, str] = {}
        self.dirs: set[str] = {"/"}

    def _add_dirs(self, path: str) -> None:
        parts = [p for p in path.split("/") if p]
        for i in range(1, len(parts) + 1):
            self.dirs.add("/" + "/".join(parts[:i]))

    def ls(self, path: str) -> list[str]:
        if path in self.files:
            return [path.rsplit("/", 1)[1]]
        prefix = path.rstrip("/") + "/"
        names = set()
        for p in list(self.files) + list(self.dirs):
            if p != "/" and p.startswith(prefix):
                names.add(p[len(prefix):].split("/", 1)[0])
        return sorted(names)

    def mkdir(self, path: str) -> None:
        self._add_dirs(path)

    def write(self, path: str, content: str) -> None:
        self._add_dirs(path.rsplit("/", 1)[0] or "/")
        self.files[path] = self.files.get(path, "") + content

    def read(self, path: str) -> str:
        return self.files.get(path, "")
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Flat dict", "idea": "Full path -> content, plus a set of directories; ls scans by prefix.", "time": "O(total paths) per ls",
     "space": "O(paths + content)", "use": "A few files; quick to write."},
    {"name": "Trie of segments", "idea": "A node per path segment with a children map.", "time": "O(L) per call (+ sort for ls)",
     "space": "O(segments + content)", "use": "Real file systems and key stores."},
]
