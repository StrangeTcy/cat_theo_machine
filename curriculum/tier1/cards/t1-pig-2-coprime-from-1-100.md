# Tier1 card — T1-PIG-2 (Pigeonhole, two coprime from 1..100)

Agent: G/I-op. **Status: blueprint-only, not training input.** Pool A Tier1 practice. Proof-target.

---

## source statement

> Among any 51 numbers chosen from {1, 2, ..., 100} there are two that are coprime.
> (operator Tier1, verified)

## target class: proposition

## intended method: Pigeonhole

Method payload signature (verified): `Pigeonhole(domain, codomain, assignment)`.
`PigeonholeObligations` generator present.

## exact mathematical target

Partition {1..100} into the 50 boxes {1,2}, {3,4}, ..., {99,100}. Consecutive integers are coprime
(any common divisor d divides their difference 1). Choosing 51 numbers forces two into the same box by
pigeonhole → they are consecutive, hence coprime. TRUE.

## required domain roles

- the set {1..100};
- the 50 adjacent-pair boxes;
- coprimality of consecutive integers;
- pigeonhole (51 into 50 boxes).

## constructor mapping found in tree (real, cited)

`PigeonholeLabel`, `CardinalityLabel`, `NatLessLabel`, `ExprAddLabel`, `ExprMulLabel`,
`KnowledgeLabel`, `GoalLabel`, `CoprimeLabel`, `GCFLabel`.

## missing constructors

`IntegerLabel`, `IntegersLabel`, `CoprimeLabel`, `GCFLabel`, `PairLabel`. (A1/A2 vocabulary. No
claim exist.)

## intended obligation sequence

Pigeonhole proof-closing shape (ProofTarget variant):
1. define `domain` = the 51 chosen numbers, `codomain` = the 50 adjacent boxes;
2. discharge pigeonhole (51 into 50 ⇒ two in the same box);
3. discharge coprimality (same box ⇒ consecutive ⇒ coprime).

## negative controls

- 50 numbers are NOT guaranteed to force a collision (50 into 50 may be injective) — the ≤51 count is
  the pigeonhole trigger;
- the box partition must be {1,2},{3,4},... and the coprimality of consecutive integers must hold.

## proof-checker evidence required

- the 50 adjacent-pair boxes;
- pigeonhole collision (51 into 50);
- consecutive ⇒ coprime.

## TrainingRecord promotion gate

Convert when Ground 1 clears (integer/coprime/gcf constructors present) AND record loads + compiles +
genuine partial match. Zero partial matches → stays blueprint-only.

## current status: blueprint-only, not training input
