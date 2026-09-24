Source: New

# DC-SEC-15 · Impossible Travel Detector ★

## 1. Header
| | |
|---|---|
| Chip ID | DC-SEC-15 |
| Difficulty | Medium |
| Start here | ★ |
| Pattern | Sort + group by user |
| Track | Cloud Security & IAM (SEC) |
| Classic pattern | LeetCode 1169 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
The service account `svc-deploy` signs in to the cloud console from a Frankfurt address at
minute 660 of the day, then from a São Paulo address at minute 685. Nobody travels 9,800 km
in 25 minutes. The same day, a user `jo` downloads a data export with a risk score of 1,500,
far above the 1,000 limit. The security-events pipeline has to flag both kinds of event and
leave the thousands of normal sign-ins alone.

## 3. Why This Is DevOps
**Production reality:** Identity threat detection looks at sign-in and API events per user.
Two events from different cities too close together in time cannot both be the real person,
so one is probably a stolen session or credential. That is an "impossible travel" alert. Events
whose own risk score is over a limit are flagged on their own. The engine groups events by user,
orders them by time, and checks each event against its neighbours inside the time window.

**Where you see it:** Microsoft Entra ID Protection ("atypical travel"), Okta ThreatInsight
and behaviour detection, Google Workspace suspicious-login alerts, AWS GuardDuty findings for
unusual console sign-ins, SIEM correlation rules.

**Reality check:** Real tools compute the distance between geo-located IPs and the speed needed
to cover it, and they learn each user's normal locations and VPN exits. A fixed "different city
within 60 minutes" rule is the simple version, and it is noisy for people who use VPNs.

**What breaks if you get it wrong:** Compare only *consecutive* events and you miss the case
where a third event sits between the two cities. Get the window edge wrong (60 vs 61 minutes)
and a real session hijack slips through, or the SOC drowns in false alerts and starts ignoring them.

## 4. Problem Statement
You get a list of events, each a string `"user,minute,risk,city"`. An event is **suspicious** if:
- its `risk` is greater than 1,000, or
- the same user has at least one other event in a **different** city whose `minute` is within
  60 of this event's minute (a difference of 60 counts).

Return every suspicious event, in the order they appear in the input. If the same string
appears twice and is suspicious, return it twice.

## 5. Input / Output format and Constraints
- `flag_events(events: list[str]) -> list[str]`
- `0 <= len(events) <= 10^4`
- `user` and `city`: 1–10 lowercase letters or `-`. `0 <= minute <= 10^4`. `0 <= risk <= 2000`.
- No field contains a comma.

## 6. Examples
**Example 1: two cities, 30 minutes apart**
```
["ana,20,100,berlin", "ana,50,100,tokyo"]  ->  both events
```

**Example 2: the window edge (edge case)**
```
["ana,0,1,berlin", "ana,60,1,tokyo"]  ->  both   (difference 60 counts)
["ana,0,1,berlin", "ana,61,1,tokyo"]  ->  []
```

**Example 3: risk alone**
```
["bo,5,1001,oslo", "bo,6,1000,oslo"]  ->  ["bo,5,1001,oslo"]
```
Exactly 1,000 is not over the limit.

## 7. Starter Code
See [`starter.py`](starter.py): `flag_events(events)` with a docstring, type hints and the two limits as constants.

```bash
make try CHIP=02-security/DC-SEC-15-impossible-travel
```

## 8. Hints
1. **Nudge:** An event can only be affected by events of the same user. How should you split the input?
2. **Pattern:** Group by user and sort each group by minute. Then every event's "neighbours
   within 60 minutes" form a contiguous run that you can track with two pointers.
3. **Near-solution:** For each event at time t, move the right pointer while `minute <= t + 60`
   and the left pointer while `minute < t - 60`, keeping a city `Counter` of the window. If the
   window holds 2 or more distinct cities, flag the event. Finally, add events with risk over 1,000.

## 9. Solution
**Approach**
1. Parse every event. Group event indexes by user.
2. Sort each user's events by minute.
3. Slide a window `[t - 60, t + 60]` across them with two pointers, counting cities in the window.
4. The event itself is inside its own window, so two or more distinct cities means another
   city is close enough. Flag it.
5. Return the flagged events and the high-risk events, in input order.

**Brute force:** Compare every pair of events: O(n²). At 10,000 events per user per day that is
100 million comparisons for each rule run.

**Optimal code:** [`solution.py`](solution.py) (key part)

```python
for i in idxs:                                   # one user's events, sorted by minute
    t = parsed[i][1]
    while hi < len(idxs) and parsed[idxs[hi]][1] <= t + 60:
        cities[parsed[idxs[hi]][3]] += 1; hi += 1
    while parsed[idxs[lo]][1] < t - 60:
        c = parsed[idxs[lo]][3]; cities[c] -= 1
        if cities[c] == 0: del cities[c]
        lo += 1
    if len(cities) > 1:                          # another city inside the window
        flagged[i] = True
```

**Complexity**
- Time: O(n log n), because sorting within each user dominates. Each pointer moves at most n steps.
- Space: O(n) for the parsed events, groups and flags.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: two cities close together, empty and single, the
inclusive 60-minute boundary, risk alone, same-city and other-user events that must not trigger,
a production VPN sign-in burst, and 1,500 random events checked against an all-pairs brute force.

## 11. Interview Talk Track
"This is an impossible-travel rule. Two rules really: a per-event risk limit, and 'same user,
different city, within 60 minutes'. The second only compares events of one user, so I group by
user and sort by time. Then the events within 60 minutes of any event are a contiguous run, and
I track it with two pointers and a count of cities. If the window holds more than one city, the
event is suspicious. That's O(n log n) instead of all pairs. Two details matter: the edge is
inclusive, and I must look both backward and forward in time, not just at the previous event. Real
detectors use geo distance and travel speed and learn each user's VPN exits, but the grouping
and windowing are the same."

## 12. Level Up
1. **"Use real speed, not 'different city'."** Store each event's latitude and longitude. For
   neighbouring events, compute the distance divided by the time and flag anything faster than
   about 1,000 km/h. Only nearby events in time matter, so the same window logic still applies.
2. **"Events arrive as a stream, possibly a few minutes late."** Keep per-user events for the
   last 60 minutes plus the allowed lateness. When an event arrives, check it against that buffer.
   Emit alerts after the lateness has passed, so late events can still pair up.
3. **"False alerts from corporate VPN exits."** Keep an allow-list of known egress IP ranges and
   treat them as "location unknown" rather than as a city. Also learn each user's usual location
   pairs and lower the score for pairs they use every week.

## 13. Related Chips
- **DC-SEC-16 Brute-Force Burst Alert**: the same group-by-user and sliding window, counting uses.
- **DC-OBS-02 5-Minute Error Counter**: a time window that expires from the front.
- **DC-SEC-14 Identity Linker**: first merge accounts, then run detection per real person.
