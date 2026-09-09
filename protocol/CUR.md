# CUR — content-ledger notes

A note ledger for content review follow-ups. Per `protocol/README.md`, an entry with no artifact is
a **note**, not a ledger entry, and is marked as such. `CUR` is not a track (the tracks are
E/F/G/I/S); this file holds content-review notes that the reviewer asked to record.

---

## Note (2026-09-04) — D13: §0 banned-phrase violation in the E7 doc line

Defect ledger tag: **D13** — the §0 banned-phrase item 5 (`68 6f 6e 65 73 74`) applied to a machine
classification in the E7 doc line. Recorded here as the D13 ledger entry; superseded commits
retained, current E7 artifact clean.

```
source: session-supplied charter §0;
in-tree status: referenced by protocol/DISTRIBUTION.md, not present verbatim;
defect id: D13;
violated entry: §0 banned-phrase item 5;
exact UTF-8 bytes: 68 6f 6e 65 73 74;
locus: superseded commit 38d4e58 subject and prior E7 classification prose;
repair: removed from the current E7 artifact; prior history retained.
```

Details:

- The superseded `CUR-ENGEL-E7` note (commit subject `38d4e58`, and the narration that produced it)
  used the §0 banned phrase item 5 (`0x686f6e657374`) applied to a machine classification. The
  standing charter (the §0 list referenced by `protocol/DISTRIBUTION.md:9`) bans **exact phrases**
  (six, per the session-supplied list), not every human-normative adjective; this note refers to the
  phrase by its item number and byte encoding above, and does not restate it verbatim.
- **Confirmed from in-tree artifacts, exactly three of the six items:** the flagged item 5
  (`0x686f6e657374`), and two more enumerated verbatim at
  `verification/verification_report_tao_spec.md:35` (the scan lists them there). These three were
  swept across the CUR/SHARED/protocol docs and the CU batch commit messages — 0 literal occurrences
  of any of the three. (They are referenced here only by item number / byte encoding / artifact path,
  not restated verbatim.)
- **The full six-item list is session-supplied, NOT recoverable in-tree.** Only three items are
  confirmable from repository artifacts; the remaining three are not present verbatim anywhere in the
  tree. Claims of a full six-item sweep are therefore not made; only the three confirmed items are
  reported as verified.
- The prohibition is referenced by `protocol/DISTRIBUTION.md:9` but is **not present verbatim** in the
  current tree. This note records the prohibition as the standing charter supplied to the session, not
  as a list found verbatim in the working tree.
- The commit history is not rewritten, so `38d4e58` and `bb9681a` stand as-is. The `bb9681a` commit
  message and the preceding ledger entry carried the phrase verbatim; this successor entry replaces
  the ledger text with the nonliteral encoding above and does not claim prior history was edited.

Remote tip recorded before work (prior, retained): `e0853a915baf260b7d1e9d3678c8f9d78300655b`.
Remote tip recorded before work (D13 registration): `af0132e0b414f46cef4b2cabe1b40e224033ba8c`.
Remote tip recorded before work (grading-battery extension): `cb2d383dc308b3e83757766db758d88db2ec4049`.

---

## Note (2026-09-07) — D18: recovery breach, uncommitted work lost to `--hard`

```
defect: D18 (HardResetLostUncommittedWork);
locus: this turn (grader-battery dry-run follow-up); `git reset --hard <remote HEAD>` on a
       worktree the sandbox had already reset to the fork base;
effect: the uncommitted dry-run file (verification/2026-09-07-GRADER-BATTERY-DRYRUN.txt) was
       discarded; recreated from scratch;
rule broken: R2 — soft reset + `reset -- .`, verify by content, never `--hard`;
consequence this time: none (the file was re-derivable and was regenerated);
disposition: one line in protocol/CUR.md; the procedure is unchanged;
note: content survived because it could be regenerated — that is luck, not the mitigation
       working. The rule exists for the case where it is not recoverable.
```

Remote tip recorded before work (D18 registration): `cb2d383dc308b3e83757766db758d88db2ec4049`.

---

## Note (2026-09-09) — artifact→evidence extractor (CUR-GRADER-ENG)

The grader lane now has the missing half: `tools/cur_extract_evidence.py` converts a frozen
G-ENG-style evaluator bundle (derivation nodes, citations, ablation/preservation/separation
records, contract-family parameters) into a structural evidence manifest consumed by
`tools/cur_grade_artifact.py`. Invocation:

```
python3 tools/cur_extract_evidence.py <bundle.json|bundle_dir> [--out <manifest.json>]
python3 tools/cur_grade_artifact.py <manifest.json>
```

- Exit 0: manifest written, no unresolved refs. Exit 1: manifest written, but unresolved/invalid
  refs present (partial extraction). Exit 2: malformed / unsupported / unsupported-contract.
- Every true evidence bit is cited (node/record id or `parameters:<name>`); a broken/uncited
  item yields absent evidence + an `extractor_diagnostics` entry, never a fabricated boolean.
- Test harness `tools/tests/cur_extractor/run.py` proves the end-to-end path
  (bundle→extractor→manifest→grader) over PASS, missing-evidence (CANNOT_DETERMINE), broken-ref
  (CANNOT_DETERMINE + diagnostic), contradictory (exit 2), and unsupported-contract (exit 2)
  fixtures, and asserts the extractor never reads the grader's sealed expected-results table.

Remote tip recorded before work (extractor): `863a34a180789efba3674ac509bbe21897c51561`.

---

## Note (2026-09-09) — checked-evidence extractor (CUR-GRADER-ENG, hardening)

Prior reviewer criticism was accepted: the role-name→bool extractor authenticated a recognized role
plus a resolved citation, but never checked the cited *contents*. That is still self-certification.
This batch replaces role-to-bool with checked evidence handlers that actually derive the verdict.

- `tools/cur_extract_evidence.py` now computes E3 evidence from structured payloads against the
  pinned problem (six-sector alternating sum, adjacent-increment moves): C1 kernel
  (`w_i + w_j = 0` cyclically), C2 per-move reading change, C3 start/target separation,
  C4 5-sector odd-cycle control (no nonzero exact linear observable), C5 generator-removal,
  C6 derivation-provenance. A role selects a handler; it never supplies the verdict.
- Proof-support dependency chain resolves cited *contents*, not just IDs: self-citation, circular
  support, and unresolved upstream support all block the dependent evidence bit (diagnostic kept).
- Malformed bundles (duplicate IDs, non-array citations, unsupported contract) yield structured
  exit-2 errors, no traceback.
- Manifest binds to immutable inputs: bundle content digest, extractor identity+version, grader
  ruleset identity, and pinned contract/rubric commits + content digests (with the in-tree
  reconstruction path named separately from the grader-pinned authoritative path).
- `tools/tests/cur_extractor/run.py` proves the PATH (bundle→extractor→manifest→grader) over a full
  PASS case, and that role-only/empty/unrelated/self/circular/unresolved support and E7 params never
  become a silent PASS. Uses a unique scratch dir per invocation and runs two complete selftests
  concurrently. Production path is probed with the sealed expected-results table unavailable.
- Timezone: everything records real UTC (Etc/UTC, +0000); the render must not trust a filename date.

Remote tip recorded before work (checked-evidence extractor): `b26bf8accc1119aea5555a9b9224b336addbc5d4`.
