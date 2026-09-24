Source: Handbook #96 Course Schedule II — `apps/camora/src/data/capra/top100/96.json` (copied unchanged as `handbook.json`)

# DC-PLAT-01 · IaC Apply Order

## 1. Header `DevOps layer`
| | |
|---|---|
| Chip ID | DC-PLAT-01 |
| Difficulty | Medium |
| Pattern | Topological sort (Kahn) |
| Track | Platform Engineering, Scheduling & Allocation (PLAT) |
| Classic pattern | LeetCode 210 |
| Premium | No |
| Time box | 25 min |
| Source | Handbook #96 Course Schedule II |

## 2. The Scenario `DevOps layer`
A pull request adds a new web tier to the `payments` Terraform workspace: `aws_vpc.main`, two
private subnets (10.40.1.0/24 and 10.40.2.0/24), `aws_security_group.web`, two instances and
`aws_lb.web`. Each instance needs its subnet and the security group, and the load balancer
needs both subnets and both instances. `terraform plan` has to decide an order in which every
resource is created only after everything it references exists, or report that no such order exists.

**Mapping: DevOps term → handbook name**

| DevOps term | Handbook name |
|---|---|
| resource (numbered 0..n-1) | course |
| number of resources in the plan | `numCourses` |
| "A references B, so B must exist first" | `prerequisites[i] = [A, B]` |
| apply order | the returned ordering |
| a dependency cycle (`Error: Cycle: …`) | the empty array |

## 3. Why This Is DevOps `DevOps layer`
**Production reality:** Terraform builds a dependency graph from the references between
resources, then walks it: a resource starts only after everything it depends on is done.
Resources with no path between them are independent, so Terraform runs them in parallel (up
to `-parallelism`, 10 by default). On `terraform destroy` the walk runs in reverse, so the load
balancer goes before the instances, and the VPC goes last. Kahn's algorithm is this walk: the
queue of "no unfinished dependencies" nodes is exactly the set of resources ready to run now.

**Where you see it:** Terraform and OpenTofu (`terraform graph` prints the graph), Pulumi,
AWS CloudFormation (`DependsOn` and implicit references), Helm hooks ordered by weight (a simpler, linear version).

**Reality check:** Terraform's walker does not produce one flat list. It starts every ready
node at once, bounded by the parallelism limit, so the real "order" is a series of waves. A flat
topological order is one valid way to run those waves one resource at a time.

**What breaks if you get it wrong:** Create an instance before its subnet and the cloud API
rejects it halfway through the apply. You are left with a partly built stack, a state file that
needs repair, and a failed change during a deploy window.

## 4. Problem Statement `From handbook`
There are `numCourses` courses labelled `0` to `numCourses - 1`. Each entry `prerequisites[i] = [a, b]` means course `b` must be completed before course `a` can be taken.

Return **an ordering of all courses** that respects every prerequisite. If several orderings are valid, any one of them is accepted. If the prerequisites contain a cycle so that finishing everything is impossible, return an empty array.

## 5. Input / Output format and Constraints
**Input / Output format `(added)`:** `Solution().findOrder(numCourses: int, prerequisites: List[List[int]]) -> List[int]`.
Any valid order is accepted (the handbook marks this `cmp: "topo"`).

**Constraints `From handbook`**
- 1 ≤ numCourses ≤ 2000
- 0 ≤ prerequisites.length ≤ numCourses × (numCourses - 1)
- prerequisites[i].length == 2
- 0 ≤ aᵢ, bᵢ < numCourses
- aᵢ ≠ bᵢ
- All the pairs [aᵢ, bᵢ] are distinct

## 6. Examples `From handbook`
**Example 1 — Single row/column**
```
Input:  numCourses = 2, prerequisites = [[1, 0]]
Output: [0, 1]
```
Course `0` must precede course `1`.

**Example 2 — 4 prerequisites**
```
Input:  numCourses = 4, prerequisites = [[1, 0], [2, 0], [3, 1], [3, 2]]
Output: [0, 1, 2, 3]
```
`[0,2,1,3]` is equally valid: `0` first, `3` last.

**Example 3 — Empty input**
```
Input:  numCourses = 1, prerequisites = []
Output: [0]
```

## 7. Starter Code `(added)`
The handbook builds its starter from the problem's function signature and stores no starter file. See
[`starter.py`](starter.py): the same `findOrder` signature, with a TODO body.

```bash
make try CHIP=03-platform/DC-PLAT-01-iac-apply-order
```

## 8. Hints `From handbook`
1. Model courses as nodes and each prerequisite as a directed edge `b → a`; a valid order is a topological ordering of this graph.
2. Use Kahn's algorithm: compute in-degrees and repeatedly take courses that have no remaining prerequisites.
3. Start a queue with every zero in-degree course; when you pop one, append it to the order and decrement its neighbors, enqueuing any that reach zero. If the order ends shorter than `numCourses`, a cycle exists — return `[]`.

## 9. Solution `From handbook`
#### DFS Post-Order with Cycle Detection
Run DFS over the prerequisite graph with three colors; a course is appended after all its prerequisites finish, and meeting a gray node means a cycle.

- Edge prereq → course, recurse into prereqs
- Gray node on the stack = cycle
- Post-order yields a valid schedule

Time: O(V + E) · Space: O(V + E)

```python
class Solution:
    def findOrder(self, numCourses, prerequisites):
        prereqs = [[] for _ in range(numCourses)]
        for course, pre in prerequisites:
            prereqs[course].append(pre)
        state = [0] * numCourses  # 0 = unvisited, 1 = visiting, 2 = done
        order = []

        def dfs(c):
            if state[c] == 1:
                return False
            if state[c] == 2:
                return True
            state[c] = 1
            for p in prereqs[c]:
                if not dfs(p):
                    return False
            state[c] = 2
            order.append(c)
            return True

        for c in range(numCourses):
            if not dfs(c):
                return []
        return order
```

#### Kahn's Algorithm (Optimal)
Repeatedly take courses with no remaining prerequisites, decrementing the in-degree of courses that depend on them; if not every course gets taken, there is a cycle.

- Start with in-degree 0 courses
- Removing a course frees its dependents
- Short output means a cycle

Time: O(V + E) · Space: O(V + E)

```python
from collections import deque

class Solution:
    def findOrder(self, numCourses, prerequisites):
        graph = [[] for _ in range(numCourses)]
        indeg = [0] * numCourses
        for course, pre in prerequisites:
            graph[pre].append(course)
            indeg[course] += 1
        q = deque(c for c in range(numCourses) if indeg[c] == 0)
        order = []
        while q:
            c = q.popleft()
            order.append(c)
            for nxt in graph[c]:
                indeg[nxt] -= 1
                if indeg[nxt] == 0:
                    q.append(nxt)
        return order if len(order) == numCourses else []
```

`solution.py` is the handbook's optimal Python solution (Kahn's Algorithm), copied unchanged.
The handbook's Java, C++, Go and JavaScript versions are in `handbook.json` → `solutions[].code`.

## 10. Tests
**From handbook:** 29 cases in `handbook.json` → `tests`, run unchanged by `test_chip.py`.

**`(added)`** [`test_chip.py`](test_chip.py) wraps those cases in pytest. Because many
orders are valid, it checks each answer with a local validity checker (`is_valid_order`: every
resource exactly once, every dependency first) instead of comparing to the one listed order.
It runs **every** Python solution from the handbook (the Step 3 check). It adds three
DevOps-layer cases: the Terraform stack above (apply order, and its reverse as a valid destroy
order), a reference cycle that must return `[]`, and a 2,000-node, 8,000-edge random DAG.

## 11. Interview Talk Track `DevOps layer`
"This is how Terraform decides what to create first. Each resource is a node, and each reference
is an edge from the thing referenced to the thing that uses it. I count, for every node, how many
dependencies it is still waiting on. Everything at zero goes in a queue. Those are the resources
that can start right now, in parallel. I pop one, 'create' it, and decrement its dependents;
any that reach zero join the queue. If I finish with fewer nodes than I started with, the
leftovers are in a cycle, and that's Terraform's 'Cycle' error. It's O(V + E). Destroy is the
same walk on the reversed graph, which is why the VPC is created first and deleted last."

## 12. Level Up `DevOps layer`
1. **"Run it as fast as possible with 10 workers."** Don't flatten to one list. Process the
   graph in waves: start every zero-dependency node (up to 10 at a time), and when one finishes,
   decrement its dependents and start the ones that became ready. Total time is bounded below
   by the longest dependency chain. DC-REL-03 computes that critical path.
2. **"One resource failed mid-apply."** Stop scheduling its dependents, because they can
   never become ready, but let independent branches finish. Record what succeeded, so the next
   run only has the remainder to do. Terraform keeps successful resources in state and leaves
   the failed branch to the next apply.
3. **"The graph has 200,000 resources across many workspaces."** Split it along workspace or
   module boundaries, and pass data between them by explicit outputs, so each graph stays
   small. A cycle across workspaces then shows up as an ordering problem between pipelines,
   which DC-PLAT-02 can detect.

## 13. Related Chips `DevOps layer`
- **DC-PLAT-02 Circular Dependency Detector**: the same graph, asking only "is there a cycle?"
- **DC-REL-03 Pipeline Critical Path**: topological order plus the longest chain of durations.
- **DC-REL-05 Buildable Artifacts**: a topological walk that starts from what already exists.
