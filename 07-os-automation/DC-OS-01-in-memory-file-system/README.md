Source: New

# DC-OS-01 · In-Memory File System

## 1. Header
| | |
|---|---|
| Chip ID | DC-OS-01 |
| Difficulty | Hard |
| Pattern | Directory tree design |
| Track | OS & Automation (OS) |
| Classic pattern | LeetCode 588 |
| Premium | Yes (P). Free alternative: LeetCode 208 Implement Trie (Prefix Tree), which uses the same "node with a map of children" structure, keyed by characters instead of path segments. |
| Time box | 40 min |
| Source | New |

## 2. The Scenario
Your team's deployment tool writes config files, and its unit tests currently touch the real
disk: they are slow, flaky in CI, and they leave junk in `/tmp`. You're asked to build a small
in-memory filesystem the tool can use in tests: `mkdir`, `ls`, `write` (append) and `read`. The
first test mounts a fake ConfigMap at `/etc/config` with `app.yaml` and `feature-flags.json`, and
a sidecar appends lines to `/var/log/app/sidecar.log`.

## 3. Why This Is DevOps
**Production reality:** Paths are trees: every `/` goes one level down. A filesystem, a key
store with folder-style keys, and a config tree all store a node per path segment, each with a
map of children. Fake in-memory filesystems make infrastructure code testable without real disks.
The same tree structure also describes how hierarchical key-value stores are browsed and listed by
prefix.

**Where you see it:** in-memory filesystems for tests (Go's `testing/fstest.MapFS`, `pyfakefs`
for Python), Kubernetes ConfigMap and Secret volumes (each key appears as a file in the mounted
directory), Consul KV's folder-style keys, etcd key prefixes (etcd v3 stores a flat, ordered key
space, and folders are only a naming convention: a similar idea).

**Reality check:** Real filesystems add permissions, inodes, hard links, file handles, and atomic
rename. Kubernetes updates ConfigMap volumes through an atomic symlink swap. etcd has no real
directories: it lists by key range. This chip is the simplest tree: names, directories and appendable content.

**What breaks if you get it wrong:** Return `ls` results in insertion order instead of sorted order,
and a test that renders "all files in the config dir" passes on your laptop but fails in CI. Or treat
a file path as a directory, and a template writes `app.yaml/` as a folder, which the pod can't read.

## 4. Problem Statement
Design `FileSystem` with four operations. All paths are absolute, like `/a/b/c`, and `/` is the root.

- `ls(path)`: if `path` is a file, return a list containing only its name. If it is a directory,
  return the names of its direct children (files and directories), sorted in plain string order.
- `mkdir(path)`: create the directory. Create any missing parent directories too.
- `write(path, content)`: append `content` to the file. If the file does not exist, create it first,
  along with any missing parent directories.
- `read(path)`: return the file's full content.

## 5. Input / Output format and Constraints
- `ls -> list[str]`, `read -> str`, and `mkdir` and `write` return `None`.
- Names use letters, digits, `.`, `-` and `_`, 1–100 characters each. Paths are well-formed.
- A path is never used as both a file and a directory. `read` and `ls` are only called on paths that exist.
- Up to `3 * 10^4` calls in total, and total content up to `10^6` characters.

## 6. Examples
**Example 1: build and list**
```
mkdir("/a/b/c")
ls("/")      -> ["a"]
ls("/a/b")   -> ["c"]
```

**Example 2: append and read**
```
write("/a/b/c/d", "hello")
write("/a/b/c/d", " world")
read("/a/b/c/d")  -> "hello world"
ls("/a/b/c/d")    -> ["d"]          # a file lists as its own name
```

**Example 3: empty root (edge case)**
```
ls("/") -> []
```

## 7. Starter Code
See [`starter.py`](starter.py): the `FileSystem` class with `ls`, `mkdir`, `write` and `read`
signatures, docstrings and type hints. Bodies are TODO.

```bash
make try CHIP=07-os-automation/DC-OS-01-in-memory-file-system
```

## 8. Hints
1. **Nudge:** Split the path on `/`. What does each piece correspond to?
2. **Pattern:** A tree (a trie keyed by path segments). Each node has `children: dict[name, node]`,
   plus a flag and content if it is a file.
3. **Near-solution:** Write a `_walk(path, create)` helper that follows the segments from the
   root, creating missing nodes if asked. `mkdir` is a walk with `create=True`. `write` walks, marks
   the node as a file and appends. `ls` walks: return `[name]` for a file, or `sorted(children)` for a directory.

## 9. Solution
**Approach**
1. Represent each path segment as a node with a `children` map. The root is `/`.
2. One helper, `_walk(path, create)`, turns a path into a node, optionally creating missing nodes.
   All four operations use it.
3. Files are nodes with `is_file = True`. Content is kept as a list of chunks, so appends are O(1),
   and it is joined on read.
4. `ls` sorts the children at call time. `sorted()` on a dict's keys gives plain string order.

**Brute force:** Store a flat dict from full path to content, plus a set of directory paths. `ls`
then scans every stored path for the prefix, which is O(total paths) per call. The tests use this
as the reference.

**Optimal code:** [`solution.py`](solution.py)

```python
class _Node:
    __slots__ = ("children", "is_file", "content")

    def __init__(self):
        self.children = {}
        self.is_file = False
        self.content = []


class FileSystem:
    def __init__(self):
        self._root = _Node()

    @staticmethod
    def _parts(path):
        return [p for p in path.split("/") if p]

    def _walk(self, path, create):
        node = self._root
        for part in self._parts(path):
            nxt = node.children.get(part)
            if nxt is None:
                if not create:
                    return None
                nxt = node.children[part] = _Node()
            node = nxt
        return node

    def ls(self, path):
        node = self._walk(path, create=False)
        if node is None:
            return []
        if node.is_file:
            return [self._parts(path)[-1]]
        return sorted(node.children)

    def mkdir(self, path):
        self._walk(path, create=True)

    def write(self, path, content):
        node = self._walk(path, create=True)
        node.is_file = True
        node.content.append(content)

    def read(self, path):
        node = self._walk(path, create=False)
        return "".join(node.content) if node is not None and node.is_file else ""
```

**Complexity** (L = path length in characters, c = number of children listed)
- Time: `mkdir` and `write` are O(L), because the walk touches each segment once and the append is
  O(1). `read` is O(L + content size). `ls` is O(L + c log c), because of the sort.
- Space: O(total distinct path segments + total content).

## 10. Tests
[`test_chip.py`](test_chip.py) has 8 cases: an empty root, `mkdir` creating parents, append and
read, `ls` on a file, sorted listing that mixes files and directories (with uppercase names), the
ConfigMap and sidecar-log scenario, 3,000 random operations checked against a flat
path-dict reference, and a 2,000-file tree.

## 11. Interview Talk Track
"Paths are trees, so I model the filesystem as a trie keyed by path segments. Each node has a
map of children, and file nodes also hold content. Everything goes through one walk helper that
splits the path and follows or creates nodes. That keeps mkdir, write, read and ls simple, each
O(path length), plus a sort for ls. I store content as a list of chunks, so appends don't copy
the whole file each time. The reason this matters in DevOps: in-memory filesystems like
`fstest.MapFS` or `pyfakefs` make config-generation code testable without touching disk, and
ConfigMap volumes and folder-style key stores are the same tree idea. Real systems add
permissions and atomic updates. Kubernetes swaps ConfigMap contents with an atomic symlink change."

## 12. Level Up
1. **"`ls` is called 1,000 times more often than `mkdir`."** Keep each node's children in a sorted
   structure: sort once when the children change, cache the sorted list, and clear the cache when a
   child is added. `ls` becomes O(L + c) with no re-sort.
2. **"Add `rm -r` and `mv`."** `rm -r` removes a child entry, and the subtree is freed. `mv` is
   detach-and-attach: remove the child from the old parent and insert it under the new name, O(L),
   without copying the subtree. That is why `mv` within one real filesystem is fast.
3. **"Several threads write at once."** Use one lock per file for appends, and a lock per directory
   for creating children. Always lock parents before children so the lock order is fixed and there
   is no deadlock (DC-PLAT-14). Or copy-on-write the path from the root, which is roughly how some
   real systems publish atomic snapshots.

## 13. Related Chips
- **DC-NET-05 Route Prefix Trie**: the same trie, keyed by characters or path segments, for routing.
- **DC-SEC-11 Redundant Prefix Grant Cleaner**: prefix relationships between storage paths.
- **DC-SEC-01 Path Traversal Guard**: normalising paths before walking the tree.
