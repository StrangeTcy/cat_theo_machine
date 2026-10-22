# Tier0 card — Pigeonhole / n+1 integers residue classes (blueprint)

Agent: G/I-op (Agent 3, parallel-unblock lane). **Status: blueprint-only, not training input.**
Ground 2 (statement) state: CLEARED. Ground 1 (constructors) state: OPEN. Ground 3 (count-target) n/a for this card (proof-target).

---

## source statement

> Prove that among any n+1 integers, there exist two whose difference is divisible by n.
> (supplied verbatim, recorded in protocol/I.md Turn 3)

## target class: proposition

## intended method: Pigeonhole

Method payload signature (verified in tree, `planner.py`: `class Pigeonhole`):
`Pigeonhole(domain, codomain, assignment)` — `assignment` sends every element of `domain` to one of
`codomain`. There IS an obligation generator (`PigeonholeObligations`) and a `PigeonholeConclusion`
(verified).

## exact mathematical target

Among any n+1 integers, two have difference divisible by n. Equivalently: the n+1 integers occupy
n residue classes mod n, so two fall in the same class; their difference is ≡ 0 mod n.
Target proposition: `Exists(two, distinct, same-residue-mod-n)`.

## required domain roles

- an integer-set (the n+1 integers);
- a residue/remainder map mod n;
- the n residue classes (the codomain);
- the residue-assignment (each integer → its residue class);
- a congruence relation mod n (difference divisible by n).

## constructor mapping found in tree (real, cited)

Existing, usable in tree: `PigeonholeLabel`, `ModuloLabel`, `CardinalityLabel`, `NatLessLabel`,
`KnowledgeLabel`, `GoalLabel`, `ExtremalLabel`.

## missing constructors

`IntegerLabel`, `IntegersLabel`, `RemainderLabel`, `ResidueLabel`, `CongruentLabel` (an integer-set,
a residue/remainder, and a congruence relation). `ModuloLabel`/`CardinalityLabel`/`NatLessLabel` exist
but do not state "n+1 integers fall into n residue classes." Filing:
`protocol/[SHARED]-A1-CONSTRUCTORS.md` (pigeonhole row). No claim these exist.

## intended obligation sequence

The `PigeonholeObligations` shape applies to a **proposition-closing** target. Intended obligations
(semantic roles; exact machine terms require the integer/residue/congruence constructors):

1. define `domain` = the n+1 integers, `codomain` = the n residue classes;
2. discharge the pigeonhole step: an `assignment` (residue map) from a domain of n+1 elements to a
   codomain of n classes makes two domain elements map to the same class;
3. discharge the conclusion: the two same-class elements have difference ≡ 0 mod n (divisible by n).

## required theorem leaves

- the residue map is well-defined (every integer has a residue mod n);
- pigeonhole: |domain| > |codomain| ⇒ two map to the same class;
- same-residue ⇒ difference divisible by n.
(These are leaves the proof checker must accept; none asserted as present in tree.)

## negative controls

- n+1 integers with **n+1** distinct residues mod n — impossible (pigeonhole fails only if the
  class count is wrong); a "difference divisible by n" claim must NOT be asserted when the codomain
  is under-counted.
- The claim is specifically mod n, not mod n+1 — the divisor must match the residue modulus.

## proof-checker evidence required

- a replayable derivation whose final step is the same-residue ⇒ divisible-by-n conclusion;
- every leaf discharged by existing laws;
- the pigeonhole step (|domain| > |codomain|) recorded explicitly.

## TrainingRecord promotion gate

Convert card → TrainingRecord only when BOTH:
- Ground 1 clears (INT-SHARED-A1 lands `IntegerLabel`, `IntegersLabel`, `RemainderLabel`,
  `ResidueLabel`, `CongruentLabel`) — constructors present; AND
- the record loads through the real `TrainingRecordLoader`, its goal compiles, and it obtains a
  genuine partial match (not a vacuous label touchdown).
If Ground 1 or the partial-match check fails, the record stays blueprint-only.

## current status: blueprint-only, not training input
