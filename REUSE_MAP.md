# Reuse Map (confirmed 2026-09-23)

Handbook: Capra Handbook, **Top 100** list. Index: `apps/camora/src/pages/Blind75Page.tsx`.
Content: `apps/camora/src/data/capra/top100/<id>.json` in the copilot monorepo.

Matching was done by LeetCode URL slug, which is the same as matching by LeetCode number.
Handbook IDs are **not** LeetCode numbers (handbook #23 is Remove Nth Node, but LC 23 is
handbook #24), so no match relies on the ID.

Every handbook entry has a statement, examples, constraints, hints, solutions in
Python/JS/Java/C++/Go with complexity, and about 30 JSON test cases.
Two things every REUSE chip adds, both labelled "(added)":
- `test_chip.py`: a pytest wrapper that runs the handbook's JSON cases unchanged.
- `starter.py`: the handbook builds its starter from the problem's function signature and
  does not store a starter file.

Each REUSE chip folder also holds `handbook.json`, a byte-for-byte copy of the handbook
entry (all languages, variants and tests).

| Chip ID | LC # | Status | Handbook location | Sections missing in handbook |
|---|---|---|---|---|
| DC-OBS-02 | 362 | REUSE | #102 Design Hit Counter, `top100/102.json` | 3rd hint level (Near-solution) |
| DC-OBS-03 | 239 | REUSE | #83 Sliding Window Maximum, `top100/83.json` | — |
| DC-OBS-08 | 295 | REUSE | #39 Find Median from Data Stream, `top100/39.json` | 2nd example |
| DC-OBS-14 | 23 | REUSE | #24 Merge K Sorted Lists, `top100/24.json` | — |
| DC-SEC-02 | 20 | REUSE | #16 Valid Parentheses, `top100/16.json` | — |
| DC-SEC-05 | 56 | REUSE | #61 Merge Intervals, `top100/61.json` | — |
| DC-PLAT-01 | 210 | REUSE | #96 Course Schedule II, `top100/96.json` | — |
| DC-PLAT-02 | 207 | REUSE | #45 Course Schedule, `top100/45.json` | — |
| DC-PLAT-03 | 253 | REUSE | #64 Meeting Rooms II, `top100/64.json` | — |
| DC-PLAT-04 | 621 | REUSE | #73 Task Scheduler, `top100/73.json` | — |
| DC-PLAT-06 | 146 | REUSE | #88 LRU Cache, `top100/88.json` | — |
| DC-NET-05 | 208 | REUSE | #36 Implement Trie (Prefix Tree), `top100/36.json` | 2nd example |
| DC-NET-12 | 994 | REUSE | #95 Rotting Oranges, `top100/95.json` | — |
| DC-CAP-01 | 875 | REUSE | #85 Koko Eating Bananas, `top100/85.json` | — |

All other 64 chips are **NEW**. None are LIKELY. Related handbook problems (different
LeetCode problems, so NEW) appear under each chip's Related Chips section:

| Chip | Related handbook problem |
|---|---|
| DC-OBS-04 (652) | #35 Serialize and Deserialize Binary Tree |
| DC-OBS-05 (1244) | #5 Top K Frequent Elements |
| DC-OBS-06 (1438) | #83 Sliding Window Maximum |
| DC-OBS-16 (1004) | #14 Longest Repeating Character Replacement |
| DC-SEC-04 (820), DC-SEC-17 (1032) | #36 Implement Trie, #38 Word Search II |
| DC-SEC-10 (715), DC-PLAT-15 (759) | #60 Insert Interval, #61 Merge Intervals |
| DC-PLAT-05 (433) | #97 Word Ladder |
| DC-PLAT-12 (460) | #88 LRU Cache |
| DC-REL-01 (278) | #84 Binary Search |
| DC-REL-03 (2050) | #96 Course Schedule II |
| DC-NET-07 (1319), DC-NET-13 (1971) | #47 Number of Connected Components |
| DC-NET-08 (684) | #46 Graph Valid Tree |
| DC-CAP-02 (1011), DC-CAP-03 (410) | #85 Koko Eating Bananas |

Numbering traps (handbook ID equals the chip's LC number, but it is a different problem):
LC 14, 20, 23, 44, 56, 71, 93.

**Totals: REUSE 14 · LIKELY 0 · NEW 64 (78 chips)**
