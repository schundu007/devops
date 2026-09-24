Source: New

# DC-SEC-11 · Redundant Prefix Grant Cleaner

## 1. Header
| | |
|---|---|
| Chip ID | DC-SEC-11 |
| Difficulty | Medium |
| Pattern | Sort + prefix check (or trie) |
| Track | Cloud Security & IAM (SEC) |
| Classic pattern | LeetCode 1233 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
A quarterly access review flags the role `data-reader` in the fake account `111122223333`.
Its policy lists 40 object-path grants. Many are left over from tickets: the role can already
read `/acme-logs-prod/app`, yet it also has separate grants for `/acme-logs-prod/app/2026` and
`/acme-logs-prod/app/2026/09/23`. The reviewer wants the shortest list of grants that
gives exactly the same reach, so the policy is readable and fits under the size limit.

## 3. Why This Is DevOps
**Production reality:** Object-store and filesystem permissions are usually granted by path
prefix. A grant on a folder already covers everything below it, so child grants add nothing
and only make the policy longer and harder to review. Cleaning them up is a routine step in
access reviews and in "least privilege" projects. The same logic dedupes Vault policy paths,
gitignore-style include lists and backup include paths.

**Where you see it:** AWS IAM policy `Resource` ARNs with `prefix/*`, S3 bucket policies,
HashiCorp Vault policy paths, IAM Access Analyzer policy findings, GCS IAM conditions on
`resource.name.startsWith(...)`.

**Reality check:** Removing a child grant is only safe when the parent grant gives the **same
actions and the same conditions**. If `/app` allows only `s3:GetObject` and `/app/2026`
allows `s3:PutObject`, the child is not redundant. Real policies also use wildcards (`*`, `?`)
in the middle of paths, which a pure prefix check does not handle (see DC-SEC-08).

**What breaks if you get it wrong:** A plain text-prefix check treats `/logs/app` as covering
`/logs/apple`. The cleaner then deletes the `/logs/apple` grant, a pipeline loses access, and
someone "fixes" it by granting `/logs/*`, which is far wider than before.

## 4. Problem Statement
You get a list of grant paths. Each path starts with `/` and is made of segments separated by
`/`. A grant **covers** another grant if the other path begins with the first path followed by
`/`. So `/logs/app` covers `/logs/app/2026`, but not `/logs/apple` or `/logs/app-old`.

Return the grants that are **not** covered by any other grant, sorted in ascending order.
All input paths are distinct.

## 5. Input / Output format and Constraints
- `remove_covered(grants: list[str]) -> list[str]`
- `0 <= len(grants) <= 4 * 10^4`, each path is 2–100 characters.
- A path starts with `/`, has no trailing `/`, no empty segments, and uses lowercase letters,
  digits and `-`.
- Paths are distinct. Output is sorted with Python's normal string order.

## 6. Examples
**Example 1: parent and children**
```
["/logs/app", "/logs/app/2026", "/logs/app/2026/09", "/metrics"]
-> ["/logs/app", "/metrics"]
```
Both child grants sit under `/logs/app`.

**Example 2: text prefix is not a path parent (edge case)**
```
["/logs/apple", "/logs/app"]  ->  ["/logs/app", "/logs/apple"]
```
`/logs/apple` does not start with `/logs/app/`, so it stays.

**Example 3: nothing to clean**
```
[]  ->  []
```

## 7. Starter Code
See [`starter.py`](starter.py): `remove_covered(grants)` with a docstring and type hints.

```bash
make try CHIP=02-security/DC-SEC-11-redundant-grant-cleaner
```

## 8. Hints
1. **Nudge:** If you put the paths in a good order, where would a path's parent appear relative to it?
2. **Pattern:** Sort, then compare each path only with the last grant you kept. Check
   `startswith(kept + "/")`, not just `startswith(kept)`.
3. **Near-solution:** Sort by `path.split("/")`, not by raw text: `-` sorts before `/`, so raw
   text order can put `/a-b` between `/a` and `/a/c`. Keep a path only if it does not start with
   `last_kept + "/"`. A trie of segments, stopping at any node that ends a grant, also works.

## 9. Solution
**Approach**
1. Sort the paths by their list of segments. Now every parent comes right before all of its children.
2. Walk the sorted list. Skip a path if it starts with the last kept grant plus `/`.
3. Otherwise keep it. It becomes the new "last kept".
4. Return the kept grants in normal string order.

**Brute force:** For each path, check every other path to see if it is a parent. O(n² · L)
for n paths of length L: 1.6 billion comparisons at 40,000 grants.

**Optimal code:** [`solution.py`](solution.py)

```python
def remove_covered(grants: list[str]) -> list[str]:
    kept: list[str] = []
    for path in sorted(grants, key=lambda p: p.split("/")):   # segment order
        if kept and path.startswith(kept[-1] + "/"):          # covered by a parent
            continue
        kept.append(path)
    return sorted(kept)
```

**Complexity**
- Time: O(n · L · log n), because sorting compares segment lists of length up to L. The walk
  is O(n · L).
- Space: O(n · L) for the split keys and the output.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: a normal parent with children, empty and single,
the `/logs/app` vs `/logs/apple` boundary, input order, the `-` before `/` sorting trap, a
production bucket policy, and 1,500 random paths checked against an all-pairs brute force.

## 11. Interview Talk Track
"This is least-privilege cleanup: drop grants already covered by a parent path. The key idea is
ordering. If I sort paths so each parent sits right before its children, I only need to compare
each path with the last grant I kept. Two traps: a text prefix isn't a path prefix, so I check
`startswith(parent + '/')`; and raw string sort breaks when names contain a dash, because dash
sorts before slash, so I sort by the list of segments. That's O(n log n) comparisons. In a real
review I'd only merge grants with identical actions and conditions. A read grant on the parent
doesn't cover a write grant on the child."

## 12. Level Up
1. **"Grants have different actions."** Group grants by `(actions, conditions)` and run the
   cleaner inside each group. A child is redundant only if some parent's action set is a
   superset of its own. Write that check explicitly, rather than relying on grouping.
2. **"Paths contain wildcards like `/logs/*/2026`."** Prefix logic no longer works. Coverage
   between two patterns becomes a language question ("is every match of B a match of A?").
   Tools usually compare against real resource names instead of pattern against pattern (DC-SEC-08).
3. **"A million grants, re-checked on every policy change."** Keep a segment trie. Inserting a
   new grant walks its segments. If it passes a node that already ends a grant, it is covered.
   If it ends on a node with children, those children become covered. Each change costs O(L).

## 13. Related Chips
- **DC-SEC-08 IAM Wildcard Matcher**: matching with `*` and `?` instead of plain prefixes.
- **DC-NET-05 Route Prefix Trie**: the trie version of prefix lookup.
- **DC-SEC-04 Domain Suffix Compactor**: the same "covered by another entry" idea, from the other end.
