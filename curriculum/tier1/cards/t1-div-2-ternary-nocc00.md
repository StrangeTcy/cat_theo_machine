# Tier1 card — T1-DIV-2 (Divide, ternary strings no two consecutive zeros)

Agent: G/I-op. **Status: blueprint-only, not training input.** Pool A Tier1 practice. **Count-target.**
Inherits **Ground 3 — RULED-UNSUPPORTED-PENDING-IMPLEMENTATION**.

---

## source statement

> Let a(n) be the number of ternary strings of length n with no two consecutive zeros. Determine a(3).
> (operator Tier1, verified. a(3) = 22.)

## target class: count

## intended method: Divide

Method payload signature (verified): `DivideObligations(parts, combine, rank)`. **The obligation
generator is NOT present at the integration tip — Ground 3 ruling applies.**

## exact mathematical target

Partition the length-n string by its last symbol. If it ends in 1 or 2 (2 options), the prefix of
length n−1 is any valid string → a(n−1) each. If it ends in 0, the previous symbol must be 1 or 2
(2 options) with any valid length-(n−2) prefix → 2·a(n−2). a(n) = 2a(n−1) + 2a(n−2), a(1) = 3,
a(2) = 8. a(3) = 2·8 + 2·3 = 16 + 6 = **22**. Sequence 3, 8, 22, 60, 164, 448. VERIFIED.

## required domain roles

- ternary strings of length n;
- the "no two consecutive zeros" restriction;
- the partition by last symbol (ends 1/2 vs ends 0);
- part count per part;
- recombination into the recurrence.

## constructor mapping found in tree (real, cited)

`DivideLabel`, `DivideObligationsLabel`? **ABSENT** — note the missing obligation generator.
`IntegerLabel`, `CardinalityLabel`, `NatLessLabel`, `ExprAddLabel`, `KnowledgeLabel`, `GoalLabel`,
`TernaryLabel`, `ZeroLabel`, `WordLabel`.

## missing constructors

`WordLabel`, `TernaryLabel`, `ZeroLabel`, `OneLabel`, `TwoLabel`, `StringLabel`. (A2 vocabulary. No
claim exist.)

## Ground 3 ruling (ratifier issued)

`CountTargetUnsupported(Divide, missing_obligation_generator)`. This card is **blueprint-only** until
G1-completion lands **`DivideObligations(parts, combine, rank)`**.

## fixed skeleton shape (per the ruling) — to be satisfied by G-eng G1-completion

`DivideObligations(parts, combine, rank)` must emit, **in order**:
1. `PartitionExhaustive` — the last symbol partition covers all strings;
2. `PartitionDisjoint` — a string has exactly one last symbol (1, 2, or 0);
3. `PartCount` per part — ends-in-symbol counts;
4. `Recurrence` — a(n) = 2a(n−1) + 2a(n−2);
5. `BaseCase` — a(1) = 3, a(2) = 8;
6. then `ClosedForm` as a **SEPARATE** obligation — never discharged by (4)+(5) alone.

Classification must be **SEMANTIC**; the obligation generator must not write to the Knowledge store;
`combine` and `rank` are declared inputs; no `if goal contains` dispatch.

## intended obligation sequence

1. partition (exhaustive, disjoint);
2. part counts;
3. recurrence (combine step);
4. base cases;
5. closed form (separate).

## negative controls

- Ending-in-0 must force a nonzero predecessor (else the "no two consecutive zeros" rule is violated)
  — this doubles the a(n−2) term;
- a(n) = 2a(n−1) + 2a(n−2) (not a(n) = a(n−1) + a(n−2)) — the factor 2 on the 0-ending part is
  load-bearing.

## proof-checker evidence required

- recurrence replayed: a(n) = 2a(n−1) + 2a(n−2);
- base cases a(1)=3, a(2)=8;
- a(3) = 22 discharged;
- `PartitionExhaustive`/`PartitionDisjoint`/`PartCount`/`Recurrence`/`BaseCase`/`ClosedForm` emitted.

## TrainingRecord promotion gate

**Blocked** — convert only when G-eng G1-completion lands `DivideObligations` AND Ground 1 clears AND
record loads + compiles + genuine partial match. Zero partial matches → stays blueprint-only.

## current status: blueprint-only, not training input (Ground 3 pending)
