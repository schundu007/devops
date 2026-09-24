Source: New

# DC-SEC-17 · Streaming Secret Scanner

## 1. Header
| | |
|---|---|
| Chip ID | DC-SEC-17 |
| Difficulty | Hard |
| Pattern | Reverse trie |
| Track | Cloud Security & IAM (SEC) |
| Classic pattern | LeetCode 1032 |
| Premium | No |
| Time box | 40 min |
| Source | New |

## 2. The Scenario
The CI job `build-api #4471` streams its log to the log collector one character at a time as
the runner prints it. Somewhere in step 3, a script echoes `AWS_KEY=AKIAFAKE123`. The log
collector has a list of known credential prefixes (all fake here: `AKIAFAKE`, `ghp_FAKE`,
`-----BEGIN FAKE KEY`). It must raise a flag **the moment** a prefix completes, so it can mask
the line before anything reaches long-term storage, with no waiting for the line or the job to finish.

## 3. Why This Is DevOps
**Production reality:** Secrets leak into build logs, chat messages and container output
all the time. Log shippers and CI systems try to catch them *as the text flows*, before it
is stored or shown in the UI. That means checking many known patterns against a character
stream and reacting when one ends at the latest character. Keeping the patterns in a reverse trie
turns each new character into one short walk backward, instead of re-checking every pattern.

**Where you see it:** GitHub Actions secret masking in logs, GitLab CI masked variables,
GitHub push protection and secret scanning, gitleaks and trufflehog in pre-commit and CI hooks,
IDS engines such as Suricata and Snort matching many byte patterns in network traffic.

**Reality check:** Tools like gitleaks use **regex rules** (plus entropy checks), not fixed
strings, and they usually scan whole files or commits, not one character at a time. IDS engines
that must match thousands of fixed patterns at line rate use multi-pattern algorithms such as
**Aho-Corasick**, which moves forward one state per character. The reverse trie in this chip is a
simpler way to get the same "a pattern just ended here" signal.

**What breaks if you get it wrong:** If the scanner checks only complete lines, a key printed
without a newline (for example inside a progress bar) is never masked. It lands in the
build log, which 300 engineers can read, and the key has to be rotated.

## 4. Problem Statement
Build a `SecretScanner` from a list of fixed patterns. Then characters arrive one at a time
through `feed(ch)`. After each character, return `True` if some pattern exactly equals the
text that ends at this character (a suffix of everything fed so far), otherwise `False`.

## 5. Input / Output format and Constraints
- `SecretScanner(patterns: list[str])`, then `feed(ch: str) -> bool` with `len(ch) == 1`.
- `1 <= len(patterns) <= 2000`, each pattern has `1 <= length <= 200` printable ASCII characters.
- Up to `4 * 10^4` calls to `feed`.

## 6. Examples
**Example 1: a match on the pattern's last character**
```
patterns = ["key"]; feed each of "a key"
-> [False, False, False, False, True]
```

**Example 2: overlapping patterns**
```
patterns = ["abc", "bc", "ab"]; feed "a", "b", "c"
-> [False, True, True]
```
"ab" ends at `b`; both "bc" and "abc" end at `c`.

**Example 3: not yet complete (edge case)**
```
patterns = ["token"]; feed "t","o","k","e"  ->  [False, False, False, False]
```

## 7. Starter Code
See [`starter.py`](starter.py): the `SecretScanner` class with `__init__` and `feed`, docstrings and type hints.

```bash
make try CHIP=02-security/DC-SEC-17-streaming-secret-scanner
```

## 8. Hints
1. **Nudge:** Every match you care about *ends* at the newest character. Which direction should you read the stream in?
2. **Pattern:** Store the patterns reversed in a trie. Walk it from the newest character backward
   and stop at the first node that marks the end of a pattern.
3. **Near-solution:** Keep only the last `max_len` characters in a `deque(maxlen=max_len)`. On
   `feed`, append the character, then walk the trie with `reversed(deque)`. Return `True` at an end
   marker, and `False` when the walk falls off the trie.

## 9. Solution
**Approach**
1. Insert every pattern **reversed** into a trie. Mark the node where each pattern ends.
2. Keep a bounded buffer of the last `L` characters, where `L` is the longest pattern length.
3. On each `feed`, append the character and walk the trie from the newest character toward older ones.
4. Reaching an end marker means a pattern ends here. Falling off the trie means no pattern can.

**Brute force:** After each character, check `stream.endswith(p)` for every pattern: O(P · L)
per character. With 2,000 patterns of 200 characters, that is 400,000 character comparisons per
character of log.

**Optimal code:** [`solution.py`](solution.py)

```python
class SecretScanner:
    def __init__(self, patterns: list[str]) -> None:
        self.root: dict = {}
        for p in patterns:
            node = self.root
            for ch in reversed(p):            # store backwards
                node = node.setdefault(ch, {})
            node[_END] = True
        self.recent = deque(maxlen=max(map(len, patterns)))

    def feed(self, ch: str) -> bool:
        self.recent.append(ch)
        node = self.root
        for c in reversed(self.recent):      # newest character first
            node = node.get(c)
            if node is None:
                return False
            if _END in node:
                return True
        return False
```

**Complexity**
- Time: building is O(total pattern length). Each `feed` is O(L), where L is the longest
  pattern, and usually much less because the walk stops early.
- Space: O(total pattern length) for the trie, plus O(L) for the buffer.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: a match at the last character, a single-character
pattern, overlapping and nested patterns, "not yet complete", a first character plus a long
quiet stream, a production CI log with fake credential prefixes, and 20,000 random characters
checked against an `endswith` brute force.

## 11. Interview Talk Track
"The scanner has to flag a secret the moment its last character arrives, before the log is
stored. Every match ends at the newest character, so I store the patterns reversed in a trie
and walk it backward from that character. Stop at an end marker: match. Fall off: no match.
I only need the last L characters, L being the longest pattern, so a bounded deque holds the
buffer. Each character costs O(L) at worst and usually much less. In production, gitleaks-style
tools use regex rules with entropy checks, and high-speed engines use Aho-Corasick, which does
O(1) amortised work per character with failure links. The reverse trie is the simplest correct version."

## 12. Level Up
1. **"Make it O(1) per character."** Build an Aho-Corasick automaton: a forward trie plus
   failure links that say where to continue when the next character doesn't match. Each
   character moves one state, and every state knows whether some pattern ends there.
2. **"Patterns are regexes, like `AKIA[0-9A-Z]{16}`."** Compile them into one combined
   automaton (a DFA, as Hyperscan and RE2 sets do), or keep a fixed-string prefix like `AKIA`
   from each regex as a cheap filter and only run the full regex on lines that hit it.
3. **"Mask the secret, don't just detect it."** When a match is found, the buffered characters
   of the match are still in the deque. Hold output back by L characters, so a match found at
   position i can still be replaced by `***` before it is written.

## 13. Related Chips
- **DC-SEC-04 Domain Suffix Compactor**: the other reverse-trie chip, compacting shared suffixes.
- **DC-NET-05 Route Prefix Trie**: a forward trie for prefix routing.
- **DC-SEC-19 Config Comment Stripper**: another character-by-character state machine.
