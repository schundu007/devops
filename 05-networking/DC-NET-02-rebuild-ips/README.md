Source: New

# DC-NET-02 · Rebuild IPs from Broken Logs

## 1. Header
| | |
|---|---|
| Chip ID | DC-NET-02 |
| Difficulty | Medium |
| Pattern | Backtracking |
| Track | Networking, Service Mesh & Resilience (NET) |
| Classic pattern | LeetCode 93 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
During a post-incident review, you find that a legacy log shipper on `batch-node-04` stripped
every `.` from the `client_ip` field before sending it to storage. Line 88,412 of the
suspicious session shows `client_ip=1001317`. The CMDB lists hosts `10.0.13.17` and
`100.1.31.7`, among others. Before you can tell the security team which host made the call,
you need every IPv4 address that `1001317` could have been.

## 3. Why This Is DevOps
**Production reality:** Log data gets damaged: CSV exports strip separators, a regex in a
pipeline drops punctuation, a field is truncated to digits for a numeric column. In forensics you
cannot re-run the past, so you rebuild every value the damaged field could have been and
intersect that set with what you know (the CMDB, DHCP leases, flow logs). If more than one
candidate survives, the evidence is ambiguous and the report has to say so.

**Where you see it:** log forensics in Splunk or Elasticsearch after a parser bug, joining
damaged fields against CMDB or cloud inventory exports, and incident reports that need to
state which hosts are "possible" and which are "confirmed".

**Reality check:** Real pipelines fix this upstream: keep the IP as a typed field (Elasticsearch
`ip` type, a Loki label, a Parquet string column) so it is never flattened. Rebuilding is a last
resort, and it only works because an IPv4 has at most 12 digits, so the candidate set is tiny.

**What breaks if you get it wrong:** Accept a candidate with a leading zero (`10.01.3.17`), or
miss a valid split, and the investigation names the wrong host. A clean server is re-imaged
while the one that was actually compromised keeps running.

## 4. Problem Statement
Write `restore_addresses(digits)`. `digits` is the text of an IPv4 address after its three dots
were removed. Return **every** valid IPv4 address that could produce `digits` when its dots are
removed. That means: insert exactly three dots, never reorder, add or drop a digit, and each of
the four parts must be a number from 0 to 255 with no leading zero (`"0"` on its own is fine).
Any order is fine. If the string has non-digits, or no valid address exists, return an empty list.

## 5. Input / Output format and Constraints
- Input: `digits: str`, length 0 to 20.
- Output: `list[str]` of dotted addresses, in any order, with no duplicates.
- A valid address always has 4 to 12 digits.

## 6. Examples
**Example 1: several answers**
```
restore_addresses("19216811")
-> ["1.92.168.11", "19.2.168.11", "19.21.68.11", "19.216.8.11", "19.216.81.1",
    "192.1.68.11", "192.16.8.11", "192.16.81.1", "192.168.1.1"]
```

**Example 2: zeros (edge case)**
```
restore_addresses("0000")   -> ["0.0.0.0"]
restore_addresses("010010") -> ["0.10.0.10", "0.100.1.0"]   # "01" and "010" are never parts
```

**Example 3: impossible**
```
restore_addresses("123")           -> []   # too short
restore_addresses("2552552552551") -> []   # 13 digits: too long
```

## 7. Starter Code
See [`starter.py`](starter.py): `restore_addresses(digits: str) -> list[str]` with a docstring. The body is TODO.

```bash
make try CHIP=05-networking/DC-NET-02-rebuild-ips
```

## 8. Hints
1. **Nudge:** The first part is 1, 2 or 3 digits long. Once you choose it, the rest is the same question with three parts left.
2. **Pattern:** Backtracking: choose a part, recurse on the rest, then undo the choice. Stop a branch early when the digits left cannot fill the parts left.
3. **Near-solution:** `place(start)` tries sizes 1–3. Skip a part that has a leading zero or is over 255. Prune when `remaining_chars` is not within `[parts_left, 3 * parts_left]`. With 0 parts left and 0 chars left, record the address.

## 9. Solution
**Approach**
1. Reject input that is not ASCII digits, or not 4 to 12 characters long.
2. Recurse with a start index and the list of parts chosen so far.
3. At each step, try a part of 1, 2 or 3 digits. Keep it only if it has no leading zero and is at most 255.
4. Prune when the digits left cannot fill the parts left (each part is 1–3 digits).
5. When four parts use all the digits, join them with dots and record the result.

**Brute force:** Try every choice of three dot positions (at most C(11,3) = 165 for 12 digits)
and validate each result. For IPv4 that is fine, and it is what the tests use as the reference.
Backtracking matters when the shape is open-ended (more parts, longer strings), because pruning
removes whole subtrees at once.

**Optimal code:** [`solution.py`](solution.py)

```python
def _valid_octet(s: str) -> bool:
    return 1 <= len(s) <= 3 and (s == "0" or s[0] != "0") and int(s) <= 255


def restore_addresses(digits: str) -> list[str]:
    out: list[str] = []
    if not digits.isascii() or not digits.isdigit() or not 4 <= len(digits) <= 12:
        return out
    parts: list[str] = []

    def place(start: int) -> None:
        left_parts, left_chars = 4 - len(parts), len(digits) - start
        if not left_parts <= left_chars <= 3 * left_parts:   # prune
            return
        if left_parts == 0:
            out.append(".".join(parts))
            return
        for size in (1, 2, 3):
            octet = digits[start:start + size]
            if len(octet) == size and _valid_octet(octet):
                parts.append(octet)      # choose
                place(start + size)      # explore
                parts.pop()              # un-choose

    place(0)
    return out
```

**Complexity**
- Time: O(1). The tree has at most 3⁴ = 81 leaves, and each address is at most 15 characters.
  For a general version with p parts, it is O(3ᵖ · n).
- Space: O(1) for the recursion (depth 4) plus the output, which never exceeds a few dozen addresses.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases:
- the normal `19216811` case;
- empty and too-short strings;
- the 4- and 12-digit boundaries, and 13 digits;
- no leading zeros in any output;
- non-digit input;
- a production-style CMDB match with two surviving candidates;
- 3,000 random strings checked against an independent brute force that validates with Python's `ipaddress`.

## 11. Interview Talk Track
"A log shipper dropped the dots from client IPs, and I need every address the digits could
have been, so I can match them against inventory. An IPv4 is four parts, each one to three
digits, from 0 to 255, with no leading zero. I backtrack: choose the next part's length,
check the part, recurse, then undo. The key pruning is that the digits left must fit the parts
left, between one and three digits each, which cuts dead branches immediately. The tree has at
most 81 leaves, so it's constant time. In the report, if more than one candidate matches a real
host, I say the evidence is ambiguous instead of picking one. And the real fix is upstream:
store IPs as a typed field so this never happens."

## 12. Level Up
1. **"The field lost its colons too: rebuild IPv6."** Up to 32 hex digits split into 8 groups
   of 1–4 creates a huge number of candidates, and without `::` rules it is almost always
   ambiguous. Filter by known prefixes first (your VPC's `/56`), which fixes the first
   groups and shrinks the search.
2. **"Run this over 50 million damaged log lines."** Do not rebuild per line. Group by the
   damaged value first, since many lines share a client, compute candidates once per distinct
   value, and join against the inventory as a hash set. It is a map-reduce job, not a loop.
3. **"Some lines also lost a digit."** Now the search space includes insertions. Rank candidates
   by edit distance to known inventory IPs (DP, as in edit distance) instead of listing
   everything, and report confidence, not a single answer.

## 13. Related Chips
- **DC-NET-01 IP Address Validator**: the same octet rules, used to check one string.
- **DC-SEC-14 Identity Linker**: another forensics join, merging records that refer to the same entity.
- **DC-SEC-09 IP Range to CIDR Blocks**: IPv4 as numbers and bit ranges instead of strings.
