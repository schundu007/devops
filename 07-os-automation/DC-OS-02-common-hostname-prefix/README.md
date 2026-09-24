Source: New

# DC-OS-02 · Common Hostname Prefix

## 1. Header
| | |
|---|---|
| Chip ID | DC-OS-02 |
| Difficulty | Easy |
| Pattern | String scan |
| Track | OS & Automation (OS) |
| Classic pattern | LeetCode 14 |
| Premium | No |
| Time box | 15 min |
| Source | New |

## 2. The Scenario
You're writing an Ansible playbook for a hotfix that must hit exactly the hosts in a
change ticket: `us-east-prod-api-01`, `us-east-prod-api-02` and `us-east-prod-worker-02`. The
ticket gives a list, but the inventory and the log index both want a pattern. What is the longest
prefix all these hostnames share, so you can write `us-east-prod-*` and check that it doesn't
match anything else?

## 3. Why This Is DevOps
**Production reality:** Infrastructure is named by convention: region, environment, role, number.
Turning a list of hosts into a pattern is everyday work: an Ansible host pattern, a target group
filter, a Prometheus `instance=~"prefix.*"` selector, or a log index name. The longest common
prefix is the tightest pattern that still covers every host. You compare the names one character
column at a time and stop at the first disagreement.

**Where you see it:** Ansible inventory patterns (`us-east-prod-*`), PromQL regex matchers on
`instance` or `pod`, Elasticsearch index patterns (`logs-prod-*`), Kubernetes pod names that share
their ReplicaSet's prefix, S3 prefix filters.

**Reality check:** A character prefix can cut through the middle of a name segment: `eu-west-prod-kafka`
and `eu-west-prod-kube` share `eu-west-prod-k`. Real tooling usually wants a prefix that
ends on a `-` or `.` boundary. A prefix also doesn't prove a pattern is safe, because other hosts
may share it. Always check the pattern's matches against the full inventory.

**What breaks if you get it wrong:** Take a prefix that is too short (`us-east-`) and the hotfix
also hits `us-east-staging-*` hosts. Take one that is too long and you miss hosts, so the fix is
only half applied, and the incident comes back on the hosts you skipped.

## 4. Problem Statement
Given a list of hostnames, return the longest string that every hostname starts with. Return `""`
if the list is empty, or if the hostnames do not share even their first character.

## 5. Input / Output format and Constraints
- Returns a string.
- `0 <= len(hosts) <= 10^4`.
- `0 <= len(hosts[i]) <= 253` (the maximum DNS name length).
- Hostnames use lowercase letters, digits, `-` and `.`.

## 6. Examples
**Example 1: two hosts**
```
["us-east-prod-api-01", "us-east-prod-worker-02"]  ->  "us-east-prod-"
```

**Example 2: nothing shared**
```
["web-01", "api-01", "db-01"]  ->  ""
```

**Example 3: one host is a prefix of the others (edge case)**
```
["cache", "cache-01", "cache-02"]  ->  "cache"
```

## 7. Starter Code
See [`starter.py`](starter.py): the `common_prefix(hosts)` signature, docstring and type hints.
The body is TODO.

```bash
make try CHIP=07-os-automation/DC-OS-02-common-hostname-prefix
```

## 8. Hints
1. **Nudge:** The answer can't be longer than the shortest hostname.
2. **Pattern:** A vertical scan: compare column `i` across all hostnames, and stop at the first column
   where they differ or one host ends.
3. **Near-solution:** Take `first = hosts[0]`. For each index `i`, if any host is too short or has a
   different character at `i`, return `first[:i]`. If the loop finishes, return `first`.

## 9. Solution
**Approach**
1. An empty list gives `""`.
2. Walk the columns of the first hostname.
3. At each column, check every other host. On a mismatch or a short host, return the prefix so far.
4. If every column matched, the first host itself is the answer.

**Brute force:** Try every prefix of the first host, from longest to shortest, and check
`startswith` on every host. That costs O(n · m²) for n hosts of length m.

**Optimal code:** [`solution.py`](solution.py)

```python
def common_prefix(hosts):
    if not hosts:
        return ""
    first = hosts[0]
    for i, ch in enumerate(first):
        for h in hosts[1:]:
            if i == len(h) or h[i] != ch:
                return first[:i]
    return first
```

**Complexity**
- Time: O(S), where S is the total characters compared. The scan stops at the first mismatching
  column, so it never reads past the answer's length plus one column.
- Space: O(1) extra, apart from the returned string.

## 10. Tests
[`test_chip.py`](test_chip.py) has 8 cases: two hosts, nothing shared, an empty list and a single host,
one host that is a prefix of the others, an empty hostname, a production case where the prefix cuts
mid-token (`eu-west-prod-k`), 300 random lists checked against a brute force, and 10,000 hosts.

## 11. Interview Talk Track
"To turn a host list into the tightest pattern, I want the longest common prefix. I scan column
by column: take the first host, and for each position check that every other host has the same
character there. I stop at the first mismatch or the first host that runs out. That's O(total
characters), and it stops early. In practice there are two catches. A character prefix can end
halfway through a name segment, so in tooling I cut it back to the last dash or dot. And a
prefix covering my hosts can also cover others, so before running a playbook I check exactly what
the pattern matches in the inventory."

## 12. Level Up
1. **"The prefix must end on a name-segment boundary."** Split each hostname on `-` (or `.`) and
   run the same vertical scan over the segments instead of the characters. `eu-west-prod-kafka-01`
   and `eu-west-prod-kube-node-7` then give `eu-west-prod`.
2. **"10 million hostnames, and we keep asking for prefixes of different subsets."** Build a trie
   of all hostnames once. The common prefix of a subset is the path from the root down to the deepest
   node that contains all of them. For sorted input, only the first and last names in the sorted
   subset need comparing: their common prefix is everyone's.
3. **"Hosts from two regions: return the smallest set of patterns that covers exactly these hosts."**
   Group the hosts by trie branch and emit one pattern per branch where every descendant is in the
   set. Then verify every pattern against the full inventory. This is how you avoid an over-broad `*`.

## 13. Related Chips
- **DC-SEC-04 Domain Suffix Compactor**: the same idea from the other end: shared suffixes of domains.
- **DC-NET-05 Route Prefix Trie**: prefix matching with a trie for many names at once.
- **DC-SEC-11 Redundant Prefix Grant Cleaner**: when one path prefix already covers another.
