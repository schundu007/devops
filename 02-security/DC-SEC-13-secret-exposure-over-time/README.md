Source: New

# DC-SEC-13 · Secret Exposure Over Time

## 1. Header
| | |
|---|---|
| Chip ID | DC-SEC-13 |
| Difficulty | Hard |
| Pattern | Union-find per time group / BFS |
| Track | Cloud Security & IAM (SEC) |
| Classic pattern | LeetCode 2092 |
| Premium | No |
| Time box | 40 min |
| Source | New |

## 2. The Scenario
A Vault token leaked at 00:00, and `ci-runner-07` used it straight away. The session log shows
who connected to whom and when: at 00:10 `ci-runner-07` opened a session to `deploy-bot`, and
in the same minute `deploy-bot` connected to `k8s-admin`. `k8s-admin` also talked to
`backup-svc`, but at 00:05, before it held anything. Security must rotate credentials for
everyone who could have received the secret, and nobody else, because rotating everything
costs a full day of outages.

## 3. Why This Is DevOps
**Production reality:** A secret spreads through sessions: a CI job passes an environment
to a deploy job, a bot hands a token to another bot, a human pastes it into a shared shell.
Whether a party is exposed depends on *when* they connected, not just *whether* they did.
Someone who met a party before it was exposed is clean. Incident response rebuilds this timeline
from audit logs to decide who must rotate credentials. Time order is the whole problem.

**Where you see it:** HashiCorp Vault audit devices, AWS CloudTrail and Kubernetes audit logs
during credential-leak incidents, SIEM timeline tools (for example Splunk and Elastic Security).

**Reality check:** Real logs have second-level clocks that disagree across hosts, so
responders treat a small window (say ±60 seconds) as "the same time" instead of exact equality.
They also know which sessions actually carried the secret, which this chip assumes every session does.

**What breaks if you get it wrong:** Ignore time order and you rotate `backup-svc` for nothing:
a pointless outage on a clean system. Mishandle same-time chains and you miss `k8s-admin`,
which keeps a leaked credential in the cluster.

## 4. Problem Statement
There are `n` parties, numbered `0` to `n - 1`. Party `0` and party `first` hold the secret at
time 0. `sessions[i] = [a, b, t]` means parties `a` and `b` connected at time `t`. When two
parties connect, if either holds the secret at that moment, both hold it afterwards.

Sessions that share the same time `t` happen together: the secret can pass along a whole chain
of them in that instant. Return every party that holds the secret after all sessions, sorted ascending.

## 5. Input / Output format and Constraints
- `exposed(n: int, sessions: list[list[int]], first: int) -> list[int]`
- `2 <= n <= 10^5`, `0 <= len(sessions) <= 10^5`
- `sessions[i] = [a, b, t]`, `0 <= a, b < n`, `a != b`, `1 <= t <= 10^5`
- `1 <= first < n`. Sessions are **not** given in time order.

## 6. Examples
**Example 1: time order matters (edge case)**
```
n = 4, sessions = [[3, 2, 2], [1, 2, 5]], first = 1  ->  [0, 1, 2]
```
3 met 2 at t=2, but 2 only received the secret at t=5.

**Example 2: a same-time chain**
```
n = 5, sessions = [[3, 4, 3], [4, 1, 3]], first = 1  ->  [0, 1, 3, 4]
```
At t=3, 1 passes the secret to 4, and 4 to 3, in the same instant.

**Example 3: no sessions**
```
n = 2, sessions = [], first = 1  ->  [0, 1]
```

## 7. Starter Code
See [`starter.py`](starter.py): `exposed(n, sessions, first)` with a docstring and type hints.

```bash
make try CHIP=02-security/DC-SEC-13-secret-exposure-over-time
```

## 8. Hints
1. **Nudge:** Handle sessions in time order. What is special about all the sessions that share one timestamp?
2. **Pattern:** Within one time slot, sessions form groups (connected components). Union-find
   builds them. Any group that touches an exposed party becomes exposed.
3. **Near-solution:** Sort by time and group equal times. Union each session's two parties. Then
   for every party in this slot not connected to party 0, reset its parent to itself. This
   "un-union" stops a later session from exposing it retroactively.

## 9. Solution
**Approach**
1. Union-find over all parties. Union `0` with `first`.
2. Sort sessions by time, then process one time slot at a time.
3. Union both parties of every session in the slot, so chains link instantly.
4. For each party in the slot, if it is not connected to 0, reset it to its own set. It met
   people, but none of them held the secret.
5. At the end, return every party connected to 0. Keep 0's root as the root when merging,
   so "connected to 0" is always one `find` call.

**Brute force:** For each time slot, sweep its sessions again and again until nothing
changes. That is O(k²) per slot of k sessions, and O(m²) when every session shares one time.

**Optimal code:** [`solution.py`](solution.py) (key part)

```python
for _, group in groupby(sorted(sessions, key=lambda s: s[2]), key=lambda s: s[2]):
    group = list(group)
    for a, b, _t in group:
        union(a, b)                      # same instant: chains link together
    root0 = find(0)
    for a, b, _t in group:
        for p in (a, b):
            if find(p) != root0:
                parent[p] = p            # clean this slot: undo its links
```

**Complexity**
- Time: O(m log m + (m + n) · α(n)), because sorting m sessions dominates and each union-find
  call is nearly constant.
- Space: O(n + m) for the parent array and the sorted sessions.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: a normal chain, time order, a same-time chain, no
sessions, a clean group reset before a later slot, a production leaked-token scenario, and
random graphs (30 small plus one run of 20,000 parties and 50,000 sessions) checked against a
sweep-until-stable brute force.

## 11. Interview Talk Track
"This is leak-response timeline analysis. A secret passes through sessions, but only forward
in time, so I sort sessions by time and handle one timestamp at a time. Within a timestamp,
sessions can chain, so I union them all. Any group that touches party 0 is exposed. The
trick is the groups that don't: they met each other but nobody held the secret, so I reset
those nodes to their own sets. Otherwise a later session would expose them retroactively.
It's O(m log m) for the sort plus near-constant union-find calls. In a real incident, clocks
drift, so I'd treat a small window as simultaneous and only count sessions that could carry the secret."

## 12. Level Up
1. **"Clocks differ by up to 60 seconds between hosts."** Bucket time into windows, or treat
   sessions whose times overlap within the skew as one slot. The answer grows to include
   everyone who *might* be exposed, which is the safe choice for rotation.
2. **"Stream this live from the audit log."** Keep the exposed set. For each new time slot,
   BFS inside the slot's sessions starting from exposed parties. That is O(slot size) per slot,
   and nothing needs to be reset because clean parties never enter the set.
3. **"Not every session carries every secret."** Label edges with the secret types they can
   carry (a Vault token, a DB password) and run one spread per secret type. Rotation is then
   per secret, not per party.

## 13. Related Chips
- **DC-SEC-12 Blast Radius of a Leaked Credential**: the same spread with no time dimension.
- **DC-SEC-14 Identity Linker**: union-find to merge groups.
- **DC-NET-12 Failure Spread Timer**: spread in rounds, counted in minutes.
