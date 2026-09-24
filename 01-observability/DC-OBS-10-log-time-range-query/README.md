Source: New

# DC-OBS-10 · Log Time-Range Query

## 1. Header
| | |
|---|---|
| Chip ID | DC-OBS-10 |
| Difficulty | Medium |
| Pattern | Timestamp truncation + range scan |
| Track | Observability & SRE (OBS) |
| Classic pattern | LeetCode 635 |
| Premium | Yes (P). Free alternative: LeetCode 981 Time Based Key-Value Store (Medium): the same sorted-timestamps-plus-binary-search idea (also chip DC-OBS-01). |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
The New Year's Eve incident on `billing-api` began at about 23:00 on 31 December and ended
shortly before 01:00 on 1 January. For the review you need every log line from "23:00 to
00:59, at minute detail". Later the team lead asks for "everything on the 23rd" (day detail)
and then "all of last year" (year detail). Each log line has an ID and a timestamp written as
`YYYY:MM:DD:hh:mm:ss`, for example `2025:12:31:23:30:00`.

## 3. Why This Is DevOps
**Production reality:** Almost every log question starts with a time range, picked at some
level of detail: "this minute", "this hour", "yesterday". The time picker in a log tool turns
that into a start and an end, and the store returns the lines in between. Timestamps with
fixed-width, zero-padded fields sort as text in the same order as in time, so "cut to the hour"
is just "keep the first 13 characters", and a range query becomes two binary searches over sorted data.

**Where you see it:** the time picker in Grafana Explore and in Kibana, Loki (log chunks are
indexed by time, so a query only reads chunks that overlap the range), Elasticsearch time-based
indices and data streams, and CloudWatch Logs Insights.

**Reality check:** Loki and Elasticsearch never scan everything: data is partitioned by time,
and a query first skips every chunk, index or shard whose time span does not overlap the range.
Then it filters inside. Real systems store epoch timestamps with time zones, not local strings.
This chip is the single-node version: one sorted list, two binary searches.

**What breaks if you get it wrong:** An off-by-one at the end of the range drops the last
minute of the incident, which is often the minute where the fix landed. A text compare
without zero-padding puts `2026:9:…` after `2026:10:…`, and the query returns the wrong month.

## 4. Problem Statement
Build a `LogStore`.

- `put(log_id, timestamp)`: store a log line's ID with its timestamp `YYYY:MM:DD:hh:mm:ss`.
  Every field is zero-padded.
- `retrieve(start, end, granularity)`: return the IDs of all logs whose timestamp lies between
  `start` and `end`, inclusive, **comparing only the fields down to `granularity`**. `granularity`
  is one of `Year`, `Month`, `Day`, `Hour`, `Minute`, `Second`. Finer fields are ignored, on
  `start`, on `end` and on the logs. Return the IDs in ascending order.

## 5. Input / Output format and Constraints
- `log_id: int`, unique, `0 <= log_id <= 10^9`.
- Timestamps are valid, zero-padded `YYYY:MM:DD:hh:mm:ss` strings with years 2000–2099.
- `start <= end` when both are cut to `granularity`.
- Up to `10^5` calls to `put` and `retrieve` combined. Returns `list[int]`.

## 6. Examples
Logs: `1 → 2026:09:23:02:14:05`, `2 → 2026:09:23:02:59:59`, `3 → 2026:09:22:23:00:00`,
`4 → 2025:12:31:23:59:59`.

**Example 1: one hour**
```
retrieve("2026:09:23:02:00:00", "2026:09:23:02:00:00", "Hour") -> [1, 2]
```
At hour detail, `start` and `end` both mean "02:xx on the 23rd", so both 02:14 and 02:59 match.

**Example 2: finer fields are ignored**
```
retrieve("2026:09:22:23:59:59", "2026:09:23:00:00:00", "Day") -> [1, 2, 3]
```
At day detail this means "the 22nd through the 23rd". The 23:00 log on the 22nd is included,
even though it is earlier than 23:59:59.

**Example 3: exact seconds (edge case)**
```
retrieve("2026:09:23:02:14:06", "2026:09:23:02:59:58", "Second") -> []
```
Log 1 is one second before the start and log 2 is one second after the end.

## 7. Starter Code
See [`starter.py`](starter.py): `LogStore` with `put` and `retrieve` signatures, docstrings
and type hints. Bodies are TODO.

```bash
make try CHIP=01-observability/DC-OBS-10-log-time-range-query
```

## 8. Hints
1. **Nudge:** Compare `"2026:09:23"` and `"2026:10:01"` as plain strings. Does text order match
   time order here? Why?
2. **Pattern:** Truncate to a prefix length (Year = 4, Month = 7, Day = 10, Hour = 13,
   Minute = 16, Second = 19 characters), then do a range scan. Keep the logs sorted by timestamp
   so the scan can start with a binary search.
3. **Near-solution:** The lowest timestamp inside the range is `start[:n]`, and the highest is
   `end[:n]` followed by anything. `bisect_left` for `start[:n]`, and `bisect_right` for
   `end[:n] + "~"` (`~` sorts after every digit and `:`), then slice.

## 9. Solution
**Approach**
1. Keep a list of `(timestamp, log_id)` sorted by timestamp.
2. For a query, take the prefix length `n` for the granularity.
3. The lower bound is `start[:n]`: every timestamp with that prefix or later sorts at or after it.
4. The upper bound is `end[:n] + "~"`: every timestamp with `end`'s prefix sorts before it.
5. Two binary searches find the slice. Return its IDs sorted.

**Brute force:** Check every stored log against the cut `start` and `end` on every query:
O(n) per query, even when the answer is a handful of lines from one minute out of a year.

**Optimal code:** [`solution.py`](solution.py)

```python
from bisect import bisect_left, bisect_right, insort

_PREFIX_LEN = {"Year": 4, "Month": 7, "Day": 10, "Hour": 13, "Minute": 16, "Second": 19}


class LogStore:
    def __init__(self) -> None:
        self._entries: list[tuple[str, int]] = []   # (timestamp, id), sorted

    def put(self, log_id: int, timestamp: str) -> None:
        insort(self._entries, (timestamp, log_id))

    def retrieve(self, start: str, end: str, granularity: str) -> list[int]:
        n = _PREFIX_LEN[granularity]
        lo = (start[:n], -1)              # smallest possible key with start's prefix
        hi = (end[:n] + "~", -1)          # above every key with end's prefix
        i = bisect_left(self._entries, lo)
        j = bisect_right(self._entries, hi)
        return sorted(log_id for _, log_id in self._entries[i:j])
```

**Complexity**
- Time: `retrieve` is O(log n + m log m) for m results: two binary searches, then sorting the
  IDs. `put` is O(n) because a Python list insert shifts elements. Logs mostly arrive in time
  order, so in practice it is an append.
- Space: O(n) for the stored entries.

## 10. Tests
[`test_chip.py`](test_chip.py) has 6 cases: an hour range, an empty store, day and year
granularity ignoring finer fields, inclusive second boundaries, a production-style incident
window across midnight and a year end, and 20,000 random logs with 200 random queries checked
against a brute force that compares integer fields.

## 11. Interview Talk Track
"This is the time picker in any log tool. Timestamps are fixed-width and zero-padded, so their
text order is their time order, and granularity is just a prefix length: 13 characters for
the hour, 16 for the minute. I keep the logs sorted by timestamp. For a query, the lowest
matching key is the start's prefix, and the highest is the end's prefix followed by a
character that sorts above any digit. Two binary searches give me the slice, so a query is
O(log n) plus the results. Loki and Elasticsearch apply the same idea one level up: data is split
into chunks or indices by time, and a query first skips everything that can't overlap the range,
then filters inside the few that can."

## 12. Level Up
1. **"A billion lines a day, and inserts are O(n)."** Don't keep one list. Append to the
   current chunk (logs arrive nearly in time order), seal it every few minutes or megabytes, and
   record each chunk's min and max time in a small index. A query picks the chunks that overlap,
   then binary searches inside them. This is the Loki idea.
2. **"Also filter by service and level."** Add label indexes: a map from each label value to
   its chunk IDs. Intersect the label matches with the time-overlapping chunks before reading any
   data, which is why Loki asks you to keep labels low-cardinality.
3. **"Logs arrive from 30 time zones and some are 2 minutes late."** Store UTC epoch
   milliseconds, not local strings, and convert only for display. Accept late lines into a
   still-open chunk, or into a small out-of-order buffer that is merged later.

## 13. Related Chips
- **DC-OBS-01 Metric Point-in-Time Lookup**: a single time instead of a range.
- **DC-OBS-11 Metric Bucket Counter**: count per minute, hour or day instead of listing lines.
- **DC-OBS-14 Multi-Node Log Timeline Merge**: merge the per-node results into one timeline.
