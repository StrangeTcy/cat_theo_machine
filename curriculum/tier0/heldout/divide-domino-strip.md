# Tier0 G5 held-out — Divide / 2×n domino strip (second example)

Agent: G/I-op. **Status: blueprint-only, not training input.** G5 held-out. Count-target → inherits
Ground 3, now **RULED-UNSUPPORTED-PENDING-IMPLEMENTATION**
(`CountTargetUnsupported(Divide, missing_obligation_generator)`), + the pre-finding (no Divide
obligation generator registered).

---

## source statement

> Find the number of tilings of a 2×n strip by 1×2 dominoes.
> (supplied verbatim by operator, G5 held-out list)

## target class: count

## intended method: Divide

Method payload signature (verified in tree): `Divide(parts, combine, rank)` — `rank` is the
termination measure. **NOTE: `Divide` has a payload term but NO obligation generator** (pre-finding
on the divide-binary-words card; planner method-expansion loop only handles Pigeonhole and Extremal).
Whether a count-obligation skeleton is expressible is **Ground 3** (G-COUNT-AUDIT decides). This card
does NOT assert expressibility.

## exact mathematical target

Count of 2×n domino tilings. Verified: T(n) = T(n-1) + T(n-2), T(1) = 1, T(2) = 2 → F(n+1).

## required domain roles

- 2×n strip;
- 1×2 domino tile (horizontal or vertical);
- parts/recurrence decomposition;
- combine step;
- rank (termination) measure.

## constructor mapping found in tree (real, cited)

`DivideLabel`, `DividesLabel`, `CardinalityLabel`, `KnowledgeLabel`, `GoalLabel`, `NatLessLabel`.

## missing constructors

`StripLabel`, `DominoLabel`, `TileLabel`, `CellLabel`, `GridLabel`, `TilingLabel`. (A1 vocabulary.
No claim exist.)

## intended obligation sequence (count-target, three-obligation split)

Same split as binary-words:
1. prove the recurrence — T(n) = T(n-1) + T(n-2) (place a vertical domino: T(n-1); place two
   horizontal: T(n-2));
2. prove the base cases — T(1) = 1, T(2) = 2;
3. **separate obligation** — identify the sequence as F(n+1) (shifted Fibonacci); do NOT treat
   sequence identification as supplied merely because the recurrence was proved.

## negative controls

- A 1×n strip (single row) has a different tiling count (1 if even, mismatched) — do not conflate
  the 2×n and 1×n recurrences;
- the base cases must be exact (T(1)=1 not 0, etc.).

## proof-checker evidence required

- recurrence + base cases derived and replayed;
- sequence identification F(n+1) as its own discharge;
- every leaf discharged by existing laws.

## TrainingRecord promotion gate

Convert only when ALL: Ground 1 clears (strip/domino/tile constructors present) AND Ground 3 clears
(G-eng G1-completion lands the `DivideObligations` generator) AND the record loads + compiles +
genuine partial match. Zero partial matches → stays blueprint-only.

## fixed skeleton shape (Ground 3 ruling — to satisfy G-eng G1-completion)

`DivideObligations(parts, combine, rank)` must emit, **in order**: `PartitionExhaustive`,
`PartitionDisjoint`, `PartCount` per part, `Recurrence` (T(n) = T(n-1) + T(n-2)), `BaseCase`
(T(1)=1, T(2)=2), then `ClosedForm` as a **SEPARATE** obligation (T(n) = F(n+1), never discharged by
4+5 alone). Classification SEMANTIC; `combine`/`rank` declared inputs; no `if goal contains` dispatch;
generator must not write to the Knowledge store.

## current status: blueprint-only, not training input (Ground 3 ruling cited)
