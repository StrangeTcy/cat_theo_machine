# Engel E2 — blackboard parity invariant

Numbers `1, 2, ..., 2n` stand on a board. A move erases two of them, `a` and `b`, and writes
`|a - b|`. When `n` is odd, the last remaining number is odd.

Nothing in this encoding simulates a board. There is no board cell, no position index, no move
order, and no concrete arithmetic on `1..2n`. The proof is one symbolic preservation obligation,
one initial-parity computation, and one terminal readout.

## Ontology

Added to `labels.py`:

| label | meaning |
| --- | --- |
| `BoardSumLabel` | `BoardSum(state, value)` — the observable |
| `ParityLabel` | `Parity(value, bit)` where `bit` is `Odd` or `Even` |
| `IsEvenLabel` | `Even(value)` |
| `AbsDiffLabel`, `MinLabel` | `AbsDiff(a, b)`, `Min(a, b)` |
| `MoveErasesLabel` | `MoveErases(before, a, b, after)` — the legal move, over arbitrary `a`, `b` |
| `InitialBoardLabel`, `FinalNumberLabel`, `TerminalLabel` | the two ends of the run |
| `BlackboardProblemLabel`, `BoardSumObservableLabel` | subjects of `Invariant(problem, observable)` |
| `OddLabel`, `EvenLabel` | the two parity atoms |

`PreservesLabel` and `InvariantLabel` are reused from the E1 coin work unchanged.

Phi is `Parity(BoardSum, ?p)` — the same shape as E1's `HeadsCountParity(?p)`, with the
observable swapped.

## The move, at the level of the observable

`EraseAndReplaceRule` takes

```
BoardSum(before, S), Parity(S, p), Parity(BoardSum, p), MoveErases(before, a, b, after)
```

to

```
BoardSum(after, S - 2*Min(a, b)), Parity(S - 2*Min(a, b), p), Parity(BoardSum, p)
```

The `-2·Min(a,b)` figure is not asserted. It is derived by two term rewrites, checked
independently in `blackboard_move_sum_is_sum_minus_twice_min_test`:

- `AbsDiffRewriteRule`: `AbsDiff(a, b) -> (a + b) - 2*Min(a, b)`
- `CancelErasedNumbersRule`: `((S - a) - b) + ((a + b) - d) -> S - d`

so `S - a - b + AbsDiff(a, b)` rewrites to `S - 2*Min(a, b)` over symbolic `a` and `b`.

The parity step itself is `DoublingIsEvenRule` (`Even(2k)`) followed by
`SubtractEvenPreservesParityRule` (`Parity(x, p), Even(d) -> Parity(x - d, p)`).

`Preserves(EraseAndReplace, Phi)` is discharged once, over arbitrary `a` and `b`. No move order
is ever enumerated.

## Initial parity

`InitialBoardSumRule` is the named sum lemma `1 + 2 + ... + 2n = n(2n+1)`, taken as a given and
never unfolded into `2n` additions. From `Parity(n, Odd)`:

- `TwoKPlusOneIsOddRule` gives `Parity(2n+1, Odd)`
- `ParityOfProductRule(Odd, Odd, Odd)` gives `Parity(n(2n+1), Odd)`

## Terminal readout

`TerminalReadoutRule` fires only when `Invariant(BlackboardProblem, Parity(BoardSum))`,
the current reading `Parity(BoardSum, p)`, and `Terminal(state)` are all present, and concludes
`Parity(FinalNumber, p)`. There is no path to `Parity(FinalNumber, ...)` that bypasses the
invariant.

## Tests

Registered in `testsuite.py`:

| test | checks |
| --- | --- |
| `blackboard_parity_preserved_test` | `Preserves(EraseAndReplace, Parity(BoardSum))` and `Invariant` hold |
| `blackboard_move_sum_is_sum_minus_twice_min_test` | the `AbsDiff` / cancellation rewrites reach `S - 2*Min(a,b)` |
| `blackboard_initial_parity_is_odd_test` | `Odd(n)` yields `Parity(n(2n+1), Odd)` |
| `blackboard_final_number_is_odd_test` | `Parity(FinalNumber, Odd)` is derivable **and** its derivation applies a rule with `Invariant` among its premises |
| `blackboard_even_n_refuses_odd_conclusion_test` | with `Even(n)` the machine derives `Even` and cannot derive `Odd` |
| `blackboard_proof_expands_no_boards_test` | `expanded` is zero — the obligation is discharged without search |
| `blackboard_start_has_no_board_cells_test` | the start state mentions only `InitialBoard`, `Parity`, `Terminal`, `Invariant` |

## Pack

`packs/engel-blackboard.pack.yaml` carries the same thirteen rules in YAML, with the example
`engel_e2_final_number_is_odd`. It is loaded by `main.py` and reachable from the theorem agenda
under the filters `blackboard`, `e2`, `engel-blackboard`, and `all`.

## Repairs made along the way

`HEAD` did not boot. Three unrelated breakages had to be fixed first:

- `labels.py` was missing `IncreasingLabel`, `DecreasingLabel`, `BoundedAboveLabel`,
  `BoundedBelowLabel`, `ConvergesLabel`, `GapContractsLabel`, and `LimitValueLabel`, all of which
  `invariance.py` and `sequence-order.pack.yaml` already referenced. Pack loading raised
  `Unknown symbol in pack: GapContractsLabel`.
- `search/compare_rules.py` was missing the `from .model import *` its sibling modules carry, so
  `SearchModeText` was undefined at test-install time.
- `paused_comparison_job_snapshot_roundtrip_test` compared an unevaluated `Head` edge against a
  label instead of its result.
