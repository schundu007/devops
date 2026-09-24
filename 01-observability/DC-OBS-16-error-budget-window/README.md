Source: New

# DC-OBS-16 · Error Budget Window

## 1. Header
| | |
|---|---|
| Chip ID | DC-OBS-16 |
| Difficulty | Medium |
| Pattern | Sliding window |
| Track | Observability & SRE (OBS) |
| Classic pattern | LeetCode 1004 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
A blackbox probe checks `https://status.internal.example/health` every 30 seconds, and
each result is pass (1) or fail (0). Over the last 2 hours there were 240 probes, including
a 3-minute outage at probes 100–105 and a few scattered failures. The SLO review asks: "If we
can tolerate at most 4 failed probes, what is the longest stretch where we stayed inside that
budget?" The answer shows how much headroom the budget really gives.

## 3. Why This Is DevOps
**Production reality:** An SLO turns reliability into a budget: at 99.9% over 30 days you
may fail about 43 minutes. Engineers then ask window questions like "what is the longest
stretch that stayed within the budget?" or "where did we burn it?". Health-check results are a
pass/fail stream, and a sliding window that grows on the right and shrinks on the left, while
counting failures, answers these questions in one pass.

**Where you see it:** SLO tooling such as Sloth, Pyrra and Google Cloud SLO monitoring, the
Prometheus blackbox exporter (`probe_success` is exactly 1 or 0), Kubernetes probes
(`failureThreshold` counts consecutive failures), and uptime checks in Datadog or Pingdom.

**Reality check:** Real SLOs are usually ratios over time (good events ÷ total events over
30 days), and alerting uses burn rates over fixed windows, not "longest window" searches.
Kubernetes `failureThreshold` counts *consecutive* failures, which is a related but different
rule. This chip is an analysis tool for SLO reviews, not an alert rule.

**What breaks if you get it wrong:** If the window count is off, the review claims there
was more headroom than there was. The team then ships a risky migration into a budget that is
already spent, and the next incident breaches the SLO and the customer contract.

## 4. Problem Statement
You get `checks`, a list of health-check results in time order, where `1` means passed and
`0` means failed. You also get `budget`, the number of failures you can tolerate.

Return the length of the longest run of **consecutive** checks that contains at most `budget` failures.
Return `0` if no run qualifies (for example, an empty list).

## 5. Input / Output format and Constraints
- `checks: list[int]`, each value 0 or 1, with `0 <= len(checks) <= 10^5`.
- `budget: int`, with `0 <= budget <= len(checks)`.
- Returns `int`.

## 6. Examples
**Example 1**
```
longest_window([1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0], 2) -> 6
# positions 4..9: failures at 4 and 5 fit in the budget, then four passes
```

**Example 2: zero budget (edge case)**
```
longest_window([1, 0, 1, 1, 1, 0, 1, 1], 0) -> 3   # the longest all-pass run
```

**Example 3: every check failed**
```
longest_window([0, 0, 0, 0], 1) -> 1
```

## 7. Starter Code
See [`starter.py`](starter.py): `longest_window(checks, budget)` with a docstring and type
hints. The body is TODO.

```bash
make try CHIP=01-observability/DC-OBS-16-error-budget-window
```

## 8. Hints
1. **Nudge:** For a fixed right end, which left end gives the longest valid window? And does that left end ever need to move backward?
2. **Pattern:** A sliding window. Grow the right edge one check at a time, and count failures inside.
3. **Near-solution:** When failures exceed the budget, move `left` forward, subtracting a
   failure whenever `checks[left] == 0`, until the window is valid again. Track `right - left + 1`.

## 9. Solution
**Approach**
1. Two pointers, `left` and `right`, bound the window. Keep `failures`, the number of 0s inside it.
2. Move `right` across the list, and add 1 to `failures` when the new check failed.
3. While `failures > budget`, move `left` forward, subtracting 1 if the check leaving was a failure.
4. After each step the window is valid. Record its length.

**Brute force:** Try every start and extend until the budget breaks. That is O(n²), and far
too slow for 30 days of 10-second probes (about 260,000 checks).

**Optimal code:** [`solution.py`](solution.py)

```python
def longest_window(checks: list[int], budget: int) -> int:
    left = failures = best = 0
    for right, ok in enumerate(checks):
        if ok == 0:
            failures += 1
        while failures > budget:          # over budget: shrink from the left
            if checks[left] == 0:
                failures -= 1
            left += 1
        best = max(best, right - left + 1)
    return best
```

**Complexity**
- Time: O(n), because each check enters the window once and leaves it at most once.
- Space: O(1), for two pointers and a counter.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: the normal example, empty and single-check
inputs, a zero budget, a budget that covers every failure, all failures, a production-style
2-hour blackbox probe with an outage, and random checks against an O(n²) brute force
(30 random inputs plus one of 3,000 checks).

## 11. Interview Talk Track
"Health checks are a pass/fail stream, and the question is the longest stretch that stays
within an error budget of k failures. I use a sliding window. The right edge moves forward one
check at a time, counting failures. When the count goes over k, I move the left edge forward
until I've dropped a failure. The window is always valid, so I record its length. Each check
enters and leaves once, so it's O(n) time and O(1) space. In a real SLO this becomes a ratio,
like 99.9% of requests over 30 days, and alerting uses burn rates over fixed windows. This
exact search is useful in the SLO review, to show how much slack the budget really leaves."

## 12. Level Up
1. **"The budget is a percentage, not a count: at most 0.1% failures in the window."** The
   limit now depends on the window's size. Check `failures * 1000 <= length` instead. This is
   no longer monotonic in the same simple way, so use prefix sums of failures and search per
   right edge, or fix candidate window sizes (1 h, 6 h, 30 d) like multi-window burn-rate alerts do.
2. **"Probes come from 5 regions, and a check fails only if 3 or more regions fail."** Reduce
   each time slot to one pass/fail by majority vote first, then run the same window. This is
   how multi-location uptime checks avoid paging on one bad probe location.
3. **"Answer this live, over the last 30 days, as new probes arrive."** Keep a queue of the
   failure timestamps inside the rolling 30-day window. The live question becomes "how many
   failures in the window?", which is DC-OBS-02's counter with a longer window.

## 13. Related Chips
- **DC-OBS-02 5-Minute Error Counter**: counting failures in a rolling time window.
- **DC-OBS-06 Longest Stable Latency Window**: the longest window under a different rule (max − min).
- **DC-SEC-16 Brute-Force Burst Alert**: a sliding window over events per user.
