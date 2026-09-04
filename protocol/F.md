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
