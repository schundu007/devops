Source: New

# DC-REL-02 · Version Comparator

## 1. Header
| | |
|---|---|
| Chip ID | DC-REL-02 |
| Difficulty | Medium |
| Pattern | Split + two pointers |
| Track | Release & CI/CD (REL) |
| Classic pattern | LeetCode 165 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
A security advisory says `libfoo` is fixed in `3.0.13`. Your fleet image `base-ubuntu:2026.09`
ships `libfoo 3.0.2`. The in-house scanner compares versions as plain strings, decides
`"3.0.2" > "3.0.13"` and marks the image safe. The same bug makes it call cluster
version `1.27.10` older than `1.27.9`. You need a comparator that treats each part as a number.

## 3. Why This Is DevOps
**Production reality:** Release tooling compares versions all the time. Is the installed
package older than the fixed one? Is this cluster below the minimum supported version? Is
this chart an upgrade or a downgrade? Each dot-separated part must be compared as a
number, from left to right, and a missing part counts as zero. Plain string comparison sorts
`10` before `9` and silently gets these checks wrong.

**Where you see it:** vulnerability scanners such as Trivy and Grype ("installed < fixed
version"), Kubernetes version-skew checks during upgrades, Helm and Terraform version
constraints (`>= 1.5.0`), package managers resolving dependency ranges.

**Reality check:** Real ecosystems have extra rules. SemVer adds pre-release tags
(`1.0.0-rc.1` < `1.0.0`) and build metadata. Debian versions have epochs (`1:2.0`) and `~`,
which sorts before everything. RPM has its own rules. Scanners use a comparator per
ecosystem. This chip covers only the numeric dotted core that they all share.

**What breaks if you get it wrong:** The scanner reports a vulnerable image as patched. It
ships to production and stays exposed to a known CVE, and the dashboard shows green.

## 4. Problem Statement
Write `compare_versions(a, b)` for dotted version strings such as `1.27.10`.

- Split each version on `.` into parts. Every part is a non-negative integer and may have
  leading zeros (`010` means 10).
- Compare the parts from left to right as numbers. The first pair that differs decides.
- If one version has fewer parts, its missing parts count as `0`, so `1.2` equals `1.2.0`.

Return `1` if `a` is newer, `-1` if `a` is older, and `0` if they are the same release.

## 5. Input / Output format and Constraints
- `compare_versions(a: str, b: str) -> int`, returning one of `-1`, `0`, `1`.
- `1 <= len(a), len(b) <= 500`.
- Both versions contain only digits and `.`, never start or end with `.`, and have no empty parts.
- Every part fits in a 32-bit signed integer.

## 6. Examples
**Example 1**
```
compare_versions("1.27.10", "1.27.9") -> 1
```
The first two parts are equal, and 10 > 9. (A string compare would say `"1.27.10" < "1.27.9"`.)

**Example 2: missing parts (edge case)**
```
compare_versions("1.2", "1.2.0") -> 0
compare_versions("1.2", "1.2.0.0.1") -> -1
```
Missing parts count as 0, so only the final `1` makes the right side newer.

**Example 3: leading zeros**
```
compare_versions("1.01", "1.001") -> 0
```
Both second parts are the number 1.

## 7. Starter Code
See [`starter.py`](starter.py): `compare_versions(a, b)` with a docstring and type hints.

```bash
make try CHIP=04-release/DC-REL-02-version-compare
```

## 8. Hints
1. **Nudge:** Why does `"10" < "9"` as strings? What do you need to compare instead?
2. **Pattern:** Split both strings on `.`, then walk the two lists with one index, comparing
   the parts as integers.
3. **Near-solution:** Loop `i` up to the longer list's length. Read each part as
   `int(part)`, or `0` when that list has run out. Return at the first difference, and
   return `0` if none differs.

## 9. Solution
**Approach**
1. Split both versions on `.`.
2. Walk index `i` up to the longer of the two lists.
3. Read each part as an integer (this drops leading zeros), or use `0` past the end of a list.
4. At the first pair that differs, return `1` or `-1`.
5. If every pair matched, the versions are equal: return `0`.

**Brute force:** Pad both lists with zeros to the same length and compare them as tuples.
That is also O(n), but it builds extra lists. The problem is not speed but correctness:
the real mistake to avoid is comparing strings.

**Optimal code:** [`solution.py`](solution.py)

```python
def compare_versions(a: str, b: str) -> int:
    pa, pb = a.split("."), b.split(".")
    for i in range(max(len(pa), len(pb))):
        x = int(pa[i]) if i < len(pa) else 0   # int() drops leading zeros
        y = int(pb[i]) if i < len(pb) else 0   # a missing part counts as 0
        if x != y:
            return 1 if x > y else -1
    return 0
```

**Complexity**
- Time: O(len(a) + len(b)), because each character is read once by `split` and `int`.
- Space: O(len(a) + len(b)) for the split lists. A version that scans the characters with
  two pointers, without splitting, needs only O(1).

## 10. Tests
[`test_chip.py`](test_chip.py) has 6 tests: numeric vs string compare, single parts and
equality, missing parts, leading zeros, a scanner inventory (which packages are below their
fixed version), and 20,000 random pairs checked against a zero-padded tuple compare, plus a
250-part version.

## 11. Interview Talk Track
"Version checks are everywhere in release tooling. Is the installed package below the fixed
version? Is this cluster too old to upgrade directly? The classic bug is comparing strings,
which puts 1.27.10 before 1.27.9. I split both versions on dots and walk them with one
index, comparing each part as an integer. That handles leading zeros, and a missing part
counts as zero, so 1.2 equals 1.2.0. The first difference decides. It's linear in the length
of the strings, and constant space if I scan with two pointers instead of splitting. In
production I'd also ask which ecosystem it is, because SemVer pre-releases, Debian epochs and
RPM all add rules, and real scanners use one comparator per ecosystem."

## 12. Level Up
1. **"Support SemVer pre-releases: `1.0.0-rc.1 < 1.0.0`."** Split off the text after `-`. If the
   numeric cores differ, they decide. Otherwise a version *without* a pre-release is newer, and
   two pre-releases compare part by part: numeric parts as numbers, text parts as strings,
   and numbers sort before text. Build metadata after `+` is ignored.
2. **"Sort 2 million image tags by version."** Parse each tag once into a tuple of ints
   (with trailing zeros stripped, so `1.2` and `1.2.0` get the same key) and sort by that
   key. That is O(n log n) cheap tuple comparisons instead of re-splitting strings inside
   every comparison.
3. **"Check a version against a constraint like `>=1.26, <1.29`."** Parse the constraint into
   (operator, version) pairs and require every pair to hold, using this comparator. This is
   the core of Terraform `required_version` and Helm `kubeVersion` checks.

## 13. Related Chips
- **DC-NET-01 IP Address Validator**: another dotted string that is easy to parse loosely and get wrong.
- **DC-REL-01 Find the Breaking Commit**: the release step after a version check fails.
- **DC-OS-02 Common Hostname Prefix**: a left-to-right string scan with an early stop.
