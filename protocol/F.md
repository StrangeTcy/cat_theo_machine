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
