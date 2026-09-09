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

CURRENT-STATUS NOTE (2026-09-07, per external audit correction 2 — this
note scopes the ledger; the entries above are preserved as the historical
inspection record):

    historical absence:
      applies to the recorded inspection build and inspected refs
      (working tree at 41e80785d4de090337a9dfc08439f2fcb45915dc plus the
      refs observed 2026-09-05 via git ls-remote: master, the arena
      branches then listed, and the six tags then fetched). Statements
      like "absent from every pushed ref" in the entries above must be
      read with that 2026-09-05 ref set.

    current availability:
      requires reconciliation with the existing INT and F-tools
      deliveries. Pinned 2026-09-07, identity level only: charter
      documents at 99d92808f124387e3940a0c9abb49eedc9d7b226 (on
      arena/01a06542), F-tools battery at
      704db5e1f230a9893b8f389261e21c33c97ba7d0 (on arena/01a06eb9), INT
      preflight/partition/shared/s1/eng-base tags per
      protocol/2026-09-07-F-PROVER-owner-handoff-request.txt. Neither
      commit is in this operator branch's history; no content inspected;
      no duplicate tools commissioned.

    session readiness:
      requires exact artifact identities and compatibility with the
      owner-declared session tag; branch availability alone is
      insufficient. A declared-empty checkpoint slot is not a supplied
      checkpoint. Missing declarations remain explicit missing inputs.

## 5. Contamination ledger

Empty. No prohibited exposure occurred in this session: no reference
dependency graph, no curriculum answer set, no pack source read, no known
proof consulted, no prior target-session transcript inspected (none
exists for this operator). The project-blind declaration with its scope
statement is `protocol/2026-09-05-F-PROVER-blindness-declaration.txt`.
Any future exposure is recorded here as
`Contamination(session_id, source, time)` and voids the target session.
EXPOSURE UPDATE 2026-09-07: the target programme's identity was disclosed
through the owner's authorized archives (see
`protocol/2026-09-07-F-PROVER-exposure-update.txt`). Programme
identification is recorded there as a scope fact, NOT as Contamination;
the separate unseen list (reference proof, dependency graph, prior target
transcript, curriculum answers, pack sources, decoy statement) is
certified unseen as of 2026-09-07. Contamination count: still zero.
SCOPED UPDATE 2026-09-09: a decoy-only diagnostic was authorized and
executed on INT tip bfd4bd2; the decoy statement was received through the
owner channel for that run and exercised once. Surfaces observed are
decoy residuals only (cost, partial-match count, residual root — recorded
in logs/2026-09-09-F-PROVER-decoy-diagnostic-bfd4bd2.log). The unseen
list otherwise stands: reference proof, dependency graph, prior target
transcript, curriculum answers, pack sources — all still unseen.
Contamination count: unchanged, zero.

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
  [SUPERSEDED 2026-09-07 — see the CORRECTION block at the end of this
  section: D11 and preflight item 1 are different investigations.]
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
  mechanism named in the ledger). [SUPERSEDED 2026-09-07 — see the
  CORRECTION block at the end of this section.]
  Gate item 9 (blank controls) → Text #8 re-baseline rule after semantic
  cuts. Gate item 3 (tag) → INT preflight and cut tags.
- F-track kill conditions now on record for any future F session:
  preflight step 2 zero-partial-match on every probe gates F on the
  instrument defect; decoy/target residual identity withdraws the
  reading with no teach and no retry on unchanged semantics.
- The plan's section 4 keeps F-op, the sealed exam, approvals, and
  concept-gap decisions with the human. This operator's session record is
  pre-wave-0 evidence available to INT's protocol index; it claims no
  F-op role and no ratification authority.

CORRECTION (2026-09-07, external audit correction 1 — supersedes the two
lines above marked [SUPERSEDED], which mapped gate item 8 (D11) to INT
preflight step 1 and thereby conflated two different investigations):

    gate item 8:
      owner: INT / SHARED-D11
      required evidence:
        relevant vocabulary repair and port included in the declared build;
        dated reachability and ablation evidence;
        explicit scope of what the repair demonstrates.

    preflight item 1:
      separate checkpoint-exception investigation;
      its closure does not establish D11 closure.

The external audit further cites an existing D11 port record (one
arithmetic-label port with 0 -> 1 -> 0 candidate counts) and states it
does not establish readiness for every goal nor close the separate
producer/consumer selection check. That port record has NOT been
inspected by this operator; its identity and locus are INT/F-tools
handoff items under protocol/2026-09-07-F-PROVER-owner-handoff-request.txt.

## 11. External audit receipt and correction batch (2026-09-07)

An external audit review received 2026-09-07 inspected pushed commit
b1f1d19329f14d18c52c4840551905d1cefe3b0f, accepted the receipt
completion, and required three corrections, all executed this turn:

1. D11 mapping corrected (block in section 10; the two superseded lines
   are retained in place and marked, per no-silent-edit discipline).
2. Absence findings scoped to the inspected build — CURRENT-STATUS NOTE
   appended to section 4 with the historical-absence /
   current-availability / session-readiness structure; the 2026-09-05
   entries preserved unmodified.
3. Exposure update recorded —
   protocol/2026-09-07-F-PROVER-exposure-update.txt: programme identity
   disclosed via the received archives; reference proof, dependency
   graph, prior target transcript, curriculum answers, pack sources, and
   the decoy statement separately certified unseen; contamination count
   still zero.

Also executed: section 8 checklist routed to current owners
(protocol/2026-09-07-F-PROVER-owner-handoff-request.txt) with identity
pins taken 2026-09-07 — charter documents at
99d92808f124387e3940a0c9abb49eedc9d7b226 (arena/01a06542), F-tools
battery at 704db5e1f230a9893b8f389261e21c33c97ba7d0 (arena/01a06eb9),
INT-line tags preflight-e73d748 / preflight-6a132f3 / preflight-412b215,
partition-32bc569, shared-7cf6394, s1-relation-contracts, eng-base-0
(peeled hashes in the routing artifact). Neither pinned commit is in
this branch's history; no content of any foreign delivery was inspected;
no duplicate tooling was commissioned; no target run is authorized by
the receipt. A protocol/F.md path collision between the F-tools track
ledger and this session record is flagged to INT for ruling (routing
artifact, name-collision note).

Reset-ledger entry 3 (2026-09-07): third sandbox reset before this
batch; recovery repeated the verified procedure against pushed tip
b1f1d19; all artifacts byte-identical; zero loss.

## 12. Ratification receipt and SPLIT-ON-MERGE ruling (2026-09-07)

The correction batch was RATIFIED by the protocol owner's review channel
(acceptance basis: against this lane's turn report; the manifest
verification chain is the check of record). The same channel recorded
the INT ruling on the path collision flagged in section 11:

    ruling: SPLIT-ON-MERGE
      protocol/F.md (track ledger) — F-tools' instance keeps the
        canonical path; it is the partition-designated track file.
      protocol/F-PROVER.md — this operator's session record migrates to
        a session-scoped name at whichever merge first brings both
        lineages into one tree. Until then, neither branch renames
        anything — unpushed renames under reset pressure are how content
        gets lost.
      merge executor: whoever performs the first cross-lineage merge
        cites this ruling and performs the rename in the merge commit
        itself, with both file histories preserved.

Adoption: archived verbatim at
protocol/2026-09-07-F-PROVER-ratification-and-ruling-RECEIVED.txt so the
ruling exists at a pushed ref, citable by the merge executor. This branch
performs NO rename now. Until that merge, this file's canonical name on
this lineage remains protocol/F.md, and readers should treat it as the
F-PROVER session record, distinct in role from the F-tools track ledger
of the same path on arena/01a06eb9.

Lane state after ratification: correctly parked on external inputs;
blocked-input table (INT tag declaration / F-tools identities /
protocol-owner profile) stands as published in the routing artifact; the
first owner-supplied declared input reopens work. Next active task on
reopen: start gate on the declared tag, fresh session, decoy first.

## 13. Identity-currency rule (carry-forward, adopted 2026-09-07)

The review channel's park-confirmation added one carry-forward check,
adopted here as the standing rule for this lane:

    F-tools identity check:
      accept the exact SHA supplied by F-tools or INT;
      verify it by remote ref and manifest;
      do not substitute a remembered older battery SHA.

The "battery pinned 704db5e by identity" lines in sections 10, 11, and
the routing artifact are HISTORICAL — correct for the 2026-09-07 identity
sweep that produced them, and left unmodified in place. Corroboration at
identity level (no content read): 704db5e1f230a9893b8f389261e21c33c97ba7d0
is an ancestor of 545d2ce1dd99ab91a949246727db3593acd27771, the
arena/01a06eb9 tip observed in the 2026-09-07 fetch — the F-tools branch
advanced past the battery commit, so the pin is a historical pointer, not
a current one. The next actual integration uses the owner-supplied
current SHA. Archive:
protocol/2026-09-07-F-PROVER-park-confirmation-RECEIVED.txt.

Reset-ledger entry 4 (2026-09-07): fourth sandbox reset before this
entry; recovery repeated the verified procedure against pushed tip
6732c21; all artifacts byte-identical; zero loss.

## 14. Decoy-only diagnostic on INT tip bfd4bd2 (2026-09-09, UNTAGGED)

Authorization: protocol owner, direct instruction — "Diagnostic run, not
measurement. Decoy only. No target. No teaching." No tag contains the
subject tip, so this run is recorded as: UNTAGGED — diagnostic only, not
admissible as F measurement.

Refs (step 1, recorded):
- subject tip: bfd4bd28de5765adbdabd1d152200fa67f11e5a2 =
  refs/remotes/origin/arena/01a06542-cat-theo-machine, re-verified this
  turn, not inherited. Subject line: "[SHARED] Preflight item 1: partial
  guard committed, defect NOT closed" (2026-09-08T20:01:41+00:00).
- ancestry: ef571b688bcfb581bd3e65ec28a18f438ca32595 IS an ancestor of
  the tip (merge-base --is-ancestor, exit 0) — the general ancestor-check
  form of section 13, first operational use.
- tag status: none contains the tip.

Environment (step 2): isolated detached worktree at bfd4bd2 (removed
after the run; this session's checkout untouched); venv python 3.11.2,
gmpy2 2.3.1 (GMP 6.3.0), pyyaml 6.0.3; no conda; no machine file read or
modified; packs loaded only through the machine's own loader.

Run (steps 3-4): fresh cold process, six commands verbatim; full capture
with header at logs/2026-09-09-F-PROVER-decoy-diagnostic-bfd4bd2.log
(verbatim section). Machine-recorded results:
- research mode ON; state: taught rules 0; axioms 0; library rules 0
  pre-load; dependency requests 0; intervention episodes 0; learned
  policies 0; residual generator enabled.
- packs: loaded; library rules 167; provenance LIBRARY_THEOREM.
- parsed goal (machine term):
  (forall n (implies (greater n 1) (nosolutions positive-integers
  (unknowns a b c) (eq (plus (pow a n) (pow b n)) (pow c n)))))
- outcome: FAILED. cost=334; rules with a genuine partial match: 0.
- residual record (machine term): (zero-successor-root ((forall n
  (implies (greater n 1) (nosolutions positive-integers (unknowns a b c)
  (eq (plus (pow a n) (pow b n)) (pow c n)))))))
- suggest dependencies: search stalled; attempted operational rules: 0;
  concrete unmatched formal premises: none; dependency characterized: no.
- LibraryRuleMatchedViaSurfaceMapping in the capture: 0 occurrences.

Comparison vs the r1 decoy record (owner-supplied baseline: cost 334,
partial 0, zero-successor-root) — step 5:
- cost: 334 vs 334 — identical.
- genuine partial matches: 0 vs 0 — identical.
- residual root: zero-successor-root vs zero-successor-root — identical.
Classification per the owner's dichotomy: IDENTICAL. Finding: the D11
arithmetic port (ExprEqLabel -> eq, landed on this tip per the owner)
does NOT reach the decoy's eq position. Why-note, from machine output
only: the eq head sits as an argument of nosolutions inside forall/
implies; the machine attempted zero operational rules and found zero
genuine partial matches, so the stall is produced at the outer goal
shape before any eq-position matching could occur — none of the 167
loaded LIBRARY_THEOREM rules partially matches that outer structure on
this build. Second independent blind-lane confirmation of the narrow-
reachability reading (D-G3), as the owner framed it.

D12 check (audit header lists loaded classes): PARTIAL. Present: loaded
classes (library rules 167, LIBRARY_THEOREM), intervention episodes 0,
learned policies none, taught rules 0 (research-mode state line).
Absent: tag/commit line; checkpoint id (cold start, none declared).
The header instrument exists on this lineage (progress vs the 41e8078
inspection where it was wholly absent) but lacks two protocol fields.

Terminal classification (protocol vocabulary): UncharacterizedStall(goal,
residual). A concrete residual record exists, but the machine states it
cannot characterize the missing theorem; naming a capability would be a
fabricated capability name, which the protocol classes as a defect.

Boundary: the target sentence was NOT submitted; nothing was taught; no
checkpoint was loaded (none declared); machine code unmodified.

## 15. Reachability matrix on INT tip bfd4bd2 (2026-09-09, UNTAGGED)

Authorization: protocol owner review channel (next-work item 1, highest
value: "locate the first constructor boundary where partial matches
become nonzero... still blind-safe, still no target"). Same untagged tip
as section 14; diagnostic only, not admissible as F measurement. Full
verbatim captures: logs/2026-09-09-F-PROVER-reachability-matrix-bfd4bd2.log.

Matrix (machine values verbatim):

    probe | parsed goal                                     | outcome | cost | genuine partials | residual
    ------+-------------------------------------------------+---------+------+------------------+----------
    A     | compile refused ("cannot read the sentence
          | past 'plus'"; word-form arithmetic with '=')    | REFUSED | -    | -                | -
    A1    | (eq (plus a a) (plus a a))                      | FAILED  | 334  | 1                | missing (eq (plus a a) (plus a a)) (rule origin primitive)
    B     | (nosolutions positive-integers (unknowns a b)
          | (eq (plus a b) (plus b a)))                     | FAILED  | 334  | 0                | (zero-successor-root (...))
    C     | compile refused (same refusal as A)             | REFUSED | -    | -                | -
    C1    | (forall n (implies (greater n 1)
          | (eq (plus a a) (plus a a))))                    | FAILED  | 334  | 0                | (zero-successor-root (...))
    D     | the decoy (section 14 goal)                     | FAILED  | 334  | 0                | (zero-successor-root (...))

    LibraryRuleMatchedViaSurfaceMapping: 0 occurrences in every capture.
    cost observation: 334 on every FAILED probe on this tip (constant
    machine value; recorded, not interpreted).

Frontier finding (measured): the first constructor boundary where
genuine partial matches become nonzero is the bare eq goal itself (A1:
partial = 1, "rule origin primitive"). Adding ONE enclosing constructor
- the nosolutions shell (B) or the forall/implies shell (C1) - drops
genuine partial matches to 0 and switches the residual to the
zero-successor-root form. The wall sits at the shell boundary:
eq-position matching is live exactly when eq is the whole goal, and
goes silent under the first wrapper. Two independent shell constructors
show the same transition; "narrow reachability" is now a measured
frontier, not a single-point failure.

Parser-surface finding (machine-reported, recorded blind-safe):
word-form arithmetic followed by '=' is refused by the goal compiler;
symbolic-atom equations compile. Refusal precedes any attempt (no cost,
no residual).

Worktree-state note: probe C's boot restored a research checkpoint left
by probe A's process in the shared worktree; all state lines still
showed taught rules 0 / axioms 0 / library rules 0 pre-load, and probes
B and D reproduced the pristine-worktree diagnostic values exactly; A1
and C1 were re-run on freshly re-created worktrees to remove the
variable entirely.

DEFECT (instrument class, routed to INT; filed per the review channel's
instruction):

    DEF-2026-09-09-10  D12-HEADER-INCOMPLETE on untagged cold start
      missing: freeze-tag/commit identity in the research-mode header
      missing: checkpoint identity field (cold start may legitimately be
               "none", but the field must still be printed)
      evidence: logs/2026-09-09-F-PROVER-decoy-diagnostic-bfd4bd2.log;
                logs/2026-09-09-F-PROVER-reachability-matrix-bfd4bd2.log
      consequence: a future admissible measurement requires those fields
               present even when the values are none / untagged

INT-FACING NOTE (D-G3-FPROBE, filed per the review channel's item 2;
the matrix above is its evidence):

    D-G3-FPROBE:
      D11 ExprEq->eq does not affect FLT-shaped decoy residual on bfd4bd2
      mechanism: outer nosolutions goal gets 0 partial matches
      measured frontier: bare eq -> 1 genuine partial match; +1 enclosing
        constructor (nosolutions | forall/implies) -> 0 partials,
        zero-successor-root residual
      consequence: content port must create rules that partially match
        the outer goal shape, not only bare eq
      evidence: logs/2026-09-09-F-PROVER-reachability-matrix-bfd4bd2.log

Boundary: the target sentence was NOT submitted; no teaching; no
"suggest dependencies" submitted by any probe; machine code unmodified;
all probes constructed within the machine's own parse surface as
exhibited by machine output (banner forms and the ratified decoy
sentence's symbolic syntax).

## 16. Matrix ratification and standing adoptions (2026-09-09)

The reachability matrix was RATIFIED by the review channel (acceptance
basis: this lane's report at 9b75349 and its verification chain). The
ratification is archived verbatim at
protocol/2026-09-09-F-PROVER-matrix-ratification-RECEIVED.txt. Three
items are adopted as standing:

1. D-G3-FPROBE — routing confirmed to INT/SHARED-D11, shell-level
   consequence framing explicit, and the INT-facing note gains the
   parser-surface line:

       D-G3-FPROBE (complete form):
         D11 ExprEq->eq does not affect FLT-shaped decoy residual on
         bfd4bd2
         mechanism: outer nosolutions goal gets 0 partial matches
         measured frontier: bare eq -> 1 genuine partial match; +1
           enclosing constructor (nosolutions | forall/implies) -> 0
           partials, zero-successor-root residual
         consequence: content port must create rules that partially
           match the OUTER goal shape (nosolutions / forall / implies),
           not only bare eq; arithmetic-level surface mappings move
           this wall by exactly zero
         phrasing constraint: symbolic atoms compile; word-form
           arithmetic with '=' is refused at compile ("cannot read the
           sentence past 'plus'"); any future decoy or target sentence
           must be phrased with symbolic atoms
         evidence: logs/2026-09-09-F-PROVER-reachability-matrix-bfd4bd2.log

2. Probe-isolation rule (instrument/procedure, same class as the
   sandbox-reset discipline):

       each probe gets a fresh worktree OR a cold checkpoint reset
       between probes; a research checkpoint written by probe N must
       not survive into probe N+1's boot.

3. Conditional classification for future tagged builds:

       on a TAGGED build, AFTER INT lands shell-level content, a stall
       identical to the decoy wall (cost 334 / partial 0 /
       zero-successor-root) routes as Blocked(outer-shape-unmatched)
       rather than UncharacterizedStall. On the current untagged build
       it remains diagnostic.
       gating facts: (a) the build is owner-tagged; (b) shell-level
       content has landed on it. Both must hold; neither is true of
       bfd4bd2 today.

The two-part baseline for any future tagged target session is recorded:
the FLT-shaped goal stalls at 334/0/zero-successor-root, AND the stall
is at the outer shell (proven by bare-eq liveness at the same tip);
partial>0 at a target can therefore arise only from shell matching,
which is the only place new content can change the reading.

Lane state: verified hold. On a declared tag: start gate first, then
decoy, then target, per protocol.

## 17. D11-SHELL-ENG brief and INT trigger received (2026-09-09)

The owner published the implementation handoff for the shell frontier:
a D11-SHELL-ENG engineering brief (phases: reproduce baseline, inspect
soundness, build minimum general shell support — preferred capability
names ForallImpliesDecomposition / NosolutionsIntroduction — executable
tests including negative control and ablation, separate NON-SEMANTIC
commit repairing the D12 header per DEF-2026-09-09-10, verification
artifacts, no tag cut by the engineer) and an INT merge trigger (exact-
SHA fetch, component tests, D11 gate, both shards, checker-validated
rules only, then a new immutable SEMANTIC tag, blank controls, and
notification of this lane). Archived verbatim at
protocol/2026-09-09-D11-SHELL-ENG-brief-and-INT-trigger-RECEIVED.txt.

This lane executed neither text: the brief belongs to an engineering
agent on its own authorized branch, the trigger belongs to INT, and the
owner's message states F-PROVER is kept untouched. Inputs cited from
this lane were verified at receipt: the F request IS this branch's HEAD
d224b2c; the matrix commit 9b75349 is a hash-pinned ancestor; the
authoritative INT line still resolved to bfd4bd2 at receipt time.

REOPEN CONDITION (from the trigger, recorded as this lane's defined
hold-end): on INT's notification that the semantic tag is cut, this
lane's sequence is — rerun the reachability matrix on the new tag; then
the start gate; then decoy; then target, only when the shell frontier
has moved. The hold until that notification is earned: every blind-safe
F-scope deliverable on this lineage is on a pushed ref (request d224b2c,
matrix 9b75349, diagnostic, ledgers).

## 18. Archive ratified; spawn sequencing recorded (2026-09-09)

The cd6b0ca receipt was ratified ("the right split: the brief is
recoverable under reset; the lane does not implement D11"), and the
owner's spawn/merge sequencing is recorded verbatim at
protocol/2026-09-09-F-PROVER-spawn-sequence-ratification-RECEIVED.txt:
(1) the human operator spawns D11-SHELL-ENG in a fresh session/worktree
on an engineering branch off the live INT tip; (2) the INT merge trigger
is withheld until the engineer reports `ready for INT merge: yes` with
exact pushed SHAs, A/B/C before/after/ablation counts, and test totals;
(3) the trigger is then pasted with those exact SHAs; (4) F-PROVER stays
parked until INT publishes the new immutable semantic tag, peeled
commit, blank-control requirement, and notification. Engineer-side
identity discipline restated: D11-SHELL-ENG re-fetches the live INT tip
and records that SHA; bfd4bd2 is not hard-coded if INT has moved.

This lane performs no spawn (charter lane separation; no agent-spawning
capability on an operator lane). Lane state: parked, no further work,
blocked on D11-SHELL-ENG spawn + INT tag/notification; the F sequence on
notification is fixed exactly as in section 17.
