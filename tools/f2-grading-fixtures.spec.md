# F2 grading fixtures

The null-pair F2 sheet is zeros. That does not grade. Fixtures below
are historical non-famous-sentence transcripts on `experiment-5-frozen`.
The table definition still names no famous sentence.

Procedure: count only printed lines. Hand-grade once; later script
runs must match these counts exactly.

## counters

```text
circular-request count
computable-request count
taught-theorem count
  with unlock     (DemonstratedUsefulDependency)
  without unlock  (WITHOUT_UNLOCK_EVIDENCE or stored-without-unlock)
role-table coverage   skipped unless F3 = distinguishable for that session
```

A nonzero computable-request count is a defect, filed by locus.

## fixture T1 — toy-live-protocol.log

Teach present, residual present, unlock present.

```text
teaches printed:            3  (rel/mark/tag; link/mark/badge; ring/mark/crown)
concrete residuals:         yes  (mark _0), twice useful
circular-request count:     0
computable-request count:   0
taught-theorem count:       3
  with unlock:              2  (first two episodes DemonstratedUsefulDependency)
  without unlock:           0  (third teach measured; episodes show two useful)
role-table:                 skipped (no decoy pair in this log)
teach preceded by residual: first teach is before any residual (axiom then teach)
                            -- F4 flags that teach; F2 still counts the teach
```

Hand-grade note: line 18 teach precedes the first FAILED residual
(line 23). That teach is not residual-cited. F2 counts it; F4 marks
the cite-check false for that teach.

### T1 nonzero-path assertion

The withdrawn pair exercised every counter at 0. T1 must fail a
harness that only emits zeros.

```text
taught-theorem count:       3     nonzero
unlock-evidence count:      2     nonzero  (DemonstratedUsefulDependency)
cite-coverage cited:        2     nonzero
cite-coverage uncited:      1     nonzero
circular-request count:     0
computable-request count:   0
```

Cite-coverage is the role-coverage path when no decoy pair exists:
residual-cited teaches versus uncited teaches. A harness that skips
T1 because F3 is N/A has not exercised the nonzero paths.

Expected output artifact: `logs/f2-T1-toy-live-protocol-grading.txt`
A run that prints all zeros against T1 is a harness defect.

## fixture T2 — ground-evaluation.log

Teach present. Ground arithmetic discharged as DOMAIN_AXIOM, not as a
request.

```text
teaches printed:            2
circular-request count:     0
computable-request count:   0
taught-theorem count:       2
  with unlock:              0  (first two goals closed SEARCH_DERIVED; no episode)
  without unlock:           0  (no WITHOUT_UNLOCK line printed)
factorizations:             (eq 6 (times 2 3)), (eq 21 (times 3 7))
                            audited DOMAIN_AXIOM -- not requests
(odd 4):                    COUNTEREXAMPLE -- not a request
(impossible 4):             FAILED cost=4; partial match 0; UncharacterizedStall
```

Computable count 0 here is the calibration succeeding, not a script
blindness. A later transcript that emits a request for a ground
equation fails this fixture's invariant.

## fixture T3 — blind-geometry-dependencies.log

Teach present, residual present after first stall.

```text
teaches printed:            1
circular-request count:     0
computable-request count:   0
taught-theorem count:       1
  with unlock:              0  (retry still FAILED cost=1; partial match 1)
  without unlock:           1  unless a DemonstratedUseful line exists -- none printed
first stall:                cost=0; partial match 0; UncharacterizedStall
after teach:                cost=1; partial match 1
teach preceded by residual: yes (stall then teach law)
```

## fixture T4 — incident-misattributed-teaching.log

Teach present, concrete unmatched premises present.

```text
teaches printed:            2  (teach law; teach dependency 2)
circular-request count:     0
computable-request count:   0
taught-theorem count:       2 plus 4 already in the restored checkpoint
concrete residuals:         missing (eq (plus p q) ?y);
                            missing (solutionmap ...)
F4 extra:                   pairing request 2's residual with request 3's
                            rule -- misattribution, already named in the log
```

Restored checkpoint at boot (taught 4, episodes 2) is Regime C, not a
cold A. F2 counts only teaches printed in this transcript body unless
the audit header is being scored (F4).

## check

Hand-graded counts above are the oracle for a future script. A script
that only reproduces the all-zero withdrawn pair has not passed F2.
