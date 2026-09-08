# Tier1 card — T1-DIV-1 (Divide, staircase Fibonacci)

Agent: G/I-op. **Status: blueprint-only, not training input.** Pool A Tier1 practice. **Count-target.**
Inherits **Ground 3 — RULED-UNSUPPORTED-PENDING-IMPLEMENTATION**.

---

## source statement

> A staircase has n steps. A person can climb 1 or 2 steps at a time. In how many ways can the
> staircase be climbed to the top? (Count the sequences of 1/2-steps that sum to n.)
> (operator Tier1, verified. Count = F(n+1).)

## target class: count

## intended method: Divide

Method payload signature (verified): `DivideObligations(parts, combine, rank)`. **The obligation
generator is NOT present at the integration tip — Ground 3 ruling applies.**

## exact mathematical target

Let a(n) = number of ways to climb n steps. Partition by the first move: 1 step (leaves n−1) or 2
steps (leaves n−2), disjoint and exhaustive. a(n) = a(n−1) + a(n−2), a(1) = 1, a(2) = 2 →
a(n) = F(n+1). a(3)=3, a(4)=5, a(5)=8, a(6)=13, a(7)=21, a(8)=34, a(9)=55. VERIFIED.

## required domain roles

- the n-step staircase;
- the 1-step / 2-step moves;
- the partition of the move sequence by the first move (PartitionExhaustive, PartitionDisjoint);
- part count per first-move part;
- recombination into the recurrence.

## constructor mapping found in tree (real, cited)

`DivideLabel`, `DivideObligationsLabel`? **ABSENT** — note the missing obligation generator.
`IntegerLabel`, `CardinalityLabel`, `NatLessLabel`, `ExprAddLabel`, `KnowledgeLabel`, `GoalLabel`.

## missing constructors

`StepLabel`, `StairLabel`, `StaircaseLabel`, `PathLabel`, `SeqLabel`, `MoveLabel`. (A2 vocabulary. No
claim exist.)

## Ground 3 ruling (ratifier issued)

`CountTargetUnsupported(Divide, missing_obligation_generator)`. This card is **blueprint-only** until
G1-completion lands **`DivideObligations(parts, combine, rank)`**.

## fixed skeleton shape (per the ruling) — to be satisfied by G-eng G1-completion

`DivideObligations(parts, combine, rank)` must emit, **in order**:
1. `PartitionExhaustive` — the set of first-move parts covers all strings (0 or 1 leading 1-step vs
   2-step);
2. `PartitionDisjoint` — the parts are pairwise disjoint (a string has exactly one first move);
3. `PartCount` per part — the count of strings beginning with a 1-step and with a 2-step;
4. `Recurrence` — a(n) = a(n−1) + a(n−2);
5. `BaseCase` — a(1) = 1, a(2) = 2;
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

- A partition that is not exhaustive (misses the all-2-steps case) under-counts;
- counting via a non-recurrence direct formula would not exercise the divide skeleton.

## proof-checker evidence required

- recurrence replayed: a(n) = a(n−1) + a(n−2);
- base cases a(1)=1, a(2)=2;
- closed form a(n) = F(n+1) discharged separately;
- `PartitionExhaustive`/`PartitionDisjoint`/`PartCount`/`Recurrence`/`BaseCase`/`ClosedForm` emitted.

## TrainingRecord promotion gate

**Blocked** — convert only when G-eng G1-completion lands `DivideObligations` AND Ground 1 clears AND
record loads + compiles + genuine partial match. Zero partial matches → stays blueprint-only.

## current status: blueprint-only, not training input (Ground 3 pending)
