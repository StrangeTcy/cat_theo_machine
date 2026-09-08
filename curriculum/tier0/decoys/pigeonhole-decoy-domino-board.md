# Tier0 G4 decoy — Pigeonhole / domino board (negative-control decoy)

Agent: G/I-op. **Status: blueprint-only, not training input.** G4 decoy.

---

## source statement

> An 8×8 board with two opposite corners removed; can it be tiled by 31 dominoes (each covering two
> adjacent squares)?
> (supplied verbatim by operator, G4 decoy list)

## target class: proposition (impossibility / existence)

## surface shape (what a method might latch onto)

Counting language: 62 squares, 31 tiles → could trigger **Pigeonhole** (count / distribute).

## intended method (the trap): Pigeonhole (decoy)

The correct method is **Invariance** (checkerboard coloring). The two removed corners are the same
color, so the board has 32 squares of one color and 30 of the other; each domino covers exactly one
of each color. 31 dominoes would need 31 of each color — impossible. Pigeonhole must NOT fire.

## exact mathematical target

Impossibility: 31 dominoes would require 31 black + 31 white squares, but the board has 32 of one
color and 30 of the other (because the opposite corners share a color).

## required domain roles

- 8×8 board, two opposite corners removed;
- checkerboard 2-coloring;
- color counts (32 vs 30);
- domino = one cell of each color;
- invariance of the color-count difference.

## constructor mapping found in tree (real, cited)

`InvarianceLabel`, `ParityLabel`, `ColoringLabel` (NOT present — see missing), `CardinalityLabel`,
`NatLessLabel`, `KnowledgeLabel`, `GoalLabel`, `PigeonholeLabel`.

## missing constructors

`BoardLabel`, `CellLabel`, `SquareLabel`, `DominoLabel`, `TileLabel`, `ColoringLabel`,
`CheckerboardLabel`, `CornerLabel`, `ColorLabel`. (A1 vocabulary. No claim exist.)

## negative controls

The Pigeonhole-vs-Invariance distinction is the control. A pigeonhole policy that fires here and
"counts 31 tiles" without the invariant coloring argument is the failure mode.

## expected policy behavior

- **must not fire**, or
- **fire and fail rent** (a pigeonhole "solution" must not close; the checkerboard-invariance route
  is the right method).

## unsound-derivation risk

A wrong "solve" argues "62 squares / 2 per domino = 31, so it's tileable" — a pure count that
ignores the color imbalance. That is unsound (the invariance of the color-difference is what makes
it impossible). The policy must fail rent on it.

## proof-checker evidence required

- the two removed corners share a color (color-count 32 vs 30);
- each domino covers exactly one each color;
- impossibility by the color-invariance contradiction.

## TrainingRecord promotion gate

G4 decoy. If converted, must load + compile + partial-match AND demonstrate the Pigeonhole policy
does NOT close it.

## current status: blueprint-only, not training input
