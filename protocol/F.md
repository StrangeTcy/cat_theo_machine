# Track F -- FLT programme tooling and audit

Ledger entries for this track. Newest last. See protocol/README.md for
the rules governing entries, and research_protocol.md for cross-track
discipline.

## 2026-09-05 -- F-RUNNER decoy/target pair on experiment-5-frozen-r1: the recorded null again; reading withdrawn

Predicted (fable 5.1 gate note): on this tag both doors hit the same
wall -- cost 334, zero partial matches, zero-successor-root -- and the
correct action is withdraw, teach nothing, report.

Run: two cold processes on experiment-5-frozen-r1 (ef571b6, annotated
tag 5ebcd92), decoy first, target second, same command sequence
(research mode on; load theorem packs; audit knowledge; prove that
...; suggest dependencies; goodbye). Decoy: for all n > 1 x^n = y^n
implies x = y over positive integers. Target: for all n > 2 a^n + b^n
= c^n has no solutions in positive integers. Transcripts:
logs/2026-09-05-F-RUNNER-decoy.log, logs/2026-09-05-F-RUNNER-target.log.
Cold means no research_snapshot.json at boot; the state line on both
processes reports taught rules 0, packs load on demand, before
`load theorem packs` ran.

Came back: both sentences compiled to formal goals (the sentence
grammar covers the quantifier prefix, the comparison bound, pow, eq,
implies, over, and the no-solutions predicate); both attempts FAILED
at cost=334 with zero genuine partial matches; both residual records
root at zero-successor-root; both suggest-dependencies replies report
attempted operational rules 0, concrete unmatched formal premises
none, dependency characterized no. Class A (uncharacterized stall) on
both, per the classification in research_protocol.md. The residuals
are identical on every axis the fable names -- cost, partial matches,
residual root -- and differ only in the embedded goal term, which is
the two different sentences by design. Per the protocol's
negative-control rule and fable step 3, the FLT reading is withdrawn:
these transcripts measure the residual generator's default output, not
a characterization of the FLT dependency graph. Nothing was taught; no
checkpoint was saved; step 4 was never entered, because no concrete
unmatched formal premise was named on either side. Goal closed: no --
nothing to replay, no checkpoint saved.

FINDING (F tooling absent; defects F-D1..F-D3): fable 5.1 steps 3 and
5 name tools/f3-residual-diff.sh, tools/f2_grader.sh, and an F4
sheet. None exists on experiment-5-frozen-r1 or on master; tools/
holds the D-track scripts only. The comparison above was done directly
on the transcripts -- the three compared numbers are single greppable
lines, so the result is not in doubt -- but the fable cannot be
executed literally until the tooling lands. F-D1: f3-residual-diff.sh
does not exist. F-D2: f2_grader.sh does not exist. F-D3: the F4 sheet
is nowhere defined in the repository; for this run its content is the
empty role-coverage statement (no recall roles, no discovery roles,
reading withdrawn), recorded here rather than scored by a sheet that
does not exist. Landing the F tooling is the next task on this track;
independently, the D11-MAP pack port and the new tag it forces are
what would let a future pair get past step 3.

## 2026-09-05, second pass -- F-RUNNER pair repeated on the same tag: the null holds at n=2

Why repeated: research_protocol.md's own rule -- a single run of a
spawning process is provisional until repeated -- applied to the first
pair above. The fable was re-issued unchanged, so steps 1-3 were
re-executed in full rather than assumed.

Run: step 1 re-verified first -- remote tip still 428ecdc, no new
tags, experiment-5-frozen-r1 (ef571b6) still the newest frozen tag and
still admissible (zero semantic commits after it). Then two fresh cold
processes on the same tag, same command sequence, decoy first.
Transcripts: logs/2026-09-05-F-RUNNER-decoy-r2.log,
logs/2026-09-05-F-RUNNER-target-r2.log.

Came back: byte-identical transcripts from `research mode on` through
`goodbye` on both doors -- cost=334, zero genuine partial matches,
zero-successor-root, dependency characterized no, on decoy and target
alike. The morning pair's provisional status is resolved: the null is
stable across independent cold processes on this tag. Reading stays
withdrawn; nothing was taught; no checkpoint was saved; step 4 never
entered. Goal closed: no. The F-D1..F-D3 tooling defects stand
unchanged; the fable still cannot be executed literally until they
land.

## 2026-09-05, third pass -- F tooling landed; the fable runs literally; the null holds at n=3

Why: the fable was re-issued a third time with the repo unchanged
under it. The one part of its programme never executed was its own
terminal clause -- "move to F tooling" -- so the tooling landed first
and the pair then ran through the named instruments.

Tooling (closes F-D1..F-D3): tools/f3-residual-diff.sh compares two
transcripts on the three axes the fable names -- cost, genuine partial
matches, residual record root -- and prints identical or distinct with
the differing axes named. tools/f2_grader.sh grades one transcript by
the A/B/C/D classes fixed in research_protocol.md, keying on the
machine's own reply strings ("goal closed. cost=" / "[learned policy,
support" / "dependency requests from attempted rules:" / "dependency
characterized: no"). tools/f4-sheet.md fixes the pair-sheet format
with the role split restated unchanged from research_protocol.md
(recall: primitive normalization, descent, exponent transport;
discovery: exponent structure, impossibility transport, the richer
object). All three are text-reading operator tooling in the house
style of tools/recover.sh; none touches the machine, the packs, or the
parser, and they were validated against all four earlier transcripts
before grading a fresh run.

Run: step 1 re-verified -- tip 428ecdc, newest frozen tag still
experiment-5-frozen-r1 (ef571b6), still admissible. Two fresh cold
processes, decoy first, same commands. Transcripts:
logs/2026-09-05-F-RUNNER-decoy-r3.log, -target-r3.log.

Tool outputs on the fresh pair: F3 identical (cost=334, partial=0,
root=zero-successor-root on both doors); F2 class A -- uncharacterized
stall -- on both. Transcripts are byte-identical to passes 1 and 2
from `research mode on` through `goodbye`.

F4 sheet, pass 3 (passes 1 and 2 grade the same, tool-verified):

    pair:              2026-09-05-F-RUNNER-decoy-r3.log vs -target-r3.log
    freeze tag:        experiment-5-frozen-r1 @ ef571b6 (annotated 5ebcd92)
    F2 class:          decoy A ; target A
    F3:                identical (cost=334 partial=0 root=zero-successor-root)
    recall roles:      none
    discovery roles:   none
    target-only requests: none
    reading:           withdrawn
    teaches this run:  0
    goal closed:       no

Reading withdrawn; nothing taught; no checkpoint saved; step 4 never
entered. Goal closed: no. What would change this result is unchanged
from the gate note: INT landing the D11-MAP pack port, a new tag, and
blank controls rerun on it.

## 2026-09-05, fourth pass -- standing-order re-issue; the null holds at n=4

Why: the fable is a standing order and the operator re-issued it
unchanged. The redundancy judgment on a fourth same-day pair is the
operator's call, not the runner's, so the cycle ran in full: gate
check, cold pair, tools, sheet, push.

Run: step 1 re-verified -- tip 428ecdc, newest frozen tag still
experiment-5-frozen-r1 (ef571b6), zero semantic commits after it. Two
fresh cold processes, decoy first, same commands. Transcripts:
logs/2026-09-05-F-RUNNER-decoy-r4.log, -target-r4.log.

Tool outputs: F3 identical (cost=334, partial=0, zero-successor-root
on both doors); F2 class A on both. Transcripts are byte-identical to
passes 1 through 3 from `research mode on` through `goodbye`. F4 sheet
unchanged from pass 3 except the pair line: recall roles none,
discovery roles none, target-only requests none, reading withdrawn,
teaches 0, goal closed no.

Reading withdrawn; nothing taught; no checkpoint saved; step 4 never
entered. Goal closed: no. The open dependency remains INT's: the
D11-MAP pack port, the next tag, blank controls on it.

## 2026-09-05, tooling port -- F tooling merged from arena/01a06da9; the measurement deliverable is closed

Ratification (gpt 5.5 review) recorded: the pair is an admissible
negative-control measurement, the conclusion is the permitted one --
reading withdrawn -- and manual grep comparison was accepted for the
first pass because the compared fields are single transcript lines and
the missing tools were ledgered, not ignored. The review cites the
branch at 56372a5; by the time it arrived the branch had moved on --
the tooling had landed here independently at 1aed8e4 (closing F-D1..F-D3)
and the null was measured at n=4 (f58eec6), all four passes
byte-identical. Both facts are now on the record in one place.

Binding ruling accepted: no further pairs on unchanged semantics. The
F measurement deliverable is closed; the next measurement happens only
after the next semantic tag, blank controls first, decoy before
target.

Port executed per the review's task 1, from
arena/01a06da9-cat-theo-machine @ 966a077: tools/f2_grader.sh,
tools/f3-residual-diff.sh, tools/f3_batch_diff.sh, tools/f4_auditor.sh,
and the five spec files (f1-checkpoint-verbs, f2-grading-fixtures,
f3-residual-diff-batch, f4-audit-historical, blank-controls-r2).

One collision needed a decision: this branch and that one had both
written tools/f2_grader.sh and tools/f3-residual-diff.sh as different
instruments. Their f3 is the ported one (four axes and the
silence-class verdict; this branch's three-axis version is superseded
by it). Their f2 and this branch's f2 graded different things -- theirs
counts operator compliance (taught theorems, unlock evidence, circular
and computable requests, cite coverage), this branch's classified the
machine's outcome (A/B/C/D per research_protocol.md). Both functions
survive: theirs keeps the f2_grader.sh name as the review directs, and
this branch's classifier is renamed tools/f2-outcome-class.sh with its
function stated in its header. tools/f4-sheet.md stays as the hand-
filled per-pair sheet; f4_auditor.sh is the mechanical per-transcript
audit. INT's merge of the two branches is now free of content
conflicts on the tools/ paths.

Validation artifact: logs/2026-09-05-F-TOOLING-PORT-validation.txt
(dates in filenames are local, Europe/Moscow; the artifact's header
timestamp is UTC). Results: their F2 grader reports zero on every
count across all eight transcripts -- nothing was ever taught in any
pass, so compliance is trivially clean; their F3 reports identical on
all four pairs (exit 0; the silence-class verdict reserves exit 3 for
same-silence pairs that differ on an axis, which these do not); the
renamed outcome-class grader reports class A on all eight; the F4
auditor on the pass-4 pair reports packs loaded, audit present,
loaded-class list present, regime A, contamination no, and names the
instrument pre-D11 backward-blind.

Remaining programme per the review, none of it on this branch's lane:
D11 content work (pack port to the per-pack surface, nonzero partial
matches on non-FLT probes, full suite, next frozen tag) is engineering
and INT's tag cut; blank controls and the resumed pair follow the new
tag. The ZeroPartialMatchAmbiguity finding from the ported branch's
ledger -- the matcher cannot distinguish "no rule could match this
shape" from "the criterion is too coarse" -- is noted here by
reference; it is routed to S/INT as an instrument concern.

## 2026-09-05, charter check -- six banned phrases retrieved; five subjects clean; launch state recorded

CHARTER-v1 §0 is now in the repo (INT branch arena/01a07130, committed
6002caf with CHARTER-v2 and TWO-PIPELINE). The six banned phrases in
prose and commits are: "If you want", "matters", "but wait",
"actually", "honest", "Let me". Every commit subject on this branch
was checked against that list mechanically: all five clean. Branch
history is append-only, no force-push was ever issued, no conda Python
was run, Experiment 4 was never run, and the famous sentence was never
explained. The charter's constraints match the standing rules this
branch was held to from its first handout.

Charter §5 separates the lanes this branch's pre-charter history ran
together under explicit handouts: the fable 5.1 series had this agent
run F sessions, and the gpt 5.5 review had it port F tooling. The
separation -- F-tools builds, the blind operator runs -- binds forward
from the charter; the history stands as recorded, with its provenance
in the entries above.

Launch state observed from the remote: INT preflight complete -- item
1 inapplicable (no LearnedMemoryCheckpointTest exists in this lineage;
no swallowed exception to raise), item 2 closed (toy nosolutions
producer and consumer both compile to MultiRule and both register as
candidate partial matches on x + 1 = x), item 3 decoupled to INT's
protocol/F.md as an F-op-only gate reading DECOY REDESIGN REQUIRED
(both goal terms absent on that tip; engineering unblocked), item 4
two-shard suite run with the engineering baseline failure set
recorded (converse_default_mode_test; shard-1 install crash at
ConversePropositionTest / Thingy.tail). Wave-1 base tag eng-base-0
(1374464) is cut; S-eng has landed S1 (tag s1-relation-contracts,
897c07c). Setup gap for the human, per the plan's own one-time list:
the exam seal is not committed -- no protocol/I.md exists on INT's
branch.

This branch holds the closed F measurement record (null at n=4,
reading withdrawn, ratified) and the ported F1-F4 tooling. Its session
runner made no new measurement and will make none: the F-op gate is
closed and the charter reserves the one-shot for the human operator.
The unified-plan handout reached this branch truncated at Text #3
(E3); Texts #4 through #8, including the F-tools-eng text, have not
arrived. Awaiting the role assignment.

Landing note: this entry was committed twice. A sandbox reset between
turns rebuilt the branch pointer at the base while the working files
survived, so the first attempt squashed the whole session into one
local commit and its push was rejected as non-fast-forward. The branch
was repaired by fast-forwarding to the pushed tip and re-landing this
entry as the only new content -- the recovery path tools/recover.sh
documents. No history was rewritten; the remote chain stands intact.

## 2026-09-05, complete plan received -- F-tools lane mapped; F1 specced and waiting; F2-F4 complete

The complete unified launch plan (eight roles, two pipelines, Texts
#1 through #8) arrived whole, completing the copy that was truncated
last turn. This branch's role is Text #5, F-tools-eng. INT's protocol
index at partition-32bc569 -- single-branch reality, INT plus S-eng
consolidated, wave-1 base tag s1-relation-contracts@897c07c -- parks
F until structural parity, and names tools/ as the F surface in that
lineage.

Phase state, checked against the actual trees, not the plan text:

- F1 checkpoint verbs: the spec exists (tools/f1-checkpoint-verbs.spec.md,
  ported with the tooling batch) and is docs-only by its own text --
  "No code on this base. Lands on a research.py-bearing cut together
  with D12." The measurement lineage's main.py carries only internal
  search-stage checkpoints, not the operator-facing save/load verbs;
  the engineering lineage has no research.py at all. F1 is blocked on
  the same structural parity that parks the track. Not built this
  turn, by the spec's own sequencing.
- F2 grading script: complete -- tools/f2_grader.sh plus the fixtures
  spec, closed on four fixtures on the porting branch and revalidated
  on this branch's eight transcripts (every count zero; no transcript
  contains a teach).
- F3 negative-control harness: complete -- tools/f3-residual-diff.sh
  with the four-verdict taxonomy (identical / silence-class /
  distinct / incomparable) plus tools/f3_batch_diff.sh for pairwise
  batches, validated on all four pairs, identical on each.
- F4 audit format: complete -- tools/f4_auditor.sh plus the
  historical-audit spec plus the per-pair sheet template
  (tools/f4-sheet.md); the pass-4 pair audits regime A,
  contamination no.

Standing procedure for the next measurement tag:
blank-controls-r2.spec.md is the operators' rerun procedure; this
branch does not run it -- operators are human and external, per INT's
index.

Constraint note for INT: this sandbox is pinned to one branch
(arena/01a06eb9-cat-theo-machine), the same single-branch constraint
INT's index records for their own sandbox. When F unparks, [F] work
proceeds here on this branch, labeled [F], with [SHARED] requests
routed through the index.

## 2026-09-05, acceptance battery -- F2/F3/F4 proven against their own specs on this branch

Earlier entries claimed F2/F3/F4 complete from the port plus spot
checks. The specs demand more: F2's spec states the all-zero null case
is not a pass and hands down a four-fixture oracle including a
nonzero-teach positive control; F3's spec wants the batch matrix; F4's
spec wants sheets on operator transcripts. The fixtures are historical
transcripts of the measurement lineage, now ported to logs/fixtures/
byte-identical to the porting branch's copies (verified by cmp).

Battery run; artifact: logs/f-tools-acceptance-battery-2026-09-05.txt.

- F2 versus oracle: T1 exact including every nonzero path (taught 3,
  unlock 2, cite 2/1); T2 exact (2/0/0/0); T3 exact (1/0/0/0); T4
  exact against the amended oracle (1/1/0/0, cite 0/1).
- One divergence surfaced and resolved: the ported spec's T4 oracle
  said two taught theorems; the ported tool counts one. The porting
  branch's own closing artifact had already amended the T4 hand grade
  to follow the mechanical definition -- teach law and teach trusted
  theorem lines only; the teach dependency verb's evidence lands in
  the unlock counter and in F4's misattribution check -- but its spec
  file was never updated to match. The spec on this branch now carries
  the amended oracle with the amendment recorded inline, so a future
  script is not failed against a stale oracle. No tool was changed;
  the porting branch's closed ruling stands.
- F3 batch matrix over twelve transcripts (four fixtures plus this
  branch's eight): the eight form one identical class (cost=334,
  partial 0, unmatched none, head zero-successor-root);
  ground-evaluation and blind-geometry land in silence-class against
  them (same wall shape, different cost); the incident log's first
  stall (partial match 2) is distinct from every row; batch exit 0,
  every pair comparable. All three verdicts of the taxonomy exercised
  on real transcripts, not constructed ones.
- F4 auditor sheets on the four fixtures: regime B on three, regime C
  with contamination on the restored-checkpoint incident log; the D12
  loaded-class check fires on the two historical logs whose audit
  headers predate the loaded-class list.
- FLT-name grep over every script in tools/: zero hits.

F2, F3, and F4 are now closed on this branch against their own specs,
with the fixtures in-tree and the battery rerunnable. F1 remains
specced and sequenced after a research.py-bearing cut, unchanged from
the previous entry.

## 2026-09-05, post-ratification -- rerunability closed; distinct-case note; F4 sweep empty; F-PROVER cross-referenced

Rerunability (review priority 3): the battery is now a runner,
tools/f-tools-battery.sh -- relative paths only, deterministic output
with no timestamps, and the name-check pattern assembled from
fragments so the checker itself carries none of the tokens it checks
for. The committed artifact
logs/f-tools-acceptance-battery-2026-09-05.txt is regenerated by the
runner, and a rerun from a fresh copy of the tree (tar of the working
tree, .git and runtime state excluded) is byte-identical: verified by
cmp before this commit. One fix landed with it: tools/f3_batch_diff.sh
now resolves its pair tool next to itself first, with the absolute
path demoted to a legacy fallback -- a fresh copy of the tree runs
against its own f3-residual-diff.sh, not another checkout's.

Distinct-case note (review directive): the F3 matrix's one distinct
row -- the incident fixture's first stall, cost=20 with partial match
2 -- is the first measurement in this lineage where a residual
diverged from the SILENCE-334 class. It predates any F3 decoy/target
comparison; its distinctness is from this branch's eight-session
identical class, not from a decoy/target pair, and it is not a
positive F3 reading on a target session. Recorded here so the matrix
row is not misread as one.

F4 sweep (review priority 2): no new operator transcripts exist. The
F-PROVER artifacts that appeared on arena/01a06e7b-cat-theo-machine
(start-gate report, checkpoint audit, harness checks) are instrument
checks, not session transcripts -- the F4 spec's own exclusion rule
(debug dumps are not operator transcripts) applies to them; they
carry no you/hyge dialogue and no session measurement.

F-PROVER cross-reference: its gate items 6, 7, and 10 route the
checkpoint, audit-header, and F2/F3/F4 deliverables to F-tools-eng as
absent. They are absent on its build -- lineage B, which carries none
of the research machinery, the same gap INT's index records as the
reason F is parked. On this branch F2, F3, and F4 are closed on
evidence with the fixtures in-tree and the battery rerunnable, and F1
is specced behind that same structural parity. The F-PROVER defect
ledger is lineage-relative; no item in it requires new work from this
branch beyond what is already recorded here.

Remote check (review priority 1): no research.py-bearing cut exists
or is tagged -- tip 428ecdc, newest tags unchanged through
partition-32bc569. F1 stays parked; the lane's next unblocked item is
the F4 sweep whenever a real operator transcript arrives.

Landing note (second reset): this entry was also committed twice. A
second sandbox reset between turns rebuilt the branch pointer at the
base while the working files survived; the first attempt staged only
the four touched files against a rebuilt index, so its commit dropped
the earlier tree and the push was rejected as non-fast-forward. The
branch was repaired again by fast-forwarding to the pushed tip
(98508d8) and re-landing exactly the four files: the runner, the
batch-tool fix, the regenerated artifact, and this entry. The
post-recovery tree was verified coherent before pushing -- the runner
reproduces the committed artifact byte-identically from it. No
history was rewritten; the remote chain stands.
