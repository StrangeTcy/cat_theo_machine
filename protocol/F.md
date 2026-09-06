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
| launch-plan receipt (fable 5, partial) | protocol/2026-09-05-fable-5-unified-launch-plan-RECEIVED.txt |
| launch-plan completion (fable 5 tail)  | protocol/2026-09-05-fable-5-completion-RECEIVED.txt |
| charter source chain (v1, v2, distribution, launch sequence, qwen variant) | protocol/2026-09-05-charter-source-chain-RECEIVED.txt |
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

## 10. Owner launch-plan receipt (fable 5, partial) and reset event

Receipt. On 2026-09-05 the protocol owner issued "fable 5" (Unified Launch
Plan: One Program, Eight Roles, Two Pipelines) over the direct channel.
The text arrived TRUNCATED: it stops mid-sentence inside Text #3 (E-eng),
phase E3, at "two renderings of". Not received: the E3 remainder and any
later phases, Text #4 (G-eng), Text #5 (F-tools-eng), Text #6 (G/I-op),
Text #7 (S/E-op), Text #8 (INT batch instruction), and any closing
sections. The received bytes are archived verbatim with the truncation
locus marked in
`protocol/2026-09-05-fable-5-unified-launch-plan-RECEIVED.txt`
(six-phrase scan over the archive: zero matches). No instruction from the
plan has been executed by this operator: role assignments and the spawn
order belong to the owner's launch sequence, and this operator stays on
the F track. The plan's missing agent texts are owner material; this
operator neither reconstructs nor invents them.

Owner-mapping of this record's open gate items under the fable-5 roster
(recorded so the owner can sequence INT and F-tools-eng against them):
- gate item 3 (no declared tag) → INT deliverable (preflight tag,
  `preflight-<shortsha>`, cut-<n> tags; INT alone cuts tags).
- gate item 6 (no named checkpoint) → F-tools-eng F1 deliverable
  (checkpoints) — its Text (#5) was among the parts NOT received.
- gate item 7 (audit-header instrument absent) → F-tools-eng F4
  deliverable (audit format).
- gate item 8 (D11 closure unverifiable) → INT preflight step 1
  (exception mechanism named in protocol/preflight/ledger.md).
- gate item 9 (no blank controls) → fable invariant 2: operators rerun
  blank controls after each semantic cut; none exists yet on any tag.
- gate item 10 (no F2/F3/F4 refs) → F-tools-eng F2 (grader), F3 (decoy
  harness/comparator), F4 (auditor) deliverables.
- §8 owner declarations (a)–(g) remain prerequisite for any gate retry;
  the fable's §2 setup items (charters commit, exam seal to protocol/I.md)
  are also absent from the arena tip as of this receipt and are
  human-only steps this operator cannot perform.
- The plan designates F-op as "the human operator ... fresh context,
  maximally blind". This operator's session record (blindness declaration,
  gate artifacts, contamination ledger) is pre-wave-0 evidence available
  to INT's protocol index; no acceptance or ratification role is claimed.

Reset event (2026-09-05, after push 3d9e03b). The workspace reset to the
original checkout (HEAD 41e8078) with every session artifact surviving
only as untracked files. Recovery, fully verified: fetched the pushed tip
refs/heads/arena/01a06e7b-cat-theo-machine @ 3d9e03b (explicit refspec —
the clone's default fetch refspec covers master only, which is why a plain
fetch missed the branch); moved the 8 untracked survivors aside after
hash-verifying them against the pushed manifest; fast-forwarded; proved
all 8 files byte-identical to the surviving bytes; re-verified every
manifest hash line. Zero bytes lost. This event is empirical confirmation
of the plan's standing constraint that an unpushed commit is not
protected; it is also the first entry for a sandbox-reset ledger on this
branch.

Completion receipt (2026-09-05, second reset survived). The plan's missing
tail arrived over the owner channel and is archived verbatim in
`protocol/2026-09-05-fable-5-completion-RECEIVED.txt`. Coverage against
the truncation marker's NOT-RECEIVED list: COMPLETE — (1) Text #3 E3
remainder plus E4 and the E-track stop/report block; (2) Text #4 (G-eng,
with planner-interface inspection first and a MethodSetDivergence ledger
rule); (3) Text #5 (F-tools-eng, phases F1–F4 with fixture requirements);
(4) Text #6 (G/I-op); (5) Text #7 (S/E-op, five-leg S5 rule); (6) Text #8
(merge batch: exact-SHA fetches, SHARED→S→E→G→F-tools order, semantic
exclusion, per-failure classification, SEMANTIC/NON-SEMANTIC cut
classification); (7) closing sections 4 (five human-only items), 5 (turn
loop, stall rule), 6 (kill conditions), and the closing sentence. Seam:
the completion restates the E3 opening line, which is the RECEIVED
archive's final line; union keeps one copy (rule stated in the artifact
header). Six-phrase scan over the completion archive: zero matches.
A second sandbox reset occurred before this receipt was committed;
recovery repeated the verified procedure against pushed tip de56597 with
zero loss (reset-ledger entry 2).

Source-chain receipt (2026-09-05). The owner also delivered the document
chain that produced the plan: charter v1 (three tracks), charter v2 (five
tracks), the distribution model (TWO-PIPELINE-equivalent), the v1 launch
sequence, and the "qwen 3.8" spawn-instruction variant. Archived verbatim
with delimiters in
`protocol/2026-09-05-charter-source-chain-RECEIVED.txt`. Status: received-
record stopgap only — fable 5 §2 makes committing CHARTER-v1.md,
CHARTER-v2.md, and TWO-PIPELINE.md a HUMAN setup step; the human's
canonical commit supersedes this archive. Per fable 5's own preamble the
completed fable 5 is the operative consolidation; no reconciliation is
performed by this operator. Six-phrase scan over the source-chain
archive: 14 matched lines, all inside the owner's received text — 9 are
the standing-constraints block quoting the ban list itself, 1 is the v2
I3 outcome comment, 1 is a distribution-document heading, and the rest
are the per-text ban-list repetitions. Classification: mentions inside a
verbatim received record, not authored prose; the filter binds this
operator's authored prose, commit messages, and reports. The completion
archive is unaffected (zero matches).

Owner mapping, refined against the completed plan (supersedes the
provisional mapping above where more precise):
- Gate item 6 (named checkpoint) and item 7 (audit header) → F-tools-eng
  F1: save/load checkpoint with content-addressed ids; the audit header
  must print the loaded id AND the full loaded-class list — per Text #5,
  a header missing either is a defect by construction. Named checkpoints
  library-only-control, curriculum-a3, set-b-cumulative may land as
  empty declared slots.
- Gate item 10 (F2/F3/F4 refs) → F-tools-eng F2 (grading script, fixture-
  proved with a nonzero-teach positive control), F3 (residual comparator,
  exit taxonomy identical/silence-class/distinct/incomparable,
  N-transcript batches), F4 (per-session audit sheet).
- Gate item 8 (D11) → INT preflight step 1 (swallowed-exception
  mechanism named in the ledger). Gate item 9 (blank controls) → Text #8
  re-baseline rule after semantic cuts. Gate item 3 (tag) → INT preflight
  and cut tags.
- F-track kill conditions now on record for any future F session:
  preflight step 2 zero-partial-match on every probe gates F on the
  instrument defect; decoy/target residual identity withdraws the
  reading with no teach and no retry on unchanged semantics.
- The plan's section 4 keeps F-op, the sealed exam, approvals, and
  concept-gap decisions with the human. This operator's session record is
  pre-wave-0 evidence available to INT's protocol index; it claims no
  F-op role and no ratification authority.
