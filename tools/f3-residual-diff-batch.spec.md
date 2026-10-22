# F3 residual-diff batch

One pair is not a family. After a re-cut the question is whether walls
differ across a set of goals.

## input

Each transcript contributes one first-stall row:

```text
id
cost
partial-match count
unmatched-premise count
residual head
packs-loaded: yes/no
```

First stall only. Later teaches change the instrument inside the same
process and must not enter the matrix.

## output

NxN identity: two rows are identical when cost, partial-match,
unmatched-premise count, and residual head agree. Packs-loaded is
recorded, not used as an identity key, so a packs-on silence and a
packs-off silence that share cost/head still compare by the four
fields.

Classes: each maximal set of identical rows. Canonical goal: the
lexicographically first goal term in the class (presentation only).

## identity rule (same as the pair harness)

Distinguishable when any of cost / partial-match / unmatched-premise
count / residual head differs. Goal term is not an identity field.

## applied to pre-D11 operator logs on experiment-5-frozen

Class SILENCE-0 (blank-instrument silence, packs not loaded):

```text
cost=0  partial=0  unmatched=none  head=zero-successor-root
  blank-controls-regime-a.log                 (three probes, same class)
  blank-controls-regime-a-postfix.log
  blank-controls-after-goal-directed.log
  blind-geometry-dependencies.log             (first stall)
  blind-group-order-dependencies.log
  blind-narrative-dependencies.log
```

Class SILENCE-334 (packs loaded, still zero partial match):

```text
cost=334  partial=0  unmatched=none  head=zero-successor-root
  set-b1-symbolic-decomposition.log
  set-b2-equality-transport.log
  set-b2-transport-calibration.log
  set-b3-nosolutions-transport.log
  set-b3-transport-calibration.log            (first stall)
  F-OP-BLIND-FLT-RETRY-decoy.log
  F-OP-BLIND-FLT-RETRY-flt.log
```

Class SILENCE-676:

```text
cost=676  partial=0  unmatched=none  head=zero-successor-root
  set-b1-scope-checks.log                     (first stall of this cost)
```

Class SILENCE-4:

```text
cost=4  partial=0  unmatched=none  head=zero-successor-root
  ground-evaluation.log                       ((impossible 4))
```

Partial-match > 0 rows are not silence. They do not join the classes
above. They are post-teach or intra-session and are excluded from the
first-stall matrix except as a note that the process is no longer cold.

## D11 prediction

Every pre-D11 blank control lands in SILENCE-0. Confirmed on the three
blank-control logs. SILENCE-334 is the packs-on sibling of the same
wall, not a second instrument. A post-D11 blank control that remains
in SILENCE-0 or SILENCE-334 is a null fix.

Artifact: `logs/f3-batch-identity-matrix.txt`
