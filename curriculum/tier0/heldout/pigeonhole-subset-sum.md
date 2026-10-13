# Tier0 G5 held-out — Pigeonhole / subset sum divisible by n (second example)

Agent: G/I-op. **Status: blueprint-only, not training input.** G5 held-out.

---

## source statement

> Among any n integers there is a nonempty subset whose sum is divisible by n.
> (supplied verbatim by operator, G5 held-out list)

## target class: proposition

## intended method: Pigeonhole

Method payload signature (verified in tree): `Pigeonhole(domain, codomain, assignment)`.
`PigeonholeObligations` generator present. Same method as the pigeonhole Tier0 card, held-out.

## exact mathematical target

A nonempty subset with sum ≡ 0 mod n. Prefix-sums argument: the n prefix sums `s_1,...,s_n` plus
the empty prefix sum `0` give n+1 values mod n into n residue classes → two equal prefix sums →
their difference is a contiguous (nonempty) subset sum divisible by n.

## required domain roles

- the n integers;
- prefix sums (n+1 values incl. 0);
- residue classes mod n;
- pigeonhole (n+1 values into n classes).

## constructor mapping found in tree (real, cited)

`PigeonholeLabel`, `ModuloLabel`, `CardinalityLabel`, `NatLessLabel`, `ExprAddLabel`, `ExprMulLabel`,
`KnowledgeLabel`, `GoalLabel`.

## missing constructors

`IntegerLabel`, `IntegersLabel`, `RemainderLabel`, `ResidueLabel`, `CongruentLabel`,
`PrefixSumLabel`, `SubsetLabel`. (A1 vocabulary. No claim exist.)

## intended obligation sequence

Same proposition-closing shape as the pigeonhole Tier0 card:
1. define `domain` = the n+1 prefix sums (incl. 0), `codomain` = the n residue classes mod n;
2. discharge pigeonhole (n+1 into n ⇒ two equal residues);
3. discharge the conclusion (the difference of two equal-residue prefix sums is a nonempty subset
   sum divisible by n).

## negative controls

- fewer than n+1 values (e.g. only n prefix sums without the 0) → pigeonhole may not force a
  collision; the subset-sum claim must fail;
- the empty prefix sum `0` is essential (it supplies the "empty subset" boundary and nonempty-ness
  of the final subset is by the difference).

## proof-checker evidence required

- prefix-sum definition (s_0 = 0, s_{i+1} = s_i + a_{i+1});
- pigeonhole collision (two equal residues among n+1 values);
- subset-sum = difference of two prefix sums, nonempty and divisible by n.

## TrainingRecord promotion gate

Convert when Ground 1 clears (integer/residue/congruence constructors present) AND the record loads +
compiles + obtains a genuine partial match. Zero partial matches → stays blueprint-only.

## current status: blueprint-only, not training input
