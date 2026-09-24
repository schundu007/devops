Source: New

# DC-SEC-07 · Audit Log Run-Length Compactor

## 1. Header
| | |
|---|---|
| Chip ID | DC-SEC-07 |
| Difficulty | Medium |
| Pattern | Two pointers (in place) |
| Track | Cloud Security & IAM (SEC) |
| Classic pattern | LeetCode 443 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
An audit agent on a small edge box (10.0.7.21, 64 MB of RAM) records one status character per
second: `.` for a healthy heartbeat, `W` for a write event, `!` for an auth failure. Most of the
time the buffer is long runs of `.` like `.....................W...!!!!!......`. Before each upload
over a slow cellular link, the agent squashes runs in place, in the same buffer, because it cannot
afford a second copy: `.58W.3!5.120`.

## 3. Why This Is DevOps
**Production reality:** Log and telemetry agents on small devices work in fixed buffers.
Repeated values (heartbeats, idle markers, zero readings) compress very well with run-length
encoding: store the value once, followed by how many times it repeats. Doing it in place, with a
read pointer ahead of a write pointer, means no second buffer. The same read and write pointer
technique is how compaction works in log-structured storage.

**Where you see it:** Prometheus' Gorilla-style XOR chunk encoding (repeated values take very
few bits), run-length and dictionary encoding in Parquet and ORC columns, and bitmap and image
formats. The read and write pointer compaction idea is also used in log-structured stores.

**Reality check:** Real log shippers (Fluent Bit, Vector, the OpenTelemetry Collector) compress
with gzip or zstd, not plain RLE. RLE is the simplest compression idea and teaches in-place
buffer work. Also, decimal counts are ambiguous if the data itself holds digits (`"1"` twice
becomes `"12"`), so real formats use a length byte or an escape character.

**What breaks if you get it wrong:** If the write pointer ever passes the read pointer, the
encoder overwrites events it hasn't read yet. For an audit log, that means a failed login (`!`)
silently disappears from the uploaded record, which is exactly the evidence an investigation needs.

## 4. Problem Statement
Write `compress(buf)`, where `buf` is a list of single characters.

- Split `buf` into runs of equal characters.
- Replace each run with the character, followed by the run length in decimal if the run is longer
  than 1 (`"aaa"` → `"a3"`, `"b"` → `"b"`, 12 `c`s → `"c12"`).
- Do it **in place**: write the result at the start of `buf` using O(1) extra space.
- Return the length of the result. Only `buf[:length]` matters. The rest can hold anything.

## 5. Input / Output format and Constraints
- `compress(buf: list[str]) -> int`. `buf` is changed in place.
- `0 <= len(buf) <= 2 * 10^5`. Each item is one printable ASCII character.
- Extra space: O(1) (not counting the digits of a single count).

## 6. Examples
**Example 1: runs**
```
buf = list("aabbccc")
compress(buf) -> 6        # buf[:6] == list("a2b2c3")
```

**Example 2: multi-digit count (edge case)**
```
buf = list("b" + "c" * 12)
compress(buf) -> 4        # buf[:4] == list("bc12")
```

**Example 3: nothing to squash**
```
compress(list("abc")) -> 3        # unchanged
compress([])          -> 0
```

## 7. Starter Code
See [`starter.py`](starter.py): `compress` with a docstring and type hints. The body is TODO.

```bash
make try CHIP=02-security/DC-SEC-07-audit-log-run-length-compactor
```

## 8. Hints
1. **Nudge:** You read the buffer from left to right. Can the compressed output ever get ahead of what you have read?
2. **Pattern:** Two pointers on one buffer: `read` finds the end of each run, `write` lays down the output behind it.
3. **Near-solution:** For each run: write the char, then, if the run is longer than 1, write each digit of
   `str(run)`. A run of length r needs `1 + len(str(r)) <= r` slots, so `write` never passes `read`.

## 9. Solution
**Approach**
1. `read` scans forward to find the end of the current run.
2. Write the run's character at `write`.
3. If the run is longer than 1, write the digits of its length.
4. Repeat until `read` reaches the end, then return `write`.

**Brute force:** Build a new string with `itertools.groupby` and copy it back. Time is still O(n),
but it uses O(n) extra memory, which is exactly what the edge device doesn't have.

**Optimal code:** [`solution.py`](solution.py)

```python
def compress(buf: list[str]) -> int:
    write = read = 0
    n = len(buf)
    while read < n:
        ch = buf[read]
        run_start = read
        while read < n and buf[read] == ch:
            read += 1
        buf[write] = ch
        write += 1
        run = read - run_start
        if run > 1:
            for digit in str(run):        # 1 + digits <= run, so write stays behind read
                buf[write] = digit
                write += 1
    return write
```

**Complexity**
- Time: O(n): `read` visits each character once, and `write` moves at most as far.
- Space: O(1) extra: only the pointers and the digits of one count.

## 10. Tests
[`test_chip.py`](test_chip.py) has 6 cases: normal runs, empty and single buffers, multi-digit
boundaries (9, 10, 12 and 1,000), a check that the output is never longer than the input, a
production heartbeat buffer with auth failures, and a large random check (300 random buffers
plus a long buffer of about 500,000 characters, against an independent `groupby` encoder).

## 11. Interview Talk Track
"On a small device I can't afford a second buffer, so I compress in place with two pointers.
The read pointer finds each run of equal characters, and the write pointer puts down the
character and, if the run is longer than one, its count. The important invariant is that write
never passes read: a run of length r needs 1 plus the number of digits in r slots, and that's
never more than r. So I never overwrite data I haven't read. It's one pass, O(n) time and O(1)
extra space. In a real shipper I'd use zstd, but two things carry over: in-place compaction
with a read and a write pointer, and the format question. Decimal counts are ambiguous once the
data can contain digits, so a real format needs a length byte or an escape character."

## 12. Level Up
1. **"The data can contain digits."** Use a byte-level format: `(count byte, value byte)` pairs,
   splitting runs longer than 255. Or add an escape byte before counts. Either way the decoder
   never has to guess where the data ends and the count begins.
2. **"Upload is interrupted halfway."** Compress in fixed-size blocks and put a length and a
   checksum at the start of each block. The receiver can then verify and resume per block, and a
   bad block never corrupts the rest. Audit data also needs a hash chain so a missing block is detectable.
3. **"Most lines are unique, not repeated."** RLE makes those slightly bigger or no smaller.
   Use a dictionary compressor (zstd with a trained dictionary works well on short, similar log
   lines), and keep RLE for columns that really do repeat, such as status or zero values.

## 13. Related Chips
- **DC-SEC-19 Config Comment Stripper**: another single pass that rewrites a text buffer.
- **DC-OBS-11 Metric Bucket Counter**: summarising repeated events instead of storing each one.
- **DC-SEC-05 Firewall Range Merger**: the same "grow the current group, or start a new one" loop.
