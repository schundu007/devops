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

VARIANT_TITLE = "mkdir, write, read, ls"
VARIANT_APPROACH = "Tree of path segments · O(L) per call (+ sort for ls) · O(segments + content)"

_DU_FAST = '''from __future__ import annotations


class _Node:
    __slots__ = ("children", "size", "total", "is_file")

    def __init__(self) -> None:
        self.children: dict[str, _Node] = {}
        self.size = 0
        self.total = 0
        self.is_file = False


class DiskUsage:
    def __init__(self) -> None:
        self._root = _Node()

    @staticmethod
    def _parts(path: str) -> list[str]:
        return [p for p in path.split("/") if p]

    def write(self, path: str, size: int) -> None:
        trail = [self._root]
        node = self._root
        for part in self._parts(path):
            node = node.children.setdefault(part, _Node())
            trail.append(node)
        delta = size - node.size
        node.size = size
        node.is_file = True
        for n in trail:
            n.total += delta

    def du(self, path: str) -> int:
        node = self._root
        for part in self._parts(path):
            node = node.children.get(part)
            if node is None:
                return 0
        return node.total

    def rm(self, path: str) -> None:
        parts = self._parts(path)
        trail = [self._root]
        node = self._root
        for part in parts[:-1]:
            node = node.children.get(part)
            if node is None:
                return
            trail.append(node)
        child = node.children.pop(parts[-1], None)
        if child is None:
            return
        for n in trail:
            n.total -= child.total
'''

_DU_SLOW = '''from __future__ import annotations


class DiskUsage:
    def __init__(self) -> None:
        self.files: dict[str, int] = {}

    @staticmethod
    def _under(p: str, path: str) -> bool:
        return path == "/" or p == path or p.startswith(path + "/")

    def write(self, path: str, size: int) -> None:
        self.files[path] = size

    def du(self, path: str) -> int:
        return sum(s for p, s in self.files.items() if self._under(p, path))

    def rm(self, path: str) -> None:
        for p in [p for p in self.files if self._under(p, path)]:
            del self.files[p]
'''

_MOUNT_FAST = '''from __future__ import annotations


def resolve_mounts(mounts: list[str], paths: list[str]) -> list[str]:
    root: dict = {}
    END = "\\0"
    for m in mounts:
        node = root
        for part in [p for p in m.split("/") if p]:
            node = node.setdefault(part, {})
        node[END] = m
    out = []
    for path in paths:
        node = root
        best = node.get(END, "")
        for part in [p for p in path.split("/") if p]:
            node = node.get(part)
            if node is None:
                break
            best = node.get(END, best)
        out.append(best)
    return out
'''

_MOUNT_SLOW = '''from __future__ import annotations


def resolve_mounts(mounts: list[str], paths: list[str]) -> list[str]:
    out = []
    for path in paths:
        best = ""
        for m in mounts:
            if m == "/" or path == m or path.startswith(m + "/"):
                if len(m) > len(best):
                    best = m
        out.append(best)
    return out
'''


def _dops(*calls):
    return {"ops": ["DiskUsage"] + [c[0] for c in calls], "vals": [[]] + [list(c[1:]) for c in calls]}


def _du_large():
    rng = random.Random(1101)
    dirs = ["/var/log/nginx", "/var/log/app", "/var/lib/docker", "/home/ci", "/tmp"]
    calls = []
    for i in range(250):
        r = rng.random()
        d = rng.choice(dirs)
        if r < 0.6:
            calls.append(("write", f"{d}/f{rng.randrange(15)}", rng.randint(0, 5000)))
        elif r < 0.9:
            calls.append(("du", rng.choice(dirs + ["/", "/var", "/var/log"])))
        else:
            calls.append(("rm", f"{d}/f{rng.randrange(15)}" if rng.random() < 0.8 else d))
    return _dops(*calls)


def _mount_large():
    rng = random.Random(1102)
    segs = ["srv", "data", "db", "logs", "app", "cache", "k8s", "pods"]
    mounts = sorted({"/" + "/".join(rng.choice(segs) for _ in range(rng.randint(1, 3))) for _ in range(25)})
    paths = ["/" + "/".join(rng.choice(segs) for _ in range(rng.randint(1, 5))) for _ in range(150)]
    return {"mounts": mounts, "paths": paths}


VARIANTS = [
    {
        "key": "disk-usage",
        "title": "du with cached subtree totals",
        "approach": "Segment tree with a running total per node · O(L) per call · O(segments)",
        "spec": {"kind": "design", "fn": "DiskUsage", "params": []},
        "statement": (
            "A node agent needs `du` answers on every scrape, so walking the whole tree each time is too slow. Build `DiskUsage`.\n"
            "\n"
            "### Methods\n"
            "- `write(path, size)`: create the file (and missing parents), or **overwrite** its size\n"
            "- `du(path)`: total bytes of the file, or of every file under the directory; `0` if the path does not exist\n"
            "- `rm(path)`: delete the file or the whole directory subtree; nothing happens if it does not exist\n"
            "\n"
            "### Rules\n"
            "- Paths are absolute\n"
            "- A path is never used as both a file and a directory\n"
            "- `rm` is never called on `/`"
        ),
        "examples": [
            {"args": _dops(("write", "/var/log/app.log", 300), ("write", "/var/log/old.log", 700), ("write", "/var/lib/db", 50),
                           ("du", "/var/log"), ("du", "/"), ("rm", "/var/log"), ("du", "/var")),
             "explanation": "/var/log holds 1,000 bytes and the whole disk 1,050. After removing /var/log only /var/lib/db is left.",
             "why": {"t": "Totals roll up", "d": "Every ancestor sees each write and each removal."}},
        ],
        "constraints": ["0 ≤ calls ≤ 300", "1 ≤ path depth ≤ 6", "0 ≤ size ≤ 10⁹"],
        "hints": [
            "Keep a `total` on every node: the sum of all file sizes below it.",
            "On write, the change is `size - old_size`; add it to every node on the path, root included.",
            "On rm, detach the child from its parent and subtract the child's total from every ancestor.",
        ],
        "tests": [
            {"args": _dops(("du", "/")), "why": {"t": "Empty disk", "d": "Nothing written yet."}},
            {"args": _dops(("write", "/a", 10), ("write", "/a", 4), ("du", "/"), ("du", "/a")),
             "why": {"t": "Overwrite", "d": "A second write replaces the size; it does not add to it."}},
            {"args": _dops(("write", "/a/b", 5), ("du", "/a/c"), ("du", "/x"), ("rm", "/x/y"), ("du", "/")),
             "why": {"t": "Missing paths", "d": "du of a missing path is 0 and rm of one changes nothing."}},
            {"args": _dops(("write", "/data/x", 1), ("write", "/database/y", 2), ("du", "/data")),
             "why": {"t": "Prefix, not a parent", "d": "/database is not inside /data."}},
            {"args": _dops(("write", "/a/b/c", 7), ("rm", "/a/b/c"), ("du", "/a"), ("write", "/a/b/c", 9), ("du", "/")),
             "why": {"t": "Remove then recreate", "d": "A deleted file can be written again."}},
            {"args": _dops(("write", "/z", 0), ("du", "/z"), ("du", "/")), "why": {"t": "Zero-byte file", "d": "An empty file adds nothing."}},
            {"args": _du_large(), "why": {"t": "Larger input", "d": "250 writes, du calls and removals across five directories."}},
        ],
        "solutions": [
            {"name": "Tree with cached totals (Optimal)",
             "description": "Each path segment is a node holding the total size below it. Writes and removals push the change up the path they walked; du just reads the node's total.",
             "time": "O(L) per call", "space": "O(distinct segments)",
             "keyPoints": ["Remember the nodes you walked", "Overwrite applies a delta, not the new size", "rm subtracts the removed subtree's total"],
             "code": _DU_FAST},
            {"name": "Flat dict and prefix scan", "slow": True,
             "description": "Store full path to size. du sums every path equal to or under the prefix; rm deletes them.",
             "time": "O(files) per du and rm", "space": "O(files)",
             "keyPoints": ["Match on path + '/' so /data does not match /database", "Every du scans all files"],
             "code": _DU_SLOW},
        ],
        "starter": "class DiskUsage:\n    def __init__(self) -> None:\n        pass\n\n    def write(self, path: str, size: int) -> None:\n        pass\n\n    def du(self, path: str) -> int:\n        pass\n\n    def rm(self, path: str) -> None:\n        pass\n",
    },
    {
        "key": "mount-table",
        "title": "Which mount serves this path?",
        "approach": "Trie of mount segments, keep the deepest match · O(total segments) · O(mount segments)",
        "spec": {"kind": "fn", "fn": "resolve_mounts", "params": ["mounts", "paths"]},
        "statement": (
            "The kernel sends each file access to the **deepest mount point** that contains it, the same way an ingress picks the longest path prefix. Find the mount that serves each path.\n"
            "\n"
            "### Input\n"
            "- `mounts`: the mount table\n"
            "- `paths`: the paths to resolve\n"
            "\n"
            "### Output\n"
            "- For each path, in order, the mount that serves it, or `\"\"` if no mount contains it\n"
            "\n"
            "### Rules\n"
            "- A mount contains a path when it is the path itself or an ancestor directory of it, on **whole segments** (`/data` does not contain `/database`)\n"
            "- `/` contains every path\n"
            "- Paths and mounts are absolute, with no trailing slash (except `/`) and no empty segments"
        ),
        "examples": [
            {"args": {"mounts": ["/", "/var", "/var/lib/docker"], "paths": ["/var/lib/docker/overlay2", "/var/log/syslog", "/etc/hosts"]},
             "explanation": "The docker volume is the deepest mount for the first path, /var for the second and / for the third.",
             "why": {"t": "Deepest wins", "d": "Nested mounts shadow their parents."}},
            {"args": {"mounts": ["/data"], "paths": ["/database/x", "/data"]},
             "explanation": "/database only shares characters with /data; the mount point itself is served by its own mount.",
             "why": {"t": "Whole segments", "d": "A string prefix is not a directory prefix."}},
        ],
        "constraints": ["0 ≤ mounts.length ≤ 100", "0 ≤ paths.length ≤ 200", "1 ≤ path depth ≤ 8", "mounts are unique"],
        "hints": [
            "Split every mount into segments and insert it into a trie, marking the node where it ends.",
            "Walk each path through the trie segment by segment, remembering the last marked node you passed.",
            "Start from the root's mark so `/` is used when nothing deeper matches.",
        ],
        "tests": [
            {"args": {"mounts": [], "paths": ["/a"]}, "why": {"t": "No mounts", "d": "Nothing serves the path."}},
            {"args": {"mounts": ["/"], "paths": []}, "why": {"t": "No paths", "d": "Nothing to resolve."}},
            {"args": {"mounts": ["/"], "paths": ["/", "/a/b"]}, "why": {"t": "Root only", "d": "/ serves every path, including itself."}},
            {"args": {"mounts": ["/a/b/c"], "paths": ["/a/b", "/a/b/c", "/a/b/c/d/e"]},
             "why": {"t": "Above the mount", "d": "A path above the only mount is not served."}},
            {"args": {"mounts": ["/srv", "/srv/app", "/srv/app/cache"], "paths": ["/srv/app/cachex", "/srv/app/cache/x", "/srv/ap"]},
             "why": {"t": "Near misses", "d": "Segments that only start the same way do not match."}},
            {"args": {"mounts": ["/mnt/nfs", "/mnt"], "paths": ["/mnt/nfs/share", "/mnt/usb"]},
             "why": {"t": "Order does not matter", "d": "The deeper mount wins even when listed first."}},
            {"args": _mount_large(), "why": {"t": "Larger input", "d": "About 25 mounts and 150 paths."}},
        ],
        "solutions": [
            {"name": "Trie of mount segments (Optimal)",
             "description": "Insert each mount's segments into a trie and mark its end. Walk each path down the trie and keep the last mark seen.",
             "time": "O(total segments of mounts and paths)", "space": "O(mount segments)",
             "keyPoints": ["Segments, not characters, so /data never matches /database", "The root mark covers /", "Stop at the first missing segment"],
             "code": _MOUNT_FAST},
            {"name": "Check every mount per path", "slow": True,
             "description": "For each path, test every mount with a segment-aware prefix check and keep the longest one that matches.",
             "time": "O(P · M · L)", "space": "O(1) extra",
             "keyPoints": ["Compare with mount + '/'", "Longest matching mount is the deepest"],
             "code": _MOUNT_SLOW},
        ],
        "starter": "def resolve_mounts(mounts: list[str], paths: list[str]) -> list[str]:\n    pass\n",
    },
]
