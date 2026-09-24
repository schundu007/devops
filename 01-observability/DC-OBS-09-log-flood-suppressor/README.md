Source: New

# DC-OBS-09 · Log Flood Suppressor

## 1. Header
| | |
|---|---|
| Chip ID | DC-OBS-09 |
| Difficulty | Easy |
| Pattern | Hash map + timestamps |
| Track | Observability & SRE (OBS) |
| Classic pattern | LeetCode 359 |
| Premium | Yes (P). Free alternative: LeetCode 1797 Design Authentication Manager (Medium): a hash map of expiry times, checked against the current time (also chip DC-SEC-18). |
| Time box | 15 min |
| Source | New |

## 2. The Scenario
At 04:12 the primary Postgres at `10.0.12.7` restarts. Every pod of `api` retries its connection
in a tight loop, and each retry logs `dial tcp 10.0.12.7:5432: connect: connection refused`.
Within a second, pod `api-6f7c9-lq2xd` has written 5,000 identical lines. The log shipper falls
behind, and the one line that matters (`OOMKilled: container api`) is buried. You add a
suppressor in front of the shipper: the same message prints at most once every 10 seconds.

## 3. Why This Is DevOps
**Production reality:** One failing dependency can make every client log the same error
thousands of times per second. That floods the log pipeline, costs money per GB ingested, and
hides different errors. Log agents and alert routers therefore remember when each message
(or alert) was last sent and drop repeats inside a quiet period. It's a hash map from message
to "next time it is allowed". It must stay cheap, because it runs on every single line.

**Where you see it:** rsyslog's repeated-message reduction ("last message repeated N times"),
journald rate limits (`RateLimitIntervalSec`, `RateLimitBurst`), the Fluent Bit throttle filter,
Kubernetes event aggregation (repeats increase a `count` instead of creating new events), and
Alertmanager's `repeat_interval`, which is similar in spirit.

**Reality check:** Real tools often rate-limit by *source* (a service or container), not by
exact message text, and they usually emit a summary such as "suppressed 4,999 messages" so
the loss is visible. Alertmanager's `repeat_interval` controls re-notification for an alert
that is still firing, which is related but not identical. This chip is the exact-text, per-message version.

**What breaks if you get it wrong:** If suppressed calls reset the timer, a message that
repeats every second never prints again, and a live outage goes silent in the logs. If the
map never forgets old messages, the agent's memory grows until the agent itself is OOM-killed.

## 4. Problem Statement
Build `LogSuppressor(window=10)` with one method, `should_print(timestamp, message)`.

- Return `True` if this exact `message` has not been **printed** in the last `window` seconds,
  and remember that it was printed at `timestamp`.
- Otherwise return `False`. A suppressed call does **not** count as a print, so it does not
  restart the quiet period.
- A message printed at time `t` may print again at `t + window` or later.
- Calls arrive with non-decreasing timestamps. Many calls may share one second.

## 5. Input / Output format and Constraints
- `window: int`, `1 <= window <= 3600`.
- `timestamp: int`, `0 <= timestamp <= 2 * 10^9`, non-decreasing across calls.
- `message: str`, `1 <= len <= 1,000`.
- Up to `10^5` calls. Returns `bool`.

## 6. Examples
**Example 1**
```
LogSuppressor(window=10)
should_print(1,  "db timeout")  -> True
should_print(2,  "cache miss")  -> True
should_print(3,  "db timeout")  -> False   # printed at 1; allowed again at 11
should_print(10, "db timeout")  -> False
should_print(11, "db timeout")  -> True
```

**Example 2: suppression does not extend the quiet period (edge case)**
```
"retrying upstream" logged every second from t=0 to t=34, window=10
printed at: 0, 10, 20, 30
```
If suppressed calls reset the timer, it would print only at 0.

**Example 3: same-second burst**
```
5,000 calls at t=1700000000 with the same message -> exactly one True
```

## 7. Starter Code
See [`starter.py`](starter.py): `LogSuppressor` with `__init__(window)` and
`should_print(timestamp, message)`, docstrings and type hints. Bodies are TODO.

```bash
make try CHIP=01-observability/DC-OBS-09-log-flood-suppressor
```

## 8. Hints
1. **Nudge:** For each message, what is the single number you need to remember?
2. **Pattern:** A hash map from message to a timestamp. Checking and updating it is O(1).
3. **Near-solution:** Store `next_allowed[message] = t + window` only when you print. Print if
   the message is new or `t >= next_allowed[message]`.

## 9. Solution
**Approach**
1. Keep `next_allowed: dict[message, int]`.
2. On a call, if `timestamp < next_allowed[message]`, return `False` and change nothing.
3. Otherwise set `next_allowed[message] = timestamp + window` and return `True`.

**Brute force:** Keep a list of every printed `(timestamp, message)` and scan back through the
last `window` seconds on each call. During a flood that list holds thousands of lines per
second, and every call scans it.

**Optimal code:** [`solution.py`](solution.py)

```python
class LogSuppressor:
    def __init__(self, window: int = 10) -> None:
        self.window = window
        self._next_allowed: dict[str, int] = {}   # message -> earliest next print

    def should_print(self, timestamp: int, message: str) -> bool:
        if timestamp < self._next_allowed.get(message, timestamp):
            return False                          # suppressed: timer unchanged
        self._next_allowed[message] = timestamp + self.window
        return True
```

**Complexity**
- Time: O(1) average per call (one hash lookup and at most one write), plus O(L) to hash a message of length L.
- Space: O(m), where m is the number of distinct messages ever seen. Level Up 1 shows how to bound it.

## 10. Tests
[`test_chip.py`](test_chip.py) has 6 cases: a normal mixed sequence, the first message, the
exact window edge (109 suppressed, 110 printed), suppression not extending the quiet period,
a production-style 5,000-line same-second burst mixed with an OOM line, and 100,000 random
calls checked against an independent last-print reference.

## 11. Interview Talk Track
"A database restart makes every pod log the same 'connection refused' thousands of times a
second, which floods the pipeline and hides the one error that matters. The fix is a
suppressor in the agent: per message, I store the earliest time it may print again. A call
checks the map. If it's too early I drop the line; otherwise I print and set the next time to
now plus the window. It's one hash lookup, O(1), which matters because it runs on every line.
Two details matter. Suppressed lines must not reset the timer, or a constant error goes silent.
And the map must be bounded: in production I'd evict entries older than the window, and I'd
emit a 'suppressed N lines' summary so we don't lose the fact that it was flooding."

## 12. Level Up
1. **"The agent has run for 30 days and the map holds 40 million one-off messages."** Entries
   older than the window are useless. Also keep a queue of `(next_allowed, message)` in time
   order, and on each call pop and delete the expired entries from the front. Memory is now
   bounded by the messages seen in the last `window` seconds.
2. **"Messages differ only by a request ID, so nothing is ever suppressed."** Normalise before
   keying: replace numbers, UUIDs and IPs with placeholders (`connect to <ip>:<port> refused`).
   Log pattern tools such as Loki's pattern detection group lines in a similar way.
3. **"Allow 5 per window, not 1, and report how many were dropped."** Store `(window_start,
   count, dropped)` per message: a fixed-window counter. When a window closes with `dropped > 0`,
   emit one line saying "suppressed N repeats of …". This is close to journald's burst limit.

## 13. Related Chips
- **DC-OBS-02 5-Minute Error Counter**: counting events in a time window instead of dropping them.
- **DC-SEC-18 Session Token Manager**: the same hash map of expiry times, for tokens.
- **DC-SEC-16 Brute-Force Burst Alert**: repeated events per user within one hour.
