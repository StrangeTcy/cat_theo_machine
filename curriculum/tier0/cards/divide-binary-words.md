# Tier0 card — Divide / binary words no adjacent ones (blueprint)

Agent: G/I-op (Agent 3, parallel-unblock lane). **Status: blueprint-only, not training input.**
Ground 2 (statement) state: CLEARED. Ground 1 (constructors) state: OPEN. Ground 3 (count-target) state: PENDING G-COUNT-AUDIT — this card's count target is gated on Ground 3.

> **Pre-finding (this branch, 9ed1fe8):** the intended `Divide` method payload exists but no
> obligation generator is registered in planner.py (no `DivideObligations`/`DivideConclusion`).
> Planner line 1212-1214: "Only Pigeonhole and Extremal are expanded so far; other method terms are
> carried but generate no children." G-COUNT-AUDIT must either confirm this or find the generator; a
> "supported" verdict requires the generator to emit a count-obligation shape, not just to exist.

---

## source statement

> Find the number of binary words of length n that do not contain two adjacent ones.
> (supplied verbatim, recorded in protocol/I.md Turn 3)

## target class: count

## intended method: Divide

Method payload signature (verified in tree, `planner.py`: `class Divide`):
`Divide(parts, combine, rank)` — `rank` is the termination measure that must strictly decrease on
parts. **NOTE: `Divide` has a payload term but NO obligation generator** (verified: no
`DivideObligations`/`DivideConclusion`; planner note line 1213 says "Pigeonhole and Extremal are
expanded so far"). Whether `Divide` can generate a **count** obligation skeleton is exactly **Ground 3**
(G-COUNT-AUDIT decides). This card records the semantic design only; it does NOT assert expressibility.

## exact mathematical target

The count of binary words of length n with no two adjacent ones = F(n+2) (the Fibonacci-shifted
sequence). Verified: a_1 = 2, a_2 = 3, a_n = a_{n-1} + a_{n-2}. Target: closed-form/recurrence count
`F(n+2)`.

## required domain roles

- binary-word (a length-n binary string);
- adjacency predicate (two positions are adjacent iff consecutive);
- the "no two adjacent ones" restriction;
- a parts/recurrence decomposition;
- a combine step joining part counts;
- a rank/termination measure.

## constructor mapping found in tree (real, cited)

Existing, usable in tree: `DivideLabel`, `DividesLabel`, `KnowledgeLabel`, `GoalLabel`, `NatLessLabel`,
`CardinalityLabel`.

## missing constructors

`WordLabel`, `BinaryWordLabel`, `AdjacentLabel` (a binary-word term and an adjacency predicate).
Filing: `protocol/[SHARED]-A1-CONSTRUCTORS.md` (binary-words row). No claim these exist.

## intended obligation sequence

**This is a count target.** The obligations for a count are NOT the proof-reachability shape. Intended
obligations (semantic roles; exact machine terms require the word/adjacency constructors AND a
count-skeleton, which Ground 3 decides):

1. prove the recurrence — a binary word of length n either ends in 0 (count = a_{n-1}) or in 1
   preceded by a 0 (count = a_{n-2}); a_n = a_{n-1} + a_{n-2};
2. prove the base cases — a_1 = 2 (words "0", "1"), a_2 = 3 ("00", "01", "10");
3. **separate obligation** — identify the sequence as F(n+2). Do NOT treat sequence identification as
   supplied merely because the recurrence was proved: matching two base values plus a two-term
   recurrence to the Fibonacci recurrence F(k)=F(k-1)+F(k-2), F(1)=F(2)=1, is a distinct discharge
   (shift indexing by +2).

## required theorem leaves

- recurrence correctness (a_n = a_{n-1} + a_{n-2});
- base case values (a_1 = 2, a_2 = 3);
- the sequence-identification step (a_n = F(n+2)) as its own leaf, not conflated with the recurrence.

## negative controls

- A word length with a single binary alphabet and a "no adjacent ones" rule must NOT be counted as
  2^n (the unrestricted count) — uncontrolled would over-count.
- The recurrence must not be satisfied by a vacuous "both parts are the same" decomposition; a
  genuinely disjoint/exhaustive split is required.

## proof-checker evidence required

- a replayable derivation producing the recurrence and the base cases;
- a distinct derivation producing the sequence identification F(n+2);
- every leaf discharged by existing laws (no inferred-rule applied).

## TrainingRecord promotion gate

Convert card → TrainingRecord only when ALL of:
- Ground 1 clears (INT-SHARED-A1 lands `WordLabel`, `BinaryWordLabel`, `AdjacentLabel`);
- Ground 3 clears (G-COUNT-AUDIT confirms the Divide skeleton can carry a count target); AND
- the record loads through the real `TrainingRecordLoader`, its count goal compiles, and it obtains a
  genuine partial match (not a vacuous label touchdown).
If any gate fails, the record stays blueprint-only.

## current status: blueprint-only, not training input
