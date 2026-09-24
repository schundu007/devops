Source: New

# DC-SEC-16 · Brute-Force Burst Alert

## 1. Header
| | |
|---|---|
| Chip ID | DC-SEC-16 |
| Difficulty | Medium |
| Pattern | Sort + sliding window |
| Track | Cloud Security & IAM (SEC) |
| Classic pattern | LeetCode 1604 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
The bastion host `bastion-01` (10.0.0.5) writes every failed SSH login to its auth log as
`(account, HH:MM)`. Overnight the log shows `admin` failing at 02:10, 02:40 and 03:05, and a
few scattered failures for `backup` and `deploy`. The rule is simple: if the same account fails
3 or more times within one hour, alert and lock it. The morning report must list exactly the
accounts that tripped the rule.

## 3. Why This Is DevOps
**Production reality:** Repeated failures of one account or key in a short time are the
signature of brute-force guessing, password spraying and stolen-key abuse. Detection groups
events by account, sorts them by time, and checks whether any N of them fit inside the window.
The same rule shape rate-limits API keys and triggers temporary bans at the edge.

**Where you see it:** fail2ban (`maxretry` within `findtime`), AWS WAF rate-based rules, Okta
and Microsoft Entra smart lockout, SIEM threshold rules on auth logs.

**Reality check:** fail2ban and SIEMs work on a live stream and keep only the recent timestamps
per key, instead of sorting a full day. Real rules also look across accounts from one source
IP, because password spraying tries *one* password against *many* accounts to stay under
per-account limits.

**What breaks if you get it wrong:** If you check only fixed clock hours (02:00–02:59), failures
at 02:40, 03:05 and 03:30 never alert, even though they fit one sliding hour. An attacker who
learns your windows can pace guesses to dodge them.

## 4. Problem Statement
`names[i]` is the account used at `times[i]`, written `"HH:MM"` in 24-hour form. All times are
within one day. Raise an alert for an account if it was used **3 or more times within any
60-minute span**. The span is inclusive: `10:00`, `10:30` and `11:00` count; `10:00`, `10:30`
and `11:01` do not.

Return the alerted account names, sorted ascending and each listed once.

## 5. Input / Output format and Constraints
- `burst_alerts(names: list[str], times: list[str]) -> list[str]`
- `0 <= len(names) == len(times) <= 10^5`
- Names are 1–20 characters (lowercase letters, digits, `-`). Times are `"00:00"` to `"23:59"`.
- Times are not sorted and may repeat.

## 6. Examples
**Example 1: three in one hour**
```
names = ["svc-ci", "svc-ci", "svc-ci", "bo", "bo"]
times = ["10:00", "10:40", "10:59", "09:00", "09:05"]
-> ["svc-ci"]
```

**Example 2: the one-hour boundary (edge case)**
```
["a","a","a"], ["10:00","10:30","11:00"]  ->  ["a"]
["a","a","a"], ["10:00","10:30","11:01"]  ->  []
```

**Example 3: spread-out uses**
```
["a"] * 4, ["01:00","01:50","02:51","03:40"]  ->  []
```
Any three of these span more than 60 minutes.

## 7. Starter Code
See [`starter.py`](starter.py): `burst_alerts(names, times)` with a docstring, type hints and the limits as constants.

```bash
make try CHIP=02-security/DC-SEC-16-brute-force-burst
```

## 8. Hints
1. **Nudge:** Convert `"HH:MM"` into minutes since midnight, and look at one account at a time.
2. **Pattern:** Sort each account's minutes. Three uses fit an hour if and only if three
   *consecutive* sorted uses fit it.
3. **Near-solution:** For each account's sorted list `ts`, alert if any `ts[i] - ts[i - 2] <= 60`.
   Collect those names and sort them.

## 9. Solution
**Approach**
1. Convert each time to minutes: `h * 60 + m`.
2. Group the minutes by account and sort each group.
3. Slide a window of 3 consecutive uses. If the first and last are at most 60 minutes apart, alert.
4. Return the alerted names, sorted.

Why consecutive is enough: if any 3 uses fit in 60 minutes, then the first of them and the
next two uses in sorted order also fit, because those two lie between the first and the third.

**Brute force:** Try every triple of one account's uses: O(k³) for k uses. An account with
1,000 failures means 166 million triples.

**Optimal code:** [`solution.py`](solution.py)

```python
def burst_alerts(names: list[str], times: list[str]) -> list[str]:
    minutes: dict[str, list[int]] = defaultdict(list)
    for name, hhmm in zip(names, times):
        h, m = hhmm.split(":")
        minutes[name].append(int(h) * 60 + int(m))
    alerted = []
    for name, ts in minutes.items():
        ts.sort()
        if any(ts[i] - ts[i - 2] <= 60 for i in range(2, len(ts))):
            alerted.append(name)
    return sorted(alerted)
```

**Complexity**
- Time: O(n log n), because each account's uses are sorted once. The scan is O(n).
- Space: O(n) for the grouped minutes.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: three in an hour, empty and single, the inclusive
one-hour boundary, unsorted input with duplicate times, spread-out uses, a production
password-spray log, and random data checked against an all-triples brute force (240 events), plus
100,000 events checked against an independent bisect count.

## 11. Interview Talk Track
"This is a fail2ban-style rule: lock an account after 3 failures in any rolling hour. I convert
times to minutes, group by account and sort. The trick is that three uses fit in an hour exactly
when three *consecutive* sorted uses do, so one pass comparing `ts[i]` with `ts[i-2]` is enough.
That's O(n log n) overall. It must be a sliding window, not fixed clock hours, or an attacker can
spread guesses across the hour boundary. In production this runs on a stream: keep a small deque of
recent failures per key and drop the old ones. I'd also add a per-source-IP rule, because
password spraying hits many accounts once each."

## 12. Level Up
1. **"Run it live on 1 million events per minute."** Per key, keep a deque of the last
   `BURST - 1` failure times. On each new failure, drop entries older than 60 minutes. If the
   deque then holds `BURST - 1` entries, alert. Memory is O(keys · BURST), and idle keys expire.
2. **"Detect password spraying."** Group by source IP (or ASN) instead of by account, and count
   **distinct accounts** tried inside the window. A high distinct count with only one failure
   per account is spraying.
3. **"Times cross midnight."** Use full timestamps (epoch seconds), not `HH:MM`. The window
   logic stays the same once time is a single increasing number.

## 13. Related Chips
- **DC-SEC-15 Impossible Travel Detector**: the same grouping and window, comparing cities instead of counts.
- **DC-OBS-02 5-Minute Error Counter**: the live-stream version of a time window.
- **DC-OBS-09 Log Flood Suppressor**: per-key timestamps, used to suppress instead of alert.
