# protocol/F.md — F-PROVER protocol record
# session: FPS-20260905-A1
# execution date: 2026-09-05 (Europe/Moscow)
# operator branch: arena/01a06e7b-cat-theo-machine
# remote tip before work: origin/master @ 428ecdc146e38de3481222bed7bddeb3c08e1b2d

## 1. Mission status

The F-PROVER mission (derivation of the declared target theorem under
machine checking) is GATED on this build. The start gate failed on six of
ten items; per protocol, the dated start-gate artifact was produced and no
decoy process, no target process, and no teach was executed. See
`logs/2026-09-05-F-PROVER-start-gate.txt` for the item-by-item table.

One immutable tag per session was respected vacuously: no machine process
of any kind ran, so no session spanned a tag. No tag was cut or moved; no
branch was force-pushed.

## 2. Roles

- F-PROVER (this operator, session FPS-20260905-A1): produces evidence.
  Does NOT ratify its own success.
- F-AUDITOR: a separate fresh agent that performs the final replay and the
  acceptance decision once evidence exists. No F-AUDITOR session has run.

## 3. Gate summary

| item | subject                                   | status |
|------|-------------------------------------------|--------|
| 1    | fetch remote refs and tags                 | PASS   |
| 2    | remote tip before work recorded            | PASS   |
| 3    | immutable tag declared + peeled hash       | FAIL — no declaration exists |
| 4    | operator-branch tip recorded               | PASS   |
| 5    | working tree free of machine-code changes  | PASS   |
| 6    | named checkpoint + content-addressed id    | FAIL — no checkpoints/ dir, no declaration |
| 7    | audit header prints required fields        | FAIL — instrument absent |
| 8    | D11 (or successor) closure confirmed       | FAIL — unverifiable on this build |
| 9    | post-cut blank controls on same tag        | FAIL — absent |
| 10   | F2 grader, F3 comparator, F4 auditor refs  | FAIL — refs absent |

Verdict: GATE_FAILED. Candidate tags were fetched and hashed only
(peeled hashes in the start-gate artifact); `experiment-4-frozen` is
marked FORBIDDEN for any run.

## 4. Defect ledger (instrument gaps relative to the protocol)

All entries below were established by inspection on the untagged working
tree at branch tip 41e80785d4de090337a9dfc08439f2fcb45915dc; no machine
process ran, so none was found by running. Routing: INT (protocol owner).

- DEF-2026-09-05-01 — audit-header instrument absent.
  Locus: `runtime.py`, `main.py`, `session.py`, `persistence.py`;
  `grep -c audit` = 0 in each. Gates start-gate item 7.
- DEF-2026-09-05-02 — research-mode entry channel absent.
  Locus: `session.py` has zero occurrences of "mode"; `main.py`,
  `runtime.py`, `session.py` have zero occurrences of "research".
  Gates decoy/target process step 1.
- DEF-2026-09-05-03 — live teaching interface absent.
  Locus: `session.py`, `runtime.py`; `grep -in teach` = 0 hits.
  Gates the live teaching loop.
- DEF-2026-09-05-04 — dependency-request channel absent.
  Locus: repo-wide `grep -in "suggest depend"` = 0 hits. Gates dependency
  classification and the F3 input path. DEEPENED 2026-09-05 by the
  residual-harness check: the only "residual" concept in machine code is
  `ResidualHeadBucketLabel` (labels.py:282 defined, :1819 instantiated,
  :2102 registered — a constructor label, not a residual producer);
  machine.py, planner.py, session.py, runtime.py and search/ have zero
  "residual" occurrences; the only word-boundary stall surface is
  tools/repro_compose_stall.py, which reports engine counters and a
  reproduction banner — no residual term, no dependency suggestion, no
  unmatched-premise listing. No code path emits a concrete residual.
- DEF-2026-09-05-09 — terminal-term vocabulary absent (added 2026-09-05 by
  the residual-harness check). Locus: zero occurrences of
  UncharacterizedStall, InstrumentDefect, RegimeA/B/C in all tracked .py
  files. The machine defines no constructors for the protocol's terminal
  terms, so even a closed derivation could not be reported by the machine
  itself in that vocabulary on this build.
- DEF-2026-09-05-05 — no declared session tag, no named checkpoint, no
  profile definitions. Locus: `protocol/` and `checkpoints/` absent at
  HEAD; no declaration artifact at any pushed ref. Gates items 3 and 6 and
  the profile order.
- DEF-2026-09-05-06 — F2 grader, F3 residual comparator, F4 auditor absent
  from every pushed ref. Locus: `git ls-remote origin` enumerates master,
  six tags, and arena operator branches only; `tools/` holds
  `rung1_gate.py`, `rung2_gate.py`, `shard_suite.py`,
  `repro_compose_stall.py`, none of which is an F2/F3/F4 instrument.
  Gates item 10.
- DEF-2026-09-05-07 — D11 (or successor) closure unverifiable.
  Locus: the term "D11" has zero occurrences repo-wide; no defect register
  exists at any ref. Gates item 8.
- DEF-2026-09-05-08 — post-cut blank-control evidence absent.
  Locus: "blank control" has zero occurrences repo-wide. Gates item 9.

No defect was renamed as a capability gap; each entry names its precise
locus. No fabricated capability name appears in this record.

## 5. Contamination ledger

Empty. No prohibited exposure occurred in this session: no reference
dependency graph, no curriculum answer set, no pack source read, no known
proof consulted, no prior target-session transcript inspected (none
exists for this operator). The project-blind declaration with its scope
statement is `protocol/2026-09-05-F-PROVER-blindness-declaration.txt`.
Any future exposure is recorded here as
`Contamination(session_id, source, time)` and voids the target session.

## 6. Artifacts registered this session

| artifact | path |
|----------|------|
| project-blind declaration | protocol/2026-09-05-F-PROVER-blindness-declaration.txt |
| start-gate report         | logs/2026-09-05-F-PROVER-start-gate.txt |
| checkpoint integrity audit| logs/2026-09-05-F-PROVER-checkpoint-audit.txt |
| transcript inventory      | logs/2026-09-05-F-PROVER-transcript-inventory.txt |
| residual-harness check    | logs/2026-09-05-F-PROVER-residual-harness-check.txt |
| replay-manifest check     | logs/2026-09-05-F-PROVER-replay-manifest-check.txt |
| hash manifest             | checkpoints/2026-09-05-F-PROVER-manifest.txt |

Dated reproducible measurements recorded this session (replayable by the
commands inside the two check artifacts):
- 34/34 hash lines under snapshots/ byte-identical to the pinned
  checkpoint-audit listing (replay-manifest check, measurement 1).
- Run-manifest schema stable: 2 keys (goal_text, start_text), key-set
  hash-identical across all three search_compare runs; values unread
  (blindness preserved) (replay-manifest check, measurement 2).
- Terminal-term vocabulary counts: 0/0/0/0/0 for UncharacterizedStall,
  InstrumentDefect, RegimeA, RegimeB, RegimeC (residual-harness check,
  scan 3).

Content ids (sha256) for every artifact above are recorded in the hash
manifest; the manifest's own id is computed post-write and recorded in the
session turn report, since a file cannot contain its own hash. Raw
transcripts were not rewritten; the only in-turn regeneration was this
session's own checkpoint-audit draft being replaced by a tool-generated
version before any commit (no machine bytes were involved).

## 7. Standing constraints applied (§0 as received 2026-09-05)

- No machine, parser, search, matcher, planner, or pack file edited; no
  `core.py` edit; no monkeypatching; no generator, proof skeleton, parser
  branch, or special dispatch added; no theorem content added through
  repository files.
- Six-phrase prose filter applied to this record, all artifacts, and the
  commit message.
- No Python run inside conda; this session ran no Python at all
  (shell coreutils and jq only).
- Experiment 4 not run; no tag cut or moved; no force-push.
- All machine values, including failures, are to be treated as machine
  terms; this session produced none, and claims none.

## 8. Owner declarations required to re-open the gate

a. immutable session tag by name; b. named checkpoint with
content-addressed id; c. profile definitions (`library-only-control`,
`curriculum-a3`, `set-b-cumulative`, plus full-audited authorization
conditions); d. pushed refs for F2/F3/F4; e. D11-or-successor closure
evidence on the declared tag; f. post-cut blank-control evidence on the
same tag; g. the sealed decoy statement delivered through the machine
channel only, never through repository files or chat prose.

## 9. Next active tasks (non-target, authorized)

1. Cold-load verification of pinned snapshot states (byte-pinned in the
   checkpoint audit, drift-free per the replay-manifest check) through the
   machine's own persistence path, in a fresh process, once a python
   invocation channel is agreed — this is checkpoint verification, not a
   target process.
2. DONE 2026-09-05: residual-harness pre-check — DEF-2026-09-05-04 deepened
   with precise loci and DEF-2026-09-05-09 added
   (logs/2026-09-05-F-PROVER-residual-harness-check.txt).
3. DONE 2026-09-05: replay-manifest check — 34/34 byte-identical to the
   pinned audit; manifest schema pinned
   (logs/2026-09-05-F-PROVER-replay-manifest-check.txt).
4. On owner declarations (a)–(g): re-run the start gate on the declared
   tag in a fresh session; only on PASS may the decoy session run first.
