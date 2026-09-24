Source: New

# DC-PLAT-05 · Shortest Safe Upgrade Path

## 1. Header
| | |
|---|---|
| Chip ID | DC-PLAT-05 |
| Difficulty | Medium |
| Pattern | BFS |
| Track | Platform Engineering, Scheduling & Allocation (PLAT) |
| Classic pattern | LeetCode 433 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
Cluster `prod-eu-1` runs control plane 1.27, kubelets 1.27 and etcd 3.5. The target is 1.29
everywhere. The platform team keeps a list of **approved** combinations, the ones that have
passed the conformance suite in staging. The change policy says each maintenance window changes
**one** component, and the cluster must always land in an approved combination. What is the
fewest number of maintenance windows to reach the target, or is it impossible with the current list?

## 3. Why This Is DevOps
**Production reality:** Upgrades are a path through states, not a jump. Kubernetes supports
upgrading the control plane only one minor version at a time (kubeadm refuses to skip minors),
and kubelets must stay within the supported version skew of the API server. Every
intermediate state must be one you have tested. Treat each approved combination as a node,
connect two nodes when they differ in exactly one component, and BFS finds the fewest windows,
because every window costs the same.

**Where you see it:** kubeadm and managed Kubernetes upgrades (EKS, GKE and AKS upgrade one
minor at a time), the Kubernetes version skew policy, MongoDB (which must be upgraded through each major
release series in turn, for example 5.0 → 6.0 → 7.0), and OS upgrade tools that step through releases.

**Reality check:** Real upgrade planners also weigh risk and time, not just the number of
steps. A weighted version of this chip needs Dijkstra (DC-NET-04). The "approved" list usually
comes from a support matrix, not a hand-written set, and components such as node pools can
sometimes be upgraded in parallel.

**What breaks if you get it wrong:** Skip a minor on the control plane, or let the kubelets fall
outside the allowed skew, and you get an unsupported cluster. Nodes may stop registering, some
APIs may behave differently, and rollback is hard, because etcd data has already been migrated.

## 4. Problem Statement
A cluster state is a tuple of component versions, all of the same length, for example
`("1.28", "1.27", "3.5")` for (control plane, kubelet, etcd).

In one **step** you change exactly **one** component to any other version, and the new state
must be in the list `approved`. The starting state does not have to be approved: you may start
from a state that is out of policy.

Given `start`, `target` and `approved`, return the fewest steps from `start` to `target`.
Return `0` if they are equal, and `-1` if `target` cannot be reached (including when `target` is
not approved).

## 5. Input / Output format and Constraints
- `min_upgrade_steps(start: Sequence[str], target: Sequence[str], approved: list[Sequence[str]]) -> int`
- All states have the same length `L`, with `1 <= L <= 10`.
- `0 <= len(approved) <= 10^4`. Duplicates in `approved` are allowed and mean nothing extra.
- Component versions are non-empty strings.

## 6. Examples
**Example 1: minor by minor**
```
start    = ("1.27", "1.27", "3.5")
target   = ("1.29", "1.29", "3.5")
approved = [("1.28","1.27","3.5"), ("1.28","1.28","3.5"), ("1.29","1.28","3.5"), ("1.29","1.29","3.5")]
-> 4
```
Control plane to 1.28, kubelets to 1.28, control plane to 1.29, kubelets to 1.29.

**Example 2: target not approved (edge case)**
```
start = ("1.27",), target = ("1.29",), approved = [("1.28",)]  -> -1
```
Even though 1.28 is reachable, the target itself is not an approved state.

**Example 3: already there**
```
start = target = ("1.29", "1.29", "3.5"), approved = []  -> 0
```

## 7. Starter Code
See [`starter.py`](starter.py): the `min_upgrade_steps` signature, with a docstring and a TODO body.

```bash
make try CHIP=03-platform/DC-PLAT-05-safe-upgrade-path
```

## 8. Hints
1. **Nudge:** Every step costs one maintenance window. What search finds the fewest equal-cost steps?
2. **Pattern:** Breadth-first search over states. The hard part is finding a state's neighbours
   quickly: the approved states that differ from it in exactly one position.
3. **Near-solution:** For each approved state and each position `i`, put the state in a bucket
   keyed by `(i, state with position i removed)`. Two states are neighbours exactly when they share a
   bucket. BFS from `start`, and after a bucket has been expanded, delete it so it is never scanned again.

## 9. Solution
**Approach**
1. Handle the easy cases: `start == target` gives 0, and a target that is not approved gives -1.
2. Build the buckets: `(i, state without position i) -> [states]`.
3. BFS from `start`. For each position `i`, every state in bucket `(i, state without i)` is one
   step away. Return `steps + 1` when you reach the target.
4. Drop each bucket after using it: all its states are now queued, so it has nothing left to give.
5. If the queue empties first, return -1.

**Brute force:** For each state you pop, compare it to every approved state to find the ones
that differ in one position. That is O(N² · L) for N approved states, too slow at 10^4 states
and 10^4 queries.

**Optimal code:** [`solution.py`](solution.py)

```python
from collections import defaultdict, deque


def min_upgrade_steps(start, target, approved) -> int:
    src, dst = tuple(start), tuple(target)
    if src == dst:
        return 0
    allowed = {tuple(s) for s in approved}
    if dst not in allowed:
        return -1
    buckets = defaultdict(list)                     # (pos, state minus pos) -> states
    for s in allowed:
        for i in range(len(s)):
            buckets[(i, s[:i] + s[i + 1:])].append(s)
    seen, queue = {src}, deque([(src, 0)])
    while queue:
        state, steps = queue.popleft()
        for i in range(len(state)):
            key = (i, state[:i] + state[i + 1:])
            for nxt in buckets.get(key, ()):
                if nxt == dst:
                    return steps + 1
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, steps + 1))
            buckets.pop(key, None)                  # never scan this bucket again
    return -1
```

**Complexity**
- Time: O(N · L²). Building the buckets touches N states × L positions, and each key costs
  O(L) to build. BFS visits each bucket once, because buckets are deleted after use.
- Space: O(N · L²), for the N × L bucket keys of length L - 1 each.

## 10. Tests
[`test_chip.py`](test_chip.py) has 8 cases: the Kubernetes minor-by-minor path, a path that can't
skip minors, already at the target, a target that isn't approved, unreachable and empty inputs, a
start state outside policy, 20 random graphs checked against a separate pairwise-compare BFS, and a
10,000-state chain.

## 11. Interview Talk Track
"Every maintenance window changes one component, and every window costs the same, so the
fewest windows is a shortest path in an unweighted graph, which means BFS. The nodes are the
approved version combinations, and two nodes are connected when they differ in exactly one
component. The trick is finding neighbours without comparing every pair. I bucket each state
by 'this position blanked out', so neighbours share a bucket, and I delete a bucket after using
it, so the whole BFS is linear in the number of states times the key cost. If the target isn't
approved, I return -1 right away. In practice the approved list comes from the Kubernetes skew
policy and our conformance runs, and if windows had different risk, I'd switch to Dijkstra."

## 12. Level Up
1. **"Return the actual plan, not just the count."** Store `parent[state]` when you enqueue it,
   then walk back from the target. The printed plan is the change calendar: one line per window.
2. **"Some steps are riskier or slower than others."** Give each change a weight (an etcd
   minor upgrade might cost 3 and a kubelet change 1) and run Dijkstra (DC-NET-04). BFS is
   only correct when every step costs the same.
3. **"The state space is huge: 30 components with 5 versions each."** Don't list states up front.
   Generate neighbours lazily from rules (skew limits, one-minor steps), and search from both ends
   at once (bidirectional BFS), which explores roughly the square root of the states.

## 13. Related Chips
- **DC-PLAT-01 IaC Apply Order**: ordering changes when the order is forced by dependencies.
- **DC-NET-04 Network Delay Time**: the weighted version (Dijkstra).
- **DC-REL-02 Version Comparator**: deciding which version is newer in the first place.
- Handbook: #97 Word Ladder uses the same BFS with bucketed neighbours (a different problem).
