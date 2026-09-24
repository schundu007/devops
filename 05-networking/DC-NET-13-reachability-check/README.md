Source: New

# DC-NET-13 · Reachability Check

## 1. Header
| | |
|---|---|
| Chip ID | DC-NET-13 |
| Difficulty | Easy |
| Pattern | BFS / union-find |
| Track | Networking, Service Mesh & Resilience (NET) |
| Classic pattern | LeetCode 1971 |
| Premium | No |
| Time box | 15 min |
| Source | New |

## 2. The Scenario
A security review for the `payments` VPC (10.40.0.0/16) asks one yes/no question: "Can
anything on the internet reach the Postgres database?" The allowed paths are internet → ALB →
web tier → app tier. The app tier's rule to the database was removed in the last change, and the
database now only accepts traffic from the bastion host. Is the database reachable from the
internet? What if someone opens the bastion to the world?

## 3. Why This Is DevOps
**Production reality:** Firewalls, security groups, route tables and peering links together
define which systems can talk. The question security teams ask most often is "can A reach B
at all?". Model each allowed path as an edge, and the answer is graph reachability: BFS from A,
or check whether A and B are in the same union-find group. Running this check in CI on every
network change catches the moment a database quietly becomes internet-reachable.

**Where you see it:** AWS VPC Reachability Analyzer (checks whether a path exists between two
resources, and reports the blocking component if not), AWS Network Access Analyzer, Azure
Network Watcher connection troubleshoot, network policy linting in CI.

**Reality check:** VPC Reachability Analyzer works on your configuration and does not send
packets. It is also directional and protocol- and port-aware: a security group can allow
A → B on 443 but not B → A. This chip uses two-way links with no ports. For direction, see Level Up 1.

**What breaks if you get it wrong:** Check only the direct rules into the database ("only the
bastion is allowed, so we're safe") and you miss a path through the bastion. That multi-hop
path is how many real breaches reach the data tier.

## 4. Problem Statement
There are `n` systems, numbered `0` to `n - 1`. Each `links[i] = [a, b]` means traffic is allowed
between `a` and `b` in both directions.

Return `True` if traffic starting at `source` can reach `target`, possibly through other
systems, and `False` otherwise. A system can always reach itself.

## 5. Input / Output format and Constraints
- Returns a bool.
- `1 <= n <= 2 * 10^5`, `0 <= len(links) <= 2 * 10^5`.
- `0 <= a, b < n` and `a != b`. There are no duplicate links.
- `0 <= source, target < n`.

## 6. Examples
**Example 1: through the middle tier**
```
n = 3, links = [[0,1],[1,2]], source = 0, target = 2  ->  True
```

**Example 2: two separate segments**
```
n = 6, links = [[0,1],[0,2],[3,5],[5,4],[4,3]], source = 0, target = 5  ->  False
```
{0,1,2} and {3,4,5} never touch.

**Example 3: source equals target (edge case)**
```
n = 1, links = [], source = 0, target = 0  ->  True
```

## 7. Starter Code
See [`starter.py`](starter.py): the `can_reach(n, links, source, target)` signature, docstring and
type hints. The body is TODO.

```bash
make try CHIP=05-networking/DC-NET-13-reachability-check
```

## 8. Hints
1. **Nudge:** Turn the list of links into "who can each system talk to?".
2. **Pattern:** Graph reachability: BFS or DFS from `source`, or union-find groups.
3. **Near-solution:** Build an adjacency list with both directions. BFS from `source`, marking
   nodes as seen when they are enqueued, and return `True` as soon as `target` appears. Use a loop,
   not recursion: a 200,000-node chain overflows Python's recursion limit.

## 9. Solution
**Approach**
1. Handle `source == target` first.
2. Build the adjacency list (both directions per link).
3. BFS from `source`, marking seen on enqueue. Return `True` when `target` is found.
4. If the queue empties first, return `False`.

**Brute force:** Repeatedly scan all links, spreading "reachable" to both ends, until nothing
changes. Each pass is O(E), and a long chain needs up to n passes, so it is O(n · E).

**Optimal code:** [`solution.py`](solution.py)

```python
from collections import deque


def can_reach(n, links, source, target):
    if source == target:
        return True
    adj = [[] for _ in range(n)]
    for a, b in links:
        adj[a].append(b)
        adj[b].append(a)
    seen = [False] * n
    seen[source] = True
    queue = deque([source])
    while queue:
        node = queue.popleft()
        for nxt in adj[node]:
            if nxt == target:
                return True
            if not seen[nxt]:
                seen[nxt] = True
                queue.append(nxt)
    return False
```

**Complexity**
- Time: O(n + E). Every node is enqueued at most once, and every link is looked at twice.
- Space: O(n + E), for the adjacency list, `seen` and the queue.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: a path through the middle tier, two separate segments, a
single node, no links, the internet-to-database scenario before and after opening the bastion,
300 random graphs checked against union-find, and a 200,000-node chain (which would crash a recursive DFS).

## 11. Interview Talk Track
"Can the internet reach this database? That's reachability on a graph where every allowed path
is an edge. I build an adjacency list and BFS from the source, marking nodes when I enqueue them,
and return true as soon as the target appears. That's O(V + E). I use an iterative BFS, because
real network graphs can have long chains that overflow recursion. If I have to answer many
reachability questions on a graph that doesn't change, I'd precompute union-find groups, and each
query becomes near O(1). Real security groups are one-way and port-specific, so for a production
check I'd use directed edges labelled with protocol and port, which is what the AWS Reachability Analyzer models."

## 12. Level Up
1. **"Rules are one-way: A may call B, but B may not call A."** Store directed edges and BFS only
   along them. Union-find no longer works, because it assumes symmetry. For many queries,
   compute strongly connected components, then reachability on the condensed DAG.
2. **"Which ports?"** Label each edge with its allowed port set. Search over (node, port) states,
   or run one BFS per port class (for example 22, 443, 5432). The answer becomes "reachable
   on 5432 through the bastion".
3. **"Run it on every Terraform plan in CI, for 50 sensitive targets."** Run one BFS from
   "internet" and check all 50 targets in its result, instead of 50 searches. Fail the pipeline
   if the set of reachable sensitive targets grows compared with `main`.

## 13. Related Chips
- **DC-SEC-12 Blast Radius of a Leaked Credential**: everything reachable from one starting point.
- **DC-NET-07 Heal a Network Partition**: counting the separate segments with union-find.
- **DC-NET-12 Failure Spread Timer**: BFS from many sources, measuring time as well as reach.
