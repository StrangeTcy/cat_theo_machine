# Tier1 card — T1-INV-1 (Invariance, board |a−b| erasure)

Agent: G/I-op. **Status: blueprint-only, not training input.** Pool A Tier1 practice — UNSOURCED (agent-authored statement; not convertible until operator supplies). Proof-target.

---

## source statement

> The integers 1 through 10 are written on a board. A move erases two numbers a, b and writes
> |a − b|. Prove the last remaining number is odd.
> **(UNSOURCED: agent-authored statement, NOT operator-supplied.)**

## target class: proposition

## intended method: Invariance

Method payload signature (verified): `Invariance(observable, moveset)`. Method head
`InvarianceLabel`.

## exact mathematical target

Last remaining number odd. Invariant: parity of the sum of all numbers on the board. The total sum
is `1+...+10 = 55` (odd); the operation `|a−b|` satisfies `|a−b| ≡ a+b (mod 2)`, so the sum's parity
is preserved. Starting sum 55 (odd) → final single number must be odd.

## required domain roles

- the board multiset of integers;
- the move (erase a, b, write |a−b|);
- the sum parity observable;
- preservation of sum parity under the move.

## constructor mapping found in tree (real, cited)

`InvarianceLabel`, `ParityLabel`, `OddLabel`, `EvenLabel`, `AbsDiffLabel`, `BoardSumObservableLabel`,
`InitialBoardLabel`, `CardinalityLabel`, `ExprAddLabel`, `KnowledgeLabel`, `GoalLabel`.

## missing constructors

`BoardLabel`, `NumberLabel`, `EraseLabel`, `MoveLabel`. (A1/A2 vocabulary. No claim exist.)

## intended obligation sequence

Invariance proof-closing shape:
1. initial reading (sum parity = odd, sum = 55);
2. preservation (each move preserves sum parity since |a−b| ≡ a+b mod 2);
3. target reading (final single number = odd).

## negative controls

- If the operation preserved sum parity differently (e.g. a move that changed parity), the claim
  would fail — the mod-2 relation is load-bearing;
- a start sum even (e.g. 1..9 = 45 is odd anyway; use a 1..11 start = 66 even) would give an even
  final — the invariant must be matched to the actual start.

## proof-checker evidence required

- sum = 55 (odd) at start;
- |a−b| ≡ a+b mod 2 (parity preserved);
- final single number odd, replayed.

## TrainingRecord promotion gate

Convert when Ground 1 clears (board/number/erase constructors present) AND record loads + compiles +
genuine partial match. Zero partial matches → stays blueprint-only.

## current status: blueprint-only, not training input
