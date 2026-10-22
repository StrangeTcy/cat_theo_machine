# Tier0 G5 held-out — Invariance / seven glasses (second example)

Agent: G/I-op. **Status: blueprint-only, not training input.** G5 held-out.

---

## source statement

> Seven glasses, all upside down; a move flips exactly four glasses. Can all seven end upright?
> (supplied verbatim by operator, G5 held-out list)

## target class: proposition (impossibility)

## intended method: Invariance

Method payload signature (verified in tree): `Invariance(observable, moveset)`; the E2 record uses
`InvarianceLabel` as the method head. Same method as the blackboard-parity Tier0 record, held-out.

## exact mathematical target

Impossibility. Let `u` = number of upright glasses. A move flipping exactly 4 glasses changes `u`
by -4, -2, 0, 2, or 4 — always an **even** amount. Start `u = 0` (even); the target `u = 7` (odd) is
impossible. The parity of `u` is invariant (parity of upright glasses is preserved).

## required domain roles

- 7 glasses, each upright/down;
- a move flips exactly 4;
- the parity of the number of upright glasses (the invariant observable).

## constructor mapping found in tree (real, cited)

`InvarianceLabel`, `ParityLabel`, `EvenLabel`, `OddLabel`, `CardinalityLabel`, `NatLessLabel`,
`KnowledgeLabel`, `GoalLabel`.

## missing constructors

`GlassLabel`, `UprightLabel`, `FlipLabel`, `MoveLabel`, `CountUprightLabel`. (A1 vocabulary. No
claim exist.)

## intended obligation sequence

Same proposition-closing Invariance shape as the E2 record:
1. initial reading: `u = 0` (even);
2. preservation: each move flips exactly 4, so `u` changes by an even amount → parity invariant;
3. target reading: `u = 7` (odd) — the invariant separates start from target;
4. conclusion: unreachable.

## negative controls

- If a move could flip an **odd** number of glasses, parity would not be invariant and the
  impossibility could fail — the "exactly four" (even) is load-bearing;
- the invariant must be parity of `u`, not `u` itself (`u` is not invariant).

## proof-checker evidence required

- move flips 4 ⇒ `Δu` even ⇒ parity of `u` invariant;
- start `u=0` even, target `u=7` odd → separation;
- unreachability conclusion replayed.

## TrainingRecord promotion gate

Convert when Ground 1 clears (glass/upright/flip constructors present) AND the record loads +
compiles + genuine partial match. Zero partial matches → stays blueprint-only.

## current status: blueprint-only, not training input
