Source: New

# DC-SEC-01 · Path Traversal Guard

## 1. Header
| | |
|---|---|
| Chip ID | DC-SEC-01 |
| Difficulty | Medium |
| Pattern | Stack |
| Track | Cloud Security & IAM (SEC) |
| Classic pattern | LeetCode 71 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
A security review of `assets-svc` (running on 10.0.4.12) finds a handler for
`GET /static/<name>` that serves files from `/var/www/static`. The WAF log shows
requests like `name=css/../../../../root/.ssh/id_rsa` and `name=..//..//..//proc/self/environ`.
Your job: turn every requested name into one canonical path and refuse anything that lands
outside `/var/www/static`, before the handler opens a file.

## 3. Why This Is DevOps
**Production reality:** Web servers, artifact stores and upload handlers map user input to
files on disk. An attacker adds `../` segments to climb out of the allowed directory and
read secrets such as `/etc/passwd`, SSH keys or `/proc/self/environ`. The fix is to
normalize the path first (drop `.`, apply `..`, squash `//`) and only then compare it with
the allowed root. Normalizing is a stack walk over the path segments.

**Where you see it:** nginx and Envoy path normalization (Envoy has a `normalize_path`
setting on its HTTP connection manager), Go's `path.Clean` and `filepath.Clean`, Python's
`posixpath.normpath`, and the Zip Slip checks in archive extractors.

**Reality check:** Cleaning the text is not enough in production. A symlink inside the root
can point anywhere, so real code calls `os.path.realpath` (resolving links) and then checks
the prefix, or opens files relative to a directory handle (`openat` with `O_NOFOLLOW`-style
flags). Input also has to be URL-decoded exactly once *before* this check, or
`%2e%2e%2f` slips through.

**What breaks if you get it wrong:** A plain `startswith("/srv/app")` check lets
`/srv/app2/secret.env` through, and skipping normalization lets `../../etc/passwd` through.
Either way, an unauthenticated request reads credentials straight off the host.

## 4. Problem Statement
Write two functions.

`normalize_path(path)` turns a Unix-style path into its canonical absolute form:
- Split on `/`. Empty segments (from `//`) and `.` add nothing.
- `..` removes the most recent name. At the top (`/`) there is nothing to remove, so it stays at `/`.
- Every other segment is a name, even `...`.
- The result starts with `/`, has single slashes, and no trailing slash (except the root itself).

`is_within_root(root, requested)` decides whether a request stays inside `root`:
- If `requested` starts with `/`, it is absolute. Otherwise it is relative to `root`.
- Normalize both, then return `True` only if the target equals the root or sits under it by
  whole segments (`/srv/app2` is **not** under `/srv/app`).

## 5. Input / Output format and Constraints
- `normalize_path(path: str) -> str`, `is_within_root(root: str, requested: str) -> bool`.
- `0 <= len(path) <= 3 * 10^5`. Characters are letters, digits, `.`, `_`, `-` and `/`.
- `root` is absolute. An empty `path` means `/`.
- The check is on text only. No file system access.

## 6. Examples
**Example 1: climbing out**
```
normalize_path("/srv/app/../../etc/passwd")          -> "/etc/passwd"
is_within_root("/srv/app/uploads", "../../../etc/passwd") -> False
```

**Example 2: wandering but staying inside**
```
normalize_path("/srv//app/./config/")                -> "/srv/app/config"
is_within_root("/srv/app/uploads", "a/b/../../c.txt") -> True   # ends at /srv/app/uploads/c.txt
```

**Example 3: prefix trap (edge case)**
```
is_within_root("/srv/app", "/srv/app2/secret.env")   -> False  # shares text, not a segment
normalize_path("/../../..")                          -> "/"    # cannot go above root
```

## 7. Starter Code
See [`starter.py`](starter.py): `normalize_path` and `is_within_root` with docstrings and
type hints. Bodies are TODO.

```bash
make try CHIP=02-security/DC-SEC-01-path-traversal-guard
```

## 8. Hints
1. **Nudge:** Work segment by segment, not character by character. What does `..` do to the path you have built so far?
2. **Pattern:** The names you have kept form a stack: a name pushes, `..` pops, `.` and empty segments do nothing.
3. **Near-solution:** `for part in path.split("/")`: skip `""` and `"."`, pop on `".."` if the stack is not empty,
   else push. Return `"/" + "/".join(stack)`. For the guard, check `target == base or target.startswith(base + "/")`.

## 9. Solution
**Approach**
1. Split the path on `/`.
2. Walk the segments with a stack: skip empty and `.`, pop on `..` (unless empty), push names.
3. Join the stack with `/` and add a leading `/`.
4. For the guard, join a relative request onto the root, normalize both, and compare whole segments.

**Brute force:** Repeatedly search the string for `/./`, `//` and `/name/../` and rewrite it
until nothing changes. Each pass is O(n) and a path of many `x/..` pairs needs O(n) passes: O(n²).

**Optimal code:** [`solution.py`](solution.py)

```python
def normalize_path(path: str) -> str:
    stack: list[str] = []
    for part in path.split("/"):
        if part == "" or part == ".":
            continue                  # "//" and "/./" add nothing
        if part == "..":
            if stack:
                stack.pop()           # up one level; at "/" nowhere to go
            continue
        stack.append(part)
    return "/" + "/".join(stack)


def is_within_root(root: str, requested: str) -> bool:
    base = normalize_path(root)
    target = normalize_path(requested if requested.startswith("/") else base + "/" + requested)
    if base == "/":
        return True
    return target == base or target.startswith(base + "/")   # whole segments only
```

**Complexity**
- Time: O(n): each segment is pushed and popped at most once, and split and join are linear.
- Space: O(n): the stack and the output hold at most every segment.

## 10. Tests
[`test_chip.py`](test_chip.py) has 10 cases: five normal normalizations, an empty path and
root, traversal attempts, the `/srv/app2` segment boundary, a production static-file handler
with four real-world attack strings, and a large-input check (3,000 random paths against
`posixpath.normpath`, plus a 100,000-segment path).

## 11. Interview Talk Track
"Path traversal is an attacker adding `../` to escape the directory a handler is allowed to
read. The defence is to canonicalize first and compare second. I split the path on slashes
and walk it with a stack: names push, `..` pops, and `.` or empty segments do nothing. That's
O(n). Then I join the request onto the root, normalize, and check that the result equals the
root or starts with the root plus a slash. The trailing slash matters, because a plain
prefix check lets `/srv/app2` pass for `/srv/app`. In production I'd go further: URL-decode
exactly once before this, then call `realpath` so symlinks are resolved, and check the prefix
again. Text cleaning alone doesn't stop a symlink that points to `/etc`."

## 12. Level Up
1. **"The file system has symlinks."** Resolve the real path (`os.path.realpath`) after
   joining, then do the segment check on that. Better still, open relative to a directory
   file descriptor and refuse to follow links, so a link swapped in between check and open
   (a time-of-check to time-of-use race) cannot win.
2. **"Requests arrive URL-encoded, and on Windows hosts too."** Decode exactly once, then
   reject any `%` left over, NUL bytes and backslashes, before normalizing. Double decoding
   is how `%252e%252e` becomes `..` after the check. On Windows, also treat `\` and drive letters as separators.
3. **"The same guard for tar and zip extraction."** Every entry name goes through
   `is_within_root(dest, name)` before it is written. That blocks "Zip Slip", where an archive
   entry named `../../etc/cron.d/x` writes outside the target directory.

## 13. Related Chips
- **DC-SEC-02 Config Bracket Validator**: the same push and pop stack, on brackets.
- **DC-OS-01 In-Memory File System**: the directory tree these paths walk.
- **DC-SEC-11 Redundant Prefix Grant Cleaner**: segment-aware prefix checks on S3 paths.
