# CUR — §0 consolidated sweep, both CUR branches (2026-09-06)

Docs-only audit artifact, CUR branch. Agent: CUR-ORACLE on `arena/01a066cf-cat-theo-machine`.
Consolidates the two-branch §0 sweep into one dated record, at the branch tips recorded below.

## Scope

Swept, per the standing CUR-ORACLE directive (item 2):

- every `CUR-*.md`, `SHARED-*.md`, and `protocol/CUR.md` on both branch **tips** (content, not
  working tree — each file read at its tip SHA via `git show <ref>:<path>`);
- every **commit subject** reachable from each branch tip;
- plus the sibling's additional `protocol/*.md` and `verification/*check*.txt` files (it carries
  no `protocol/CUR.md`), swept for completeness.

## Tips recorded before work (ls-remote / fetched)

| branch | tip SHA |
|---|---|
| `arena/01a066cf-cat-theo-machine` (canonical, mine) | `b9ddf61b9d62b9a06387c7bf49b071a8b02403b7` |
| `arena/01a068c2-cat-theo-machine` (sibling) | `d573e42d659b2c5e9e59811bdf48a7417c5f2360` |

Note: the sibling tip **advanced** since the audit file `CUR-CROSS-BRANCH-AUDIT-2026-09-05.md`
was written (which records `9fb8870`); it now carries the E3/E4/E7 grader contracts, the E3 oracle
card, `CUR-MERGE-VERIFICATION-CHECKLIST.md`, and `CUR-ORACLE-SEALING-AND-DISTRIBUTION-HANDOFF.md`.
This sweep covers the current tip.

## Tokens swept

Three of the six §0 items are confirmable in-tree; the other three are session-supplied and not
recoverable in-tree (per `protocol/CUR.md`), so **exactly three** were swept — the claim boundary
is "three of six confirmed", **not** six. Tokens are identified by item number / byte encoding /
artifact path, never restated verbatim:

- **item 5** — by byte encoding `0x686f6e657374`, word-boundary, case-insensitive.
- **the two named entries** — enumerated verbatim at
  `verification/verification_report_tao_spec.md:35` (identified there by artifact path; not
  restated here).

## Result

**0 occurrences** of all three confirmed items in every in-scope file on both tips, and **0
occurrences** in every commit subject on both branches. Disposition for every file: **clean**.

| branch | files swept | item 5 | named entry A | named entry B |
|---|---|---|---|---|
| `01a066cf` (mine) | 11 (`CUR-*.md` ×9, `SHARED-*.md` ×1, `protocol/CUR.md` ×1) | 0 | 0 | 0 |
| `01a068c2` (sibling) | 7 (`CUR-*.md` ×7) | 0 | 0 | 0 |
| `01a068c2` extra (protocol + verification) | 5 | 0 | 0 | 0 |

Commit subjects (all reachable commits from each tip): mine **0**, sibling **0**.

## File-by-file disposition

### `arena/01a066cf-cat-theo-machine` (`b9ddf61`)

| file | token | disposition |
|---|---|---|
| `CUR-CROSS-BRANCH-AUDIT-2026-09-05.md` | item 5 / A / B | clean |
| `CUR-E-ENG-WAVE1.md` | item 5 / A / B | clean |
| `CUR-ENGEL-E3.md` | item 5 / A / B | clean |
| `CUR-ENGEL-E4-descent-refutation.md` | item 5 / A / B | clean |
| `CUR-ENGEL-E4-oracle.md` | item 5 / A / B | clean |
| `CUR-ENGEL-E4.md` | item 5 / A / B | clean |
| `CUR-ENGEL-E7-oracle.md` | item 5 / A / B | clean |
| `CUR-ENGEL-E7.md` | item 5 / A / B | clean |
| `CUR-EXPLAIN-E2.md` | item 5 / A / B | clean |
| `SHARED-CONSTRUCTORS-E7.md` | item 5 / A / B | clean |
| `protocol/CUR.md` | item 5 / A / B | clean |

### `arena/01a068c2-cat-theo-machine` (`d573e42`)

| file | token | disposition |
|---|---|---|
| `CUR-ENGEL-E3-EVALUATOR-CONTRACT.md` | item 5 / A / B | clean |
| `CUR-ENGEL-E3-oracle.md` | item 5 / A / B | clean |
| `CUR-ENGEL-E4-GRADER-CONTRACT.md` | item 5 / A / B | clean |
| `CUR-ENGEL-E4-ORACLE.md` | item 5 / A / B | clean |
| `CUR-ENGEL-E7-GRADER-CONTRACT.md` | item 5 / A / B | clean |
| `CUR-MERGE-VERIFICATION-CHECKLIST.md` | item 5 / A / B | clean |
| `CUR-ORACLE-SEALING-AND-DISTRIBUTION-HANDOFF.md` | item 5 / A / B | clean |

Sibling protocol / verification (no `CUR-`/`SHARED-`/`protocol/CUR.md`, swept for completeness):
`protocol/G.md`, `protocol/I.md`, `protocol/[SHARED]-A1-CONSTRUCTORS.md`,
`verification/2026-09-04-CUR-ENGEL-E4-check.txt`, `verification/audit_report_tao_refactor.txt` — all
**clean** (item 5 / A / B = 0).

## Claim boundary

**Three of six confirmed.** Only the three in-tree-confirmable items were swept. The remaining
three of the six are session-supplied and not present verbatim anywhere in the tree; no full-six
claim is made. Sweep method: byte-encoded (token never typed literally in command or artifact) +
word-boundary + case-insensitive, over `git show <ref>:<path>` content and `git log --format=%s`
subjects.

## Notes

- No violations; no ledger entry required. (Found nothing to amend — every result is clean.)
- The only §0-adjacent ledger entry remains the **D13** record in `protocol/CUR.md` (item 5, the
  E7 doc line, byte-only encoding) — that is a prior historical note, not a current content hit.
- Methodology caveat, recorded with the same discipline as the prior sweep: this is content
  scanning for the three confirmed items, not a claim about the six-item list as a whole.

Docs-only; no production code, labels, Edge classes, packs, or G implementation touched.
