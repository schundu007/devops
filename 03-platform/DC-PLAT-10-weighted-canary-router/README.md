Source: New

# DC-PLAT-10 · Weighted Canary Router

## 1. Header
| | |
|---|---|
| Chip ID | DC-PLAT-10 |
| Difficulty | Medium |
| Pattern | Prefix sums + binary search |
| Track | Platform Engineering, Scheduling & Allocation (PLAT) |
| Classic pattern | LeetCode 528 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
You are rolling out `orders-api` v2.4.0 as a canary. The rollout plan says: send 5% of
requests to the canary for 10 minutes, then 25%, then 50%, and promote if the error rate
holds. The mesh's route for `orders-api.prod.svc.cluster.local` lists two destinations,
`stable` with weight 95 and `canary` with weight 5. For every request, the proxy has to pick
one destination so that, over thousands of requests, the split matches the weights.

## 3. Why This Is DevOps
**Production reality:** Canary releases, blue-green cut-overs and A/B tests all say "send
this share of traffic here". The proxy turns the weights into running totals: `stable` owns
tickets 0–94 and `canary` owns 95–99. For each request it draws a random ticket and finds
the range that holds it. Finding the range with a binary search over the running totals
costs O(log n), even with many backends.

**Where you see it:** Istio `VirtualService` route `weight` fields, Envoy `weighted_clusters`,
Argo Rollouts canary `setWeight` steps, Flagger canary analysis, AWS ALB weighted target groups.

**Reality check:** With two or three backends, a proxy can simply walk the running totals,
so the binary search matters only with many backends (for example weighted endpoints across
hundreds of pods). Envoy does a similar idea: it draws a random value per request and
compares it with cumulative weights. Without a mesh, Argo Rollouts approximates the weight
by the ratio of canary to stable replicas, not per request.

**What breaks if you get it wrong:** An off-by-one in the ranges sends traffic to a drained
backend (weight 0), or gives the canary 6% instead of 5%. During a bad release, that means
real users hit the broken version the rollout was supposed to keep them away from.

## 4. Problem Statement
Build a `WeightedRouter` from a list of non-negative integer weights, one per backend.

- `pick()` returns a backend index `i` with probability `weights[i] / sum(weights)`.
- A backend with weight `0` is drained and must never be picked.
- Use the injected `rng` as the only source of randomness, and draw exactly one number per
  pick: `ticket = rng.randrange(total)`. Backend 0 owns tickets `[0, w0)`, backend 1 owns
  `[w0, w0 + w1)`, and so on. This makes the router testable and repeatable.
- Reject bad input with `ValueError`: an empty list, a negative weight, or a total of `0`.

## 5. Input / Output format and Constraints
- `weights`: `list[int]`, `1 <= len(weights) <= 10^5`, `0 <= weights[i] <= 10^5`, sum `> 0`.
- `rng`: an object with `randrange(stop) -> int`, by default `random.Random()`.
- `pick()` returns an `int` index. Up to `10^5` calls to `pick()`.

## 6. Examples
**Example 1: 90/10 split, ticket by ticket**
```
router = WeightedRouter([90, 10], rng)   # stable, canary
tickets 0, 8, 89 -> 0 (stable)           # stable owns 0..89
tickets 90, 99   -> 1 (canary)           # canary owns 90..99
```

**Example 2: a drained backend (edge case)**
```
router = WeightedRouter([5, 0, 5], rng)
tickets 0..4 -> 0, tickets 5..9 -> 2      # backend 1 owns no tickets at all
```

**Example 3: invalid**
```
WeightedRouter([])     -> ValueError
WeightedRouter([0, 0]) -> ValueError      # nowhere to send traffic
```

## 7. Starter Code
See [`starter.py`](starter.py): `WeightedRouter.__init__(weights, rng)` and `pick()` with
docstrings and type hints. Bodies are TODO.

```bash
make try CHIP=03-platform/DC-PLAT-10-weighted-canary-router
```

## 8. Hints
1. **Nudge:** Picture the weights as segments laid end to end on a line of length `total`.
   A random point on the line lands in one segment.
2. **Pattern:** Precompute running totals (a prefix sum). The segments' right edges are then
   sorted, so finding the segment for a point is a binary search.
3. **Near-solution:** `prefix = list(accumulate(weights))`. For `ticket = rng.randrange(prefix[-1])`,
   return `bisect_right(prefix, ticket)`. Zero weights repeat the previous prefix value, so
   `bisect_right` jumps past them.

## 9. Solution
**Approach**
1. Validate the weights, then build `prefix[i] = weights[0] + … + weights[i]`.
2. Backend `i` owns tickets `[prefix[i-1], prefix[i])`.
3. For each pick, draw `ticket` in `[0, total)` and return the first `i` with `prefix[i] > ticket`,
   which is `bisect_right(prefix, ticket)`.

**Brute force:** Walk the backends, subtracting weights until the ticket falls inside one.
That is O(n) per request: fine for 2 backends, too slow for 10,000 weighted endpoints at
high request rates.

**Optimal code:** [`solution.py`](solution.py)

```python
import random
from bisect import bisect_right
from itertools import accumulate


class WeightedRouter:
    def __init__(self, weights: list[int], rng: random.Random | None = None) -> None:
        if not weights or any(w < 0 for w in weights):
            raise ValueError("weights must be a non-empty list of non-negative ints")
        self._prefix = list(accumulate(weights))     # backend i owns [prefix[i-1], prefix[i])
        if self._prefix[-1] == 0:
            raise ValueError("at least one backend needs a positive weight")
        self._rng = rng if rng is not None else random.Random()

    def pick(self) -> int:
        ticket = self._rng.randrange(self._prefix[-1])
        return bisect_right(self._prefix, ticket)    # skips zero-weight backends
```

**Complexity**
- Time: O(n) to build the running totals once. O(log n) per `pick`, because it is a binary
  search over n totals.
- Space: O(n), for the running totals.

## 10. Tests
[`test_chip.py`](test_chip.py) has 8 cases, all deterministic. A scripted RNG feeds exact
tickets to check the 90/10 boundaries (and that there is one draw per pick over the right
total), a single backend, a drained backend, and three invalid inputs. A seeded RNG checks
the traffic split at 5%, 25% and 50% canary steps: 200,000 picks each, within 1 percentage
point. The noise is about 0.11 points, and the seed makes the result fixed. A large-input
check (5,001 backends, 3,002 tickets) compares against a brute-force walk.

## 11. Interview Talk Track
"A canary rollout says 'send 5% here', and the proxy has to honour that per request. I lay
the weights end to end as running totals, so each backend owns a range of tickets. For each
request I draw one ticket in zero to total and binary search the running totals for the
range that contains it. That's O(n) setup and O(log n) per request. Zero weights repeat the
previous total, so the search skips drained backends. Using bisect_right is what makes that
work. I inject the random source so tests can script exact tickets. In a mesh, Istio or
Argo Rollouts just rewrite the weights, and the proxy rebuilds its totals. If weights change
very often, I'd use a Fenwick tree so an update is O(log n) instead of a full rebuild."

## 12. Level Up
1. **"Weights change every few seconds (autoscaling endpoints)."** Rebuilding the prefix
   array is O(n) per change. A Fenwick (binary indexed) tree supports "change one weight"
   and "find the backend for a ticket" in O(log n) each.
2. **"The same user must keep hitting the same version."** Don't use a fresh random ticket.
   Hash a stable key (user ID or session cookie) into `[0, total)` instead. The split still
   follows the weights across users, but each user is sticky. Changing a weight moves only the
   users near the range edges.
3. **"O(1) picks at millions of requests per second."** Walker's alias method builds two
   tables in O(n) and then picks in O(1) with one random index and one coin flip. The cost is
   a full rebuild whenever any weight changes.

## 13. Related Chips
- **DC-PLAT-07 Round-Robin Load Balancer**: the deterministic way to spread requests over backends.
- **DC-CAP-01 Backlog Drain Rate**: binary search again, this time over the answer instead of a prefix array.
- **DC-SEC-06 Tenant Quota Guardrail**: running totals (prefix sums) over a timeline.
