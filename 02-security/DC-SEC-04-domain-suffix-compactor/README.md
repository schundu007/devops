Source: New

# DC-SEC-04 · Domain Suffix Compactor

## 1. Header
| | |
|---|---|
| Chip ID | DC-SEC-04 |
| Difficulty | Medium |
| Pattern | Reverse trie |
| Track | Cloud Security & IAM (SEC) |
| Classic pattern | LeetCode 820 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
The `payments` namespace sends all outbound traffic through an egress proxy with an
allow-list of hostnames: `hooks.slack.com`, `slack.com`, `api.stripe.com`, `stripe.com`,
`sts.us-east-1.amazonaws.com`, `us-east-1.amazonaws.com` and so on. The list is pushed to
every proxy replica in a small config blob that has a size limit. Many names end the same way,
so you want to store each shared ending once: a name that is a whole-label suffix of another
name can be written as a pointer into that longer name.

## 3. Why This Is DevOps
**Production reality:** Hostnames share endings: `api.prod.example.com`, `prod.example.com`
and `example.com` all end in `example.com`. DNS itself saves space this way. In a DNS message,
a repeated name suffix is replaced with a pointer to where it already appeared. Domain
allow-lists and blocklists with thousands of entries use a similar idea: a trie keyed on labels
from right to left (`com` → `example` → `prod` → `api`), so shared endings are stored once and a
lookup walks from the top-level domain inward.

**Where you see it:** DNS message compression (RFC 1035, section 4.1.4), Squid's `dstdomain`
ACL (where `.example.com` matches the domain and every subdomain), DNS blocklist resolvers, and
the domain matching in egress proxies.

**Reality check:** The classic problem compares suffixes character by character. This chip
compares whole labels, because `ample.com` is a different domain from `example.com`, and DNS
compression also works on labels. Compaction is about storage only: a real allow-list must still
mark which trie nodes are real entries. Otherwise, storing `api.prod.example.com` would quietly
allow `prod.example.com` too.

**What breaks if you get it wrong:** A character-level match treats `evil-example.com` or
`ample.com` as part of `example.com`. In a matcher, the same mistake lets an attacker register
`notexample.com` and pass an allow-list check that uses `endswith("example.com")`.

## 4. Problem Statement
Write `compact(hostnames)` and `encoded_length(hostnames)`.

- First clean each name: lowercase it and remove a trailing dot. Ignore empty names and duplicates.
- Name `A` is **covered** if some other name `B` ends with `"." + A`. For example, `prod.example.com`
  is covered by `api.prod.example.com`, but `ample.com` is not covered by `example.com`.
- `compact` returns the names that are not covered, sorted alphabetically.
- `encoded_length` returns the length of a single string that stores every kept name, each
  followed by one `#`. Covered names can point into that string, so they cost nothing extra.

## 5. Input / Output format and Constraints
- `compact(hostnames: list[str]) -> list[str]`, `encoded_length(hostnames: list[str]) -> int`.
- `0 <= len(hostnames) <= 5 * 10^4`. Each name has at most 253 characters.
- Labels contain letters, digits and `-`, separated by `.`.

## 6. Examples
**Example 1: shared endings collapse**
```
compact(["api.prod.example.com", "prod.example.com", "example.com", "cdn.example.net"])
  -> ["api.prod.example.com", "cdn.example.net"]
encoded_length(same) -> 37      # "api.prod.example.com#cdn.example.net#"
```

**Example 2: whole labels only (edge case)**
```
compact(["example.com", "ample.com"]) -> ["ample.com", "example.com"]
```

**Example 3: cleaning**
```
compact(["API.Example.COM.", "api.example.com", "example.com.", ""]) -> ["api.example.com"]
compact([]) -> []        encoded_length([]) -> 0
```

## 7. Starter Code
See [`starter.py`](starter.py): `compact` and `encoded_length` with docstrings and type hints.
Bodies are TODO.

```bash
make try CHIP=02-security/DC-SEC-04-domain-suffix-compactor
```

## 8. Hints
1. **Nudge:** Two names share an ending. Which end of the name should you start comparing from?
2. **Pattern:** A trie built on reversed labels (`com`, then `example`, then `prod`). A covered name
   is one whose path continues further into the trie.
3. **Near-solution:** Insert every cleaned, distinct name as `reversed(name.split("."))`. Remember
   each name's final node. Keep the names whose final node has no children, then sort them.

## 9. Solution
**Approach**
1. Clean the names (lowercase, strip the trailing dot) and remove empties and duplicates.
2. Insert each name into a trie, one label at a time from the right.
3. A name whose final node has children is a label-suffix of a longer name, so it is covered.
4. Return the uncovered names, sorted. The encoded length is the sum of `len(name) + 1` over them.

**Brute force:** For each name, check every other name with `endswith("." + name)`. That is
O(n² × L), too slow for tens of thousands of names.

**Optimal code:** [`solution.py`](solution.py)

```python
def _normalize(host: str) -> str:
    return host.lower().rstrip(".")          # DNS is case-insensitive; trailing dot = root


def compact(hostnames: list[str]) -> list[str]:
    names = sorted({_normalize(h) for h in hostnames if _normalize(h)})
    root: dict[str, dict] = {}
    ends: list[tuple[str, dict]] = []
    for name in names:
        node = root
        for label in reversed(name.split(".")):   # com -> example -> prod -> api
            node = node.setdefault(label, {})
        ends.append((name, node))
    return [name for name, node in ends if not node]   # children => covered


def encoded_length(hostnames: list[str]) -> int:
    return sum(len(name) + 1 for name in compact(hostnames))
```

**Complexity**
- Time: O(total characters + n log n): each label is inserted once, plus sorting the output.
- Space: O(total characters): one trie node per distinct label path.

## 10. Tests
[`test_chip.py`](test_chip.py) has 6 cases: normal suffix collapse, empty and single input,
the `ample.com` label boundary, case, trailing dots and duplicates, a production egress
allow-list, and a large random check (200 random lists against an independent O(n²) reference,
plus 20,050 cluster DNS names).

## 11. Interview Talk Track
"Hostnames share endings, so I store them in a trie keyed from the right: `com`, then
`example`, then `prod`. Any name whose trie path keeps going is a suffix of a longer name, so
it can be a pointer into that longer name instead of its own copy. DNS does exactly this with
message compression. Building the trie is linear in the total characters. The point I'd raise
in a security review is labels versus characters: `endswith('example.com')` also matches
`notexample.com`, which is a real allow-list bypass. So I compare whole labels. And the trie has
to mark which nodes are real entries, or compacting the storage silently widens the policy."

## 12. Level Up
1. **"Use this as the allow-list matcher, with wildcards like `*.example.com`."** Keep a flag on
   each node: exact entry, or wildcard for everything below. A lookup walks the request's labels
   from the right and stops at the first wildcard flag or the exact end. The cost depends on the
   number of labels, not the list size.
2. **"The list has 5 million blocked domains (a threat-intel feed)."** A dict-per-node trie in
   Python is too big. Intern the labels (store each distinct label once and use integer IDs),
   or build a compact, sorted array of reversed names and binary search it. Resolvers that block
   domains commonly use hashed sets or succinct tries at this size.
3. **"Internationalized names."** Convert to punycode (IDNA) before inserting, so `münchen.de`
   and `xn--mnchen-3ya.de` are the same key. Also watch for look-alike characters (homoglyphs),
   which is a separate check.

## 13. Related Chips
- **DC-SEC-17 Streaming Secret Scanner**: another reverse trie, matching as characters arrive.
- **DC-NET-05 Route Prefix Trie**: the forward version, used for path and prefix routing.
- **DC-SEC-11 Redundant Prefix Grant Cleaner**: removing entries covered by a parent (the prefix mirror of this chip).
