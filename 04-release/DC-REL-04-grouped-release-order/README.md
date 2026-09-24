Source: New

# DC-REL-04 · Grouped Release Order

## 1. Header
| | |
|---|---|
| Chip ID | DC-REL-04 |
| Difficulty | Hard |
| Pattern | Two-level topological sort |
| Track | Release & CI/CD (REL) |
| Classic pattern | LeetCode 1203 |
| Premium | No |
| Time box | 40 min |
| Source | New |

## 2. The Scenario
Thursday's release train ships three services: `orders-db`, `orders-api` and `orders-web`.
Each has several steps. For example, `orders-db` has `db-backup`, `db-migrate` and
`db-verify`. The change policy says one team must finish all of its steps before the next
team starts, so each service's steps must run as one block. There are also cross-service
rules: `db-verify` before `api-canary`, and `api-smoke` before `web-rollout`. A standalone
`announce` step posts to #releases at the end. Produce a runbook order, or report that the
rules contradict each other.

## 3. Why This Is DevOps
**Production reality:** Releases that span several services need two kinds of order. Inside
a service, steps depend on each other (back up, then migrate, then verify). Between
services, whole blocks depend on each other (database before API before frontend). And each
service's steps should run together, so one team owns one window and one rollback point.
Solving this is a topological sort at two levels: order the services, order the steps, then
join them.

**Where you see it:** Argo CD sync waves (the `argocd.argoproj.io/sync-wave` annotation) and
Helm hook weights order groups of resources. Multi-service release runbooks and
change-management windows are built the same way, and so are Spinnaker pipelines with stage dependencies.

**Reality check:** Argo CD and Helm give each group a number and apply the groups in
numeric order; they don't derive the order from the step dependencies. This chip derives it
from the dependencies, which is closer to how release managers plan a train. It also
detects rules that contradict each other, which fixed numbers cannot do.

**What breaks if you get it wrong:** The frontend rolls out before the API it calls, or a
migration runs after the code that needs it. Users see 500s during the release, and the
rollback has to unwind two half-finished services.

## 4. Problem Statement
A release has `n` steps numbered `0..n-1` and `m` services numbered `0..m-1`.
`service[i]` is the service that step `i` belongs to, or `-1` if it belongs to none.
`before[i]` lists the steps that must run earlier than step `i`.

Return an order of all `n` steps where:
- every rule in `before` holds, and
- all steps of the same service appear next to each other (one contiguous block).

Steps with service `-1` have no block to stay in. If several orders work, return any one.
If none exists, return an empty list.

## 5. Input / Output format and Constraints
- `release_order(n: int, m: int, service: list[int], before: list[list[int]]) -> list[int]`
- `0 <= n <= 3 * 10^4`, `0 <= m <= n` (or 0).
- `-1 <= service[i] < m`.
- `0 <= len(before[i]) <= n - 1`. Entries are distinct, in `0..n-1`, and never `i` itself.
- The answer is any valid order, or `[]` if none exists.

## 6. Examples
**Example 1**
```
n = 8, m = 2
service = [-1, -1, 1, 0, 0, 1, 0, -1]
before  = [[], [6], [5], [6], [3, 6], [], [], []]
release_order(...) -> e.g. [6, 3, 4, 1, 5, 2, 0, 7]
```
Service 0 is `{3, 4, 6}` and service 1 is `{2, 5}`. Each block is contiguous, `6 → 3 → 4`
and `5 → 2` hold, and step 1 comes after 6.

**Example 2: contradicting services (edge case)**
```
n = 4, m = 2, service = [0, 0, 1, 1], before = [[], [3], [0], []]
release_order(...) -> []
```
Step 0 (service 0) must precede step 2 (service 1), so service 0's block comes first. But
step 3 (service 1) must precede step 1 (service 0), so service 1's block comes first. Both
blocks cannot stay contiguous, even though the steps alone have no cycle.

**Example 3: a single step**
```
n = 1, m = 0, service = [-1], before = [[]]
release_order(...) -> [0]
```

## 7. Starter Code
See [`starter.py`](starter.py): `release_order(n, m, service, before)` with a docstring and type hints.

```bash
make try CHIP=04-release/DC-REL-04-grouped-release-order
```

## 8. Hints
1. **Nudge:** If you ignore the "blocks stay together" rule, it is a plain topological sort.
   What extra ordering do the blocks need?
2. **Pattern:** Two topological sorts: one over services, one over steps. A cross-service
   rule `p → i` also means "service of p before service of i".
3. **Near-solution:** Give each `-1` step its own new service ID. Build both graphs from
   `before`, and topologically sort each (return `[]` on a cycle). Put the sorted steps into
   buckets by service, then print the buckets in service order.

## 9. Solution
**Approach**
1. Give every standalone step its own new group, so every step has exactly one group.
2. For each rule `p before i`, add the step edge `p → i`. If `p` and `i` are in different
   groups, also add the group edge `group[p] → group[i]`.
3. Topologically sort the steps and the groups with Kahn's algorithm. If either has a cycle, return `[]`.
4. Walk the sorted steps and put each into its group's bucket. Order inside each group is then correct.
5. Print the buckets in the sorted group order. Cross-group rules hold because of the group
   order, and rules inside a group hold because of the step order.

**Brute force:** Try every permutation of the steps and check both rules. That is O(n!·n²)
and hopeless beyond about 10 steps. The tests use it only to check small cases.

**Optimal code:** [`solution.py`](solution.py)

```python
def release_order(n, m, service, before):
    group = list(service)
    groups = m
    for i in range(n):
        if group[i] == -1:                  # standalone step: its own group
            group[i] = groups
            groups += 1
    step_adj = [[] for _ in range(n)]; step_in = [0] * n
    group_adj = [[] for _ in range(groups)]; group_in = [0] * groups
    for i in range(n):
        for p in before[i]:
            step_adj[p].append(i); step_in[i] += 1
            if group[p] != group[i]:
                group_adj[group[p]].append(group[i]); group_in[group[i]] += 1
    step_order = _topo(step_adj, step_in)     # Kahn's algorithm, None on a cycle
    group_order = _topo(group_adj, group_in)
    if step_order is None or group_order is None:
        return []
    buckets = [[] for _ in range(groups)]
    for s in step_order:
        buckets[group[s]].append(s)
    return [s for g in group_order for s in buckets[g]]
```

**Complexity**
- Time: O(n + m + E), where E is the total number of `before` entries. Each topological sort is linear.
- Space: O(n + m + E) for the two graphs and the buckets.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 tests, all checked with a validity checker (every step
once, every rule holds, every service contiguous) rather than one exact answer. They cover
a mixed example, single and empty inputs, a step cycle, a service cycle with no step cycle
(confirmed by brute force), the db → api → web release train, 400 random small cases against
brute force over all permutations, and a 3,000-step instance built around a hidden valid order.

## 11. Interview Talk Track
"This is a release train. Each service's steps must stay together, and there are rules both
inside and across services. A single topological sort over steps would respect the rules
but could interleave services. So I do it at two levels. Each rule adds a step edge, and if
it crosses services it also adds a service edge. I topologically sort both graphs. A cycle in
either one means no valid runbook, and I return empty. That also catches the subtle case
where the steps are fine but two services each need to go first. Then I drop the sorted steps
into per-service buckets and print the buckets in service order. Everything is linear.
In practice this is what sync waves approximate with fixed numbers, but deriving the order
also finds contradictions before the release window starts."

## 12. Level Up
1. **"Services with no rules between them could run at the same time."** Use levels in the
   service sort: every service whose dependencies are all done forms a wave, and each wave
   runs in parallel. The number of waves is the length of the longest service chain. This is
   what sync waves express by hand.
2. **"A step fails halfway through."** Record the finished steps. The rollback order is the
   reverse of the finished part of the plan, run service by service in reverse service
   order. That keeps each team's rollback in one window.
3. **"The order has to be stable between runs, for review."** Replace the FIFO queue with a
   min-heap keyed by (priority, name). The order becomes deterministic and it prefers lower
   priorities, so the same rules always produce the same runbook diff.

## 13. Related Chips
- **DC-PLAT-01 IaC Apply Order**: a one-level topological sort.
- **DC-REL-03 Pipeline Critical Path**: topological order plus timing.
- **DC-PLAT-02 Circular Dependency Detector**: the cycle check this chip does twice.
