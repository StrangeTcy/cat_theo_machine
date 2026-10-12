# Tier1 card — T1-PIG-1 (Pigeonhole, sum/difference divisible by 100)

Agent: G/I-op. **Status: blueprint-only, not training input.** Pool A Tier1 practice — UNSOURCED (agent-authored statement; not convertible until operator supplies). Proof-target.

---

## source statement

> Among any 52 integers there exist two whose sum or difference is divisible by 100.
> **(UNSOURCED: agent-authored statement, NOT operator-supplied.)**

## target class: proposition

## intended method: Pigeonhole

Method payload signature (verified): `Pigeonhole(domain, codomain, assignment)`.
`PigeonholeObligations` generator present.

## exact mathematical target

Consider residues mod 100: the class {0}, the class {50}, and the 49 paired classes {r, 100−r} for
r = 1..49 — total **51 boxes**. Any 52 integers occupy 51 residue boxes; two must be in the same box,
so their sum or difference is divisible by 100. TRUE.

## required domain roles

- the 52 integers;
- residues mod 100;
- the 51 residue boxes ({0}, {50}, {r,100−r});
- pigeonhole (52 into 51 boxes).

## constructor mapping found in tree (real, cited)

`PigeonholeLabel`, `ModuloLabel`, `CardinalityLabel`, `NatLessLabel`, `ExprAddLabel`, `ExprMulLabel`,
`KnowledgeLabel`, `GoalLabel`.

## missing constructors

`IntegerLabel`, `IntegersLabel`, `RemainderLabel`, `ResidueClassLabel`, `ResidueLabel`, `KnowledgeLabel`. (A1/A2
vocabulary. No claim exist.)

## intended obligation sequence

Pigeonhole proof-closing shape:
1. define `domain` = the 52 integers, `codomain` = the 51 residue boxes;
2. discharge pigeonhole (52 into 51 ⇒ two in the same box);
3. discharge the conclusion (two in {r,100−r} have sum or difference ≡ 0 mod 100).

## negative controls

- 51 integers are NOT guaranteed to force a collision (51 into 51 boxes may be injective) — the ≤52
  count is the pigeonhole trigger;
- the {0}/{50}/{r,100−r} box construction must be correct (the distance-to-0/50 pairing).

## proof-checker evidence required

- the 51-box residue classification;
- pigeonhole collision (52 into 51);
- same-box ⇒ sum-or-difference ≡ 0 mod 100.

## TrainingRecord promotion gate

Convert when Ground 1 clears (integer/residue/remainder constructors present) AND record loads +
compiles + genuine partial match. Zero partial matches → stays blueprint-only.

## current status: blueprint-only, not training input
