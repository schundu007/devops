Source: New

# DC-SEC-14 · Identity Linker

## 1. Header
| | |
|---|---|
| Chip ID | DC-SEC-14 |
| Difficulty | Medium |
| Pattern | Union-find |
| Track | Cloud Security & IAM (SEC) |
| Classic pattern | LeetCode 721 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
Dana leaves the company on Friday. The offboarding script disables `dana@acme.example` in
Okta, but the AWS SSO export lists Dana under `dana@acme.example` **and**
`dana.ops@acme.example`, and GitHub knows the account only as `dana-dev@users.example`,
linked through `dana.ops@acme.example`. Nobody connected the three. The quarterly access
review needs one row per real person listing every email they use, so offboarding catches all of them.

## 3. Why This Is DevOps
**Production reality:** One person ends up with accounts in many systems: the identity
provider, cloud consoles, Git hosting, on-call tools. Each export lists an account with one or
more emails, and accounts that share an email belong to the same person, even through a
chain of accounts. Identity governance tools merge these into one identity so access reviews,
offboarding and "who can reach production?" questions cover every account.

**Where you see it:** identity governance tools (for example SailPoint and Okta Identity
Governance), SCIM provisioning from an identity provider to SaaS apps, AWS IAM Identity Center,
GitHub Enterprise SSO linking.

**Reality check:** Real matching also uses employee IDs, SSO subject IDs and fuzzy name
matching, and emails get reused after people leave. Linking two people by a recycled shared
mailbox (such as `oncall@`) is a real mistake that tools guard against with exclusion lists.

**What breaks if you get it wrong:** You disable Dana's Okta account but miss the GitHub
account linked only through the ops email. Three months later a personal access token on that
forgotten account pushes to a production repo.

## 4. Problem Statement
Each entry of `accounts` is `[name, email1, email2, ...]`: one account, found in some system.
Two accounts belong to the same person if they share at least one email, directly or through a
chain of other accounts. Accounts of the same person always carry the same name, but two
different people can share a name.

Return one row per person: `[name, *emails]` with the emails sorted ascending and each listed
once. Sort the rows by `(name, first email)`.

## 5. Input / Output format and Constraints
- `link_identities(accounts: list[list[str]]) -> list[list[str]]`
- `1 <= len(accounts) <= 1000`, each account has `1 <= emails <= 10`.
- Names are 1–30 lowercase letters. Emails are up to 30 characters.
- An email can appear more than once, even inside one account.

## 6. Examples
**Example 1: a shared email merges two accounts**
```
[["priya", "priya@corp.example", "p.shah@corp.example"],
 ["priya", "priya@corp.example", "priya-gh@users.example"],
 ["tom", "tom@corp.example"]]
-> [["priya", "p.shah@corp.example", "priya-gh@users.example", "priya@corp.example"],
    ["tom", "tom@corp.example"]]
```

**Example 2: same name, different people (edge case)**
```
[["alex", "alex1@corp.example"], ["alex", "alex2@corp.example"]]
-> [["alex", "alex1@corp.example"], ["alex", "alex2@corp.example"]]
```
No shared email, so they stay separate.

**Example 3: a chain**
```
[["kim", "a@x", "b@x"], ["kim", "c@x", "d@x"], ["kim", "b@x", "c@x"]]
-> [["kim", "a@x", "b@x", "c@x", "d@x"]]
```
The first two accounts share nothing, but the third links them.

## 7. Starter Code
See [`starter.py`](starter.py): `link_identities(accounts)` with a docstring and type hints.

```bash
make try CHIP=02-security/DC-SEC-14-identity-linker
```

## 8. Hints
1. **Nudge:** Think of emails as the dots. What does one account say about the dots it lists?
2. **Pattern:** "Merge groups that share a member" is union-find. Union all emails inside each account.
3. **Near-solution:** For each account, union every email with its first email and remember
   `email -> name`. Then group emails by `find(email)`, sort each group, put the name in front,
   and sort the rows.

## 9. Solution
**Approach**
1. Union-find keyed by email.
2. For each account, link all its emails to the account's first email and record each email's name.
3. Group every email by its root.
4. Each group becomes `[name, *sorted emails]`. Sort the rows by `(name, first email)`.

**Brute force:** Keep a list of email sets and repeatedly merge any two sets that overlap
until none do. Each merge pass is O(g²) set checks, and there can be g passes: O(g³) for g accounts.

**Optimal code:** [`solution.py`](solution.py) (key part)

```python
for name, *emails in accounts:
    for email in emails:
        parent.setdefault(email, email)
        owner[email] = name
    root = find(emails[0])
    for email in emails[1:]:
        other = find(email)
        if other != root:
            parent[other] = root          # same account -> same person
```

**Complexity**
- Time: O(E · α(E) + E log E), because each of E emails is unioned once, then groups are sorted.
- Space: O(E) for the parent and owner maps.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: a merge through a shared email, a single account, same
name with different people, a transitive chain, a duplicate email inside one account, a production
offboarding case across Okta, AWS SSO and GitHub, and random account sets checked against a
merge-until-stable brute force.

## 11. Interview Talk Track
"For offboarding, I need one identity per person across every system. Each account lists
emails, and any shared email means the same person, even through a chain. That's union-find:
emails are the elements, and each account unions its emails together. Then I group by root, sort
emails, and attach the name. It's near-linear in the number of emails. I key on email, not
name, because two different Alexes must not merge. In production I'd add employee and SSO
subject IDs as stronger keys, and block shared mailboxes like on-call aliases from linking
unrelated people."

## 12. Level Up
1. **"New accounts arrive every minute from SCIM."** Union-find is naturally incremental:
   add the new account's emails and union them. Merges are cheap. *Splits* (an email was
   wrongly shared) are not, so keep the raw account list and rebuild when a link is revoked.
2. **"A shared `oncall@` mailbox merges 40 people into one."** Keep a deny-list of shared
   addresses that never act as links. Also flag any group that grows past a size limit for
   human review, because one person rarely has 20 emails.
3. **"Names differ across systems (`Dana K.` vs `dana`)."** Pick the name from the system of
   record, the HR system or the identity provider, and only use emails and IDs for linking. Never
   link on names alone.

## 13. Related Chips
- **DC-SEC-13 Secret Exposure Over Time**: union-find with time slots.
- **DC-NET-07 Heal a Network Partition**: union-find to count separate segments.
- **DC-SEC-12 Blast Radius of a Leaked Credential**: what the merged identity can reach.
