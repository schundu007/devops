Source: New

# DC-SEC-12 · Blast Radius of a Leaked Credential ★

## 1. Header
| | |
|---|---|
| Chip ID | DC-SEC-12 |
| Difficulty | Medium |
| Start here | ★ |
| Pattern | Graph DFS/BFS |
| Track | Cloud Security & IAM (SEC) |
| Classic pattern | LeetCode 841 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
At 09:40 a secret scanner finds `ci-deploy-token` pasted in a public gist. The token can
start a shell on the build VM `ip-10-0-8-21`. That VM has an instance role that can read the
bucket `acme-artifacts-prod`, and a forgotten `.env` file in that bucket holds the
`orders-db` password. Before you rotate anything, the incident lead asks: "What can an
attacker reach from this one token?"

## 3. Why This Is DevOps
**Production reality:** In a cloud account, resources hold credentials to other resources: a
VM has a role, a bucket stores a key, a CI job has a deploy token, a Kubernetes service
account can read secrets. That forms a directed graph. A leak gives the attacker one node, and
everything reachable from it is the blast radius. You rotate that whole set, not just the
leaked token. Attack-path tools build this graph and search it the same way, at a much larger scale.

**Where you see it:** BloodHound (Active Directory and Azure attack paths), cloud security
posture tools that show "attack paths" (for example Wiz and Orca), AWS IAM Access Analyzer,
incident-response runbooks for credential leaks.

**Reality check:** Real graphs have typed edges ("can assume role", "can read secret",
"can exec into pod") and conditions such as MFA or source IP. Tools weigh paths by how likely
they are to be used. This chip treats every edge as usable, which is the safe assumption during
an incident.

**What breaks if you get it wrong:** You rotate only the leaked token. The attacker already
used it to read the `.env` file, so they still hold the database password. Two weeks later the
orders table is dumped with a credential you believed was never exposed.

## 4. Problem Statement
There are `n` resources numbered `0` to `n - 1`. `holds[i]` lists the resources whose
credentials can be found in resource `i`: if you control `i`, you can take over every resource
in `holds[i]`. An attacker starts in control of resource `leaked`.

Return every resource the attacker can end up controlling, including `leaked`, sorted in
ascending order.

## 5. Input / Output format and Constraints
- `blast_radius(holds: list[list[int]], leaked: int) -> list[int]`
- `1 <= n <= 10^5`, total entries across all `holds[i]` `<= 3 * 10^5`.
- `0 <= holds[i][j] < n`. Entries may repeat and may point back to `i` itself.
- `0 <= leaked < n`.

## 6. Examples
**Example 1: a chain**
```
holds = [[1], [2], [3], []], leaked = 0  ->  [0, 1, 2, 3]
```
Token → VM → bucket → database.

**Example 2: direction matters (edge case)**
```
holds = [[], [0]], leaked = 0  ->  [0]
```
Resource 1 holds resource 0's credential, not the other way round.

**Example 3: cycles**
```
holds = [[1, 0], [0], [2]], leaked = 0  ->  [0, 1]
```
0 and 1 hold each other's keys. Resource 2 is never reached.

## 7. Starter Code
See [`starter.py`](starter.py): `blast_radius(holds, leaked)` with a docstring and type hints.

```bash
make try CHIP=02-security/DC-SEC-12-credential-blast-radius
```

## 8. Hints
1. **Nudge:** Draw each resource as a dot and each held credential as an arrow. What question are you asking about the dots?
2. **Pattern:** "Everything reachable from one start node" is a graph traversal, DFS or BFS, with a visited set.
3. **Near-solution:** Push `leaked` onto a stack and mark it seen. Pop a node, then push every
   unseen resource in `holds[node]`, marking each one when you push it. Use a loop, not recursion,
   so long chains don't hit Python's recursion limit.

## 9. Solution
**Approach**
1. Start a visited set and a stack, both holding `leaked`.
2. Pop a resource and look at every credential it holds.
3. For each resource not yet visited: mark it and push it.
4. When the stack is empty, the visited set is the blast radius. Return it sorted.

**Brute force:** Repeat "for every controlled resource, add everything it holds" until a pass
adds nothing. Each pass is O(n + E) and you may need up to n passes: O(n · (n + E)).

**Optimal code:** [`solution.py`](solution.py)

```python
def blast_radius(holds: list[list[int]], leaked: int) -> list[int]:
    seen = {leaked}
    stack = [leaked]              # iterative DFS: safe on long chains
    while stack:
        node = stack.pop()
        for nxt in holds[node]:
            if nxt not in seen:
                seen.add(nxt)     # mark on push: expand each node once
                stack.append(nxt)
    return sorted(seen)
```

**Complexity**
- Time: O(n + E + R log R), because each resource and each held credential is looked at once,
  then the R reached resources are sorted.
- Space: O(n) for the visited set and the stack.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: a chain, a single resource, cycles and self-references,
edge direction, a 50,000-long chain (catches recursive DFS hitting the recursion limit), a
production leaked CI token scenario, and random graphs checked against a repeat-until-stable brute force.

## 11. Interview Talk Track
"A leaked credential is a starting node in a graph where edges mean 'this resource holds the
key to that one'. The blast radius is everything reachable, so it's a plain DFS or BFS with a
visited set: O(nodes plus edges). I mark nodes when I push them so each one is expanded once,
and I use an explicit stack because credential chains can be long. The answer is the rotation
list for the incident. In production the edges carry types and conditions, and attack-path
tools weigh them, but during an incident you assume every edge works and rotate the whole reachable set."

## 12. Level Up
1. **"Which single credential, if rotated first, cuts the most reach?"** Compute reach with and
   without each edge on the path. At scale, look for dominators: nodes that every path from the
   leak must pass through. Rotating a dominator cuts off everything behind it.
2. **"The graph has 50 million edges across 300 accounts."** Store it in a graph database or as
   adjacency lists by account, and run BFS level by level so the frontier can be sharded across
   workers. Cache reachability for high-value targets such as production databases.
3. **"Some edges need MFA or only work from the corporate network."** Give edges conditions and
   only follow edges the attacker can satisfy with what they hold so far. Reach then depends on
   the set of capabilities gathered along the path, not just on the node.

## 13. Related Chips
- **DC-SEC-13 Secret Exposure Over Time**: the same spread, but edges only work at set times.
- **DC-NET-13 Reachability Check**: the network version, "can the internet reach this database?".
- **DC-REL-06 Change Impact Query**: many reachability questions answered after one precomputation.
