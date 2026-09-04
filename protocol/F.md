# Track F -- FLT programme tooling and audit

Ledger entries for this track. Newest last. See protocol/README.md for
the rules governing entries, and research_protocol.md for cross-track
discipline.

---

## session-pair: F-OP-BLIND-FLT-RETRY

```text
session-pair: F-OP-BLIND-FLT-RETRY
tag: experiment-5-frozen
processes: two fresh; decoy first, FLT second
role: F-OP-BLIND
cold-start audit: packs 167, taught 0, episodes 0, policies none (both)
artifacts:
  logs/F-OP-BLIND-FLT-RETRY-decoy.log
  logs/F-OP-BLIND-FLT-RETRY-flt.log
  logs/F-OP-BLIND-FLT-RETRY-report.txt
  logs/fable-5.1.txt
decoy goal:  (forall n (implies (greater n 1) (over positive-integers (vars x y) (implies (eq (pow x n) (pow y n)) (eq x y)))))
flt   goal:  (forall n (implies (greater n 2) (nosolutions positive-integers (unknowns a b c) (eq (plus (pow a n) (pow b n)) (pow c n)))))
cost:                     334 / 334
partial-match rules:      0   / 0
unmatched concrete prem:  none/ none
dependency characterized: no  / no
residual:                 zero-successor-root, both
classification:           A   / A
teaching applied:         none
retry:                    not run (nothing to retry on)
verdict:                  substantially identical -> reading withdrawn on FLT
                          pre-flight step 3 confirmed empirically
follow-on defect (instrument-level, not FLT-level):
  ZeroPartialMatchAmbiguity -- the matcher cannot yet distinguish
  "no rule could match this shape" from
  "the partial-match criterion is too coarse to register a candidate."
  Same question the swallowed-exception pre-flight surfaces, now visible
  at the FLT wall. Route to S/INT as an instrument concern, not to F as
  a theorem gap.
```

Predicted: a shape-matched decoy and the FLT sentence would either
separate (F3 distinguishable residuals) or not (reading withdrawn).

Run: detached frozen tag, two fresh processes, packs loaded, no taught
rules, no shared checkpoint. Teaching withheld. Report block is the F3
diff.

Came back: identical stall shape, identical cost 334, partial match 0,
dependency characterized no. Classification A / A. Reading withdrawn
on FLT. Pre-flight step 3 closed empirically. F1 acceptance not opened.

Blocked by this pair:

- no teaching on the FLT goal (no concrete residual)
- no Experiment 4 (instrument returns the same wall on the decoy)
- no `Blocked(FLT, <capability-name>)` term (zero-successor root is not
  a named missing capability)

Unblocked by this pair:

- `ZeroPartialMatchAmbiguity` as an instrument-level item on S/INT
- other tracks on the frozen tag continue; this null does not gate them

### nosolutions pair on this tag (two-line note)

On `experiment-5-frozen`, `nosolutions` appears in zero pack rules:
neither producer nor consumer is LIBRARY_THEOREM. The F-OP-BLIND
sessions loaded packs only (taught 0), so `attempted operational
rules: 0` is absence of a candidate, not a matcher rejection of a
present MultiRule.

### follow-on (named, not solved)

`ZeroPartialMatchAmbiguity` — whether empty partial-match is "no rule
could match this shape" or "the criterion is too coarse to register a
candidate." Route to S/INT. Not a theorem gap. Not solved here. No
third knock on this pair until residuals distinguish.

---

## INT status after F-OP-BLIND-FLT-RETRY

```text
pre-flight item 2:  OPEN — nosolutions producer/consumer absent on experiment-5-frozen
                    (zero pack rules with that head; F confirmed, packs-only, taught 0)
                    owned by INT/SHARED; enters through a [SHARED] commit and a re-cut
                    F-op does not construct it
defect 1:           evidence updated — decoy zero not attributable to item 2;
                    diagnostic still required before ruling
F-OP-BLIND-FLT-RETRY:
                    closed as a measurement pair
                    no third knock until the instrument changes
F track:
                    ACTIVE
                    continue checkpoint tooling, grading, transcript audits,
                    residual-diff harness work, and preparation for post-cut
                    blank controls
```

Pre-flight step 2 was never satisfied on `experiment-5-frozen`. Zero
pack rules with a `nosolutions` head means the producer/consumer pair
was proposed but never landed on the tag.

The decoy zero is the stronger signal. The decoy goal contains no
`nosolutions`; its inner structure is `over` / `implies` / `eq` /
`pow`, and `pow` and `eq` have heads in the 167-rule library. Zero
candidates there cannot be explained by `nosolutions` absence. The
missing pair accounts for at most the FLT zero, not the decoy zero.
That leans the ruling toward (a) structural — the `forall`/`implies`
wrapper is not being decomposed — but leaning is not evidence. The
diagnostic (wrap an already-solved goal in
`(forall n (implies (greater n 1) …))`, cold start, packs loaded,
count partial matches) is still what decides it, and it is a session
on the frozen tag, not a commit.

This session pair is exhausted; the F lane is not. No third knock on
the decoy/FLT pair until the instrument changes. Blank controls after
any re-cut, before a measurement counts. All unblocked F tooling
continues in parallel.

---

## disposition correction

Predicted: "do not repeat this specific null experiment" equals "stop
the F lane."

Came back: that conversion is false. The pair is closed; the track is
active.

```text
F-OP-BLIND-FLT-RETRY:
  closed as a measurement pair
  no third knock until the instrument changes

F track:
  ACTIVE
  continue checkpoint tooling, grading, transcript audits,
  residual-diff harness work, and preparation for post-cut blank controls

F-op:
  audit operator transcripts and prepare blank controls
  do not repeat the decoy/FLT pair on unchanged semantics
```

---

## F3 residual-diff (applied to F-OP-BLIND-FLT-RETRY)

Harness fields, both columns, then the identity test. Not a verdict.
A pair is distinguishable when any field differs other than the goal
term itself.

```text
field                         decoy                         FLT
cost                          334                           334
partial-match rules           0                             0
unmatched concrete premises   none                          none
dependency characterized      no                            no
residual head                 zero-successor-root           zero-successor-root
attempted operational rules   0                             0
classification                A                             A
goal term                     (forall n (implies            (forall n (implies
                               (greater n 1) (over           (greater n 2)
                               positive-integers ...)))      (nosolutions ...)))
identity test                 identical except goal term
F3                            reading withdrawn
```

Artifact: `logs/F-OP-BLIND-FLT-RETRY-residual-diff.txt`

---

## F1 checkpoint verbs (open)

On `experiment-5-frozen`, research state persists only as
`snapshots/research_snapshot.json` written as a side effect. No `save
checkpoint` / `load checkpoint` verbs, no content-addressed ids.
DISTRIBUTION names this F-tooling. It lands on a cut that carries
`research.py`, not on a session branch that does not. Status: OPEN.

---

## post-cut blank controls (prep, not run)

After INT re-cuts, before any F measurement counts:

```text
1. fresh process, declared tag only
2. research mode on
3. load theorem packs
4. audit knowledge  -- packs loaded, taught 0, episodes 0, policies none
5. prove one already-closed library sentence (not FLT, not the decoy)
6. record cost, partial-match, residual
7. fresh process; repeat 2-4; run the decoy; record the F3 block
8. compare to F-OP-BLIND-FLT-RETRY decoy column (cost 334, match 0)
9. FLT one-shot only if the decoy column differs from that baseline
   or from the library-closed column in a field other than the goal
```

Not run on unchanged `experiment-5-frozen` semantics. Repeating the
decoy/FLT pair here would reproduce the same null.

---

## grading of F-OP-BLIND-FLT-RETRY

Role-coverage grading of the one-shot is withdrawn with the F3 reading.
The transcript is evidence that the instrument cannot separate
one-shot stalls from shape-matched decoy stalls. Recall-eligible and
discovery-eligible roles are not scored on an UncharacterizedStall
with zero partial matches.

---

## merge routing

```text
ready for docs/log merge: yes, if INT accepts measurement artifacts
ready for F1 code merge: no, blocked on research.py-bearing cut
```

INT can pull ledger/log artifacts without waiting for F1 verbs.

---

## F lane next work (allowed)

```text
F1:
  save checkpoint <name>
  load checkpoint <name>
  content-addressed ids
  audit prints loaded checkpoint
  status: OPEN, blocked on research.py-bearing cut

F2:
  grading table
  role-table coverage
  circular-request count
  computable-request count
  taught-theorem count by provenance
  unlock evidence per teach
  no famous-sentence names in the table definition
  status: format landed; applied to F-OP-BLIND-FLT-RETRY

F3:
  residual-diff harness
  classify identical/different residuals
  preserve raw residual records
  status: applied; pair identical except goal term

F4:
  transcript audit format
  Regime A/B/C/contamination classification
  verify each teach follows concrete residual
  status: format landed; applied to F-OP-BLIND-FLT-RETRY
```

---

## F2 grading table (definition; no famous-sentence names)

Count only what the transcript prints. Roles are filled after F3
says distinguishable; on an identical pair the role table is skipped.

```text
circular-request count:     requests that restate the parent goal
computable-request count:   requests dischargeable by ground evaluation
taught-theorem count:       HUMAN_SUPPLIED_TRUSTED_THEOREM lines
  of which with unlock:     DemonstratedUsefulDependency
  of which without unlock:  HUMAN_SUPPLIED_TRUSTED_THEOREM_WITHOUT_UNLOCK_EVIDENCE
role-table coverage:        skipped unless F3 = distinguishable
```

Applied to F-OP-BLIND-FLT-RETRY:

```text
circular-request count:     0
computable-request count:   0
taught-theorem count:       0
  with unlock:              0
  without unlock:           0
role-table coverage:        skipped (F3 identical)
```

Artifact: `logs/F-OP-BLIND-FLT-RETRY-F2-grading.txt`

---

## F4 transcript audit format

```text
session-id:
tag:
processes: fresh / reused
cold-start taught / episodes / policies / packs:
regime: A library-only | B research one-shot | C cumulative
contamination: yes/no
  if yes: taught-at-boot / shared-checkpoint / curriculum-in-B / oracle-in-prompt
teaches:
  each: residual-cited yes/no; circular yes/no; computable yes/no
F3 vs decoy: identical | different | decoy-not-run
```

Applied to F-OP-BLIND-FLT-RETRY:

```text
session-id: F-OP-BLIND-FLT-RETRY
tag: experiment-5-frozen
processes: two fresh
cold-start: taught 0 / episodes 0 / policies none / packs 167
regime: B research one-shot, decoy first
contamination: no
teaches: none
F3 vs decoy: identical
```

Artifact: `logs/F-OP-BLIND-FLT-RETRY-F4-audit.txt`

---

## F-eng active work (docs-only, this base)

Five items in flight. Not F1 code. Not a third knock.

```text
F2 hardening:  tools/f2-grading-fixtures.spec.md
               fixtures T1-T4 from existing transcripts
               all-zero withdrawn pair is not a pass
F3 batch:      tools/f3-residual-diff-batch.spec.md
               logs/f3-batch-identity-matrix.txt
               pre-D11 blanks all SILENCE-0 -- D11 prediction confirmed
F4 historical: tools/f4-audit-historical.spec.md
               logs/f4-historical-audits.txt
               DEFECT: loaded-class list missing on eight first audits
blank r2:      tools/blank-controls-r2.spec.md  staged, not run
contamination: logs/pre-D11-instrument-class.txt
               one line per log; logs not rewritten
sealed-oracle: protocol/SEALED-ORACLES.spec.md
               format only; seal not executed
```

Computable-request count across the F2 fixtures: 0. No defect of that
locus surfaced. Loaded-class-list defects are F4, filed above.

---

## D12 — AuditHeaderOmitsLoadedClasses

Filed from the F4 sheets. See `protocol/D12-AuditHeaderOmitsLoadedClasses.md`.

```text
locus:      research-mode `audit knowledge` output, first audit of a session
observed:   eight first audits carry no loaded-class list
class:      instrument-level, non-semantic
routing:    INT [SHARED]; lands with F1 verbs on the research.py-bearing cut
logs:       not rewritten
```

## F next-work this turn

```text
1. commit + push; ls-remote confirmation
2. F2 T1 nonzero paths: logs/f2-T1-toy-live-protocol-grading.txt
3. F3 tool: tools/f3-residual-diff.sh  exit 0 identical / 1 distinct / 2 incomparable
   verified: decoy vs FLT -> identical, exit 0
4. F1 spec docs-only: tools/f1-checkpoint-verbs.spec.md (closes D12 by construction)
5. F4 sheet: logs/f4-defect-1-ruling-diagnostic.txt (log absent; incomparable)
```

Not touched: research.py, main.py, packs, parser, decoy/FLT pair.

---

## request to INT

```text
request to INT: publish logs/defect-1-ruling-diagnostic.log
                to a path reachable from F's base, or include it
                in the next docs/log merge batch
reason: F4 audit sheet cannot be completed without the transcript
priority: low — does not block any code or measurement
```

The log lives on INT's integration branch, not on this branch. The F4
sheet stays incomparable until the transcript is published.

---

## T1 session-hygiene defect

```text
T1 toy-live-protocol: one claim without dated artifact
locus: logs/fixtures/toy-live-protocol.log line 18
       you> teach law: (rule (premises (rel ?x ?y) (mark ?y)) (conclusion (tag ?x)))
       first FAILED. cost= is line 23
class: session-hygiene defect, non-semantic
repair: none to the log; future sessions cite or do not claim
surfaced-by: tools/f2_grader.sh cite-coverage uncited: 1
```

The grader found this by running. It is a defect in the session, not
in the grader.

---

## F2 grader

`tools/f2_grader.sh <transcript>` emits taught, unlock-evidence,
circular, computable, cite-coverage. T1 fixture is
`logs/fixtures/toy-live-protocol.log`.

```text
T1 expected: taught 3, unlock 2, circular 0, computable 0, cite 2/1
null decoy:  all zeros
```

---

## status

```text
agent: F
branch: arena/01a06da9-cat-theo-machine
base: 41e8078
tests: F2 T1 taught 3 unlock 2 cite 2/1; F3 decoy/FLT identical exit 0
measurement: none (pair closed; no third knock)
pair status: closed
track status: active
ready for INT docs/log merge: yes
ready for F1 code merge: no
blocked on: INT publishing diagnostic log (low priority)
```
