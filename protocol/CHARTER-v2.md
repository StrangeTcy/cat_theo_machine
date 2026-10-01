# CHARTER v2

## §2 Tracks and ownership

| Role | Owns | First assignment after preflight |
|---|---|---|
| INT | Shared-change coordination, merge queue, suite admission, immutable tags, protocol index | Verified baseline and interface ownership map |
| S-eng | Contracts, schema mining/instantiation, learned-policy induction, lifecycle tests | S1 contracts |
| E-eng | Explanation substrate, traceable rendering, explanation tests | E1 held-out transfer; respect stop condition |
| G-eng | Five permitted planner methods and obligation skeletons | G1 against inspected planner interface |
| F-tools | Generic checkpoint, grading, negative-control tooling | F1 checkpoint tooling |
| RUN | Read-only execution of supported sessions on a frozen cut | Only after a measurement tag |
| Human operators/curators | Formalizations, approvals, sealed exam, authorized live sessions | Supply and seal records |

F-tools may rotate. The blind F operator is separately qualified.

## §3 G methods (fixed list)

Exactly five:

- Invariance(observable, moveset)
- Extremal(family, measure, direction, variation)
- Pigeonhole(domain, codomain, assignment)
- Divide(parts, combine, rank)
- Symmetry(transformation, domain)

Not Bijection. Not DoubleCount. No sixth method. No `if goal contains …` dispatch. No EvaluateProblem or UsesStrategy facts. G supplies payloads, skeletons, and episodes. S owns policy induction.

Exam results feed learning. Once an exam derivation is released to S or E for training, retire it from future held-out claims for the affected component.

## Freeze amendment

Development and integration-staging commits do not authorize measurements. INT publishes an immutable measurement tag only after the exact candidate SHA has completed the required suite and controls. Sessions remain pinned to their starting tag and checkpoint.

Submissions name base tag and exact commit SHA. INT merges reviewed SHAs, not moving branch tips.
