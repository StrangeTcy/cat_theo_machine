# CUR-ENGEL-E7 — Inventory (Cyclic 4-product sign flip, mod-4 invariant)

Scope: **read-only content inventory.** Format: 9-item inventory; reconstructed for E3/E4 to the
same shape at `CUR-ENGEL-E3.md` and `CUR-ENGEL-E4.md` (`reconstructed from session memory, not the
original artifact`). This corrects the earlier note: the prior note was correct that **no E7 content
exists in the repository tree**, but the problem is defined in Engel Ch. 1 and belongs to the
invariants method class. The absence is a *content-encoding* absence, not a *problem* absence.

Authoritative source: Engel, Chapter 1, Problem E7. Remote tip recorded before work:
`b7e6c90f739509271585c780684663c5c54f4eff` (integration branch `arena/01a06542-cat-theo-machine`).

---

## 1. Problem statement (authoritative)

Each of the numbers `a_1, …, a_n` is `1` or `-1`, and

```
S = a1·a2·a3·a4 + a2·a3·a4·a5 + … + a_n·a1·a2·a3 = 0.
```

(Indices are taken cyclically: there are `n` four-term products, one starting at each position.)
Assume `n ≥ 4` (for `n < 4` the cyclic four-windows wrap onto themselves and the "four consecutive
terms" count below is wrong).
Prove that `4 | n`.

Goal conclusion: `n` is divisible by 4. Supplied hypothesis: `S = 0`.

## 2. Method classification

**Invariance — specifically a modular (mod-4) invariant under a sign-flip move.**

Not descent, not extremal, not pigeonhole. The preservation is on the **sum of 4-wise products
modulo 4**, under the move of **flipping the sign of a single `a_i`**.

This is the same *method class* as E2 (parity-of-a-sum preserved by a rewrite), but a different
*observable shape*: E2 preserves parity of a sum under a two-numbers-into-one rewrite; E7 preserves
a sum-of-products modulo 4 under a one-element sign flip.

## 3. Ontology / vocabulary required (what is absent)

What the tree already has (generic invariance engine): `InvarianceLabel`, `Invariant`, `Preserves`,
`InvariantCandidate`, `InvariantRefuted`. `ParityLabel` gives mod‑2 reasoning only.

What E7 needs but the tree lacks:

| label / constructor | need |
|---|---|
| `ResidueMod(observable, modulus, value)` | generic modular-residue observable (mod 4, not just parity/mod 2) |
| `FlipSign(state, position)` | sign-flip legal-move primitive on one element |
| `CyclicWindowProduct(state, window_size, offset)` | sliding-window 4-product over a cycle, cyclic boundary conditions |
| `SumOfProducts(!)` | sums the window products around the cycle → the observable `S` |
| modular-preservation rule | generic: flipping one element changes `SumOfProducts` by a multiple of the modulus |

Absent labels confirmed by tree search: no `SignFlip`, no `CyclicWindowProduct`, no `SumOfProducts`,
no `ResidueMod`. `BoardSumObservable`/`BlackboardProblem` are E2-specific.

## 4. Move semantics

One move = pick a single element `a_i` and flip its sign (`a_i → -a_i`). Unlike E2 (which rewrites
two numbers into one), E7's move touches **one element** and — for the `n ≥ 4` case, where the four
cyclic windows are distinct — changes **exactly four consecutive four-term products** of `S`.

## 5. Reference invariant

`S mod 4` is invariant under any sign flip. Flipping one `a_i` changes exactly four consecutive
terms of `S`; each term flips sign, so the net change to `S` is a multiple of 4:

- 2 positive / 2 negative among the four affected terms → change `0`
- 1 positive / 3 negative (or vice versa) → change `±4`
- all four same sign → change `±8`

Hence `S ≡ 0 (mod 4)` is preserved across the whole run. Reference invariant:
`ResidueMod(SumOfProducts(state), 4, r)` with the preserved value `r = 0`.

## 6. Start & terminal states

- Start state (hypothesis): `S = 0`, any assignment of `±1` to the `a_i`.
- Terminal state: flip every `-1` to `+1` until all `a_i = 1`. Then each four-term product is `1`
  and there are `n` of them, so `S = n`.
- Since `S ≡ 0 (mod 4)` at every step and `S = n` at the terminal state, conclude `n ≡ 0 (mod 4)`.

## 7. Proof path (the generic mechanism)

1. Base: `S = 0` (hypothesis) ⇒ `S ≡ 0 (mod 4)`.
2. Preservation: any sign flip changes `S` by a multiple of 4 (step 5), so `S mod 4` is invariant.
3. Reach the all-ones state by flipping every `-1` to `+1` (a finite sequence of legal moves).
4. At the all-ones state, `S = n`; invariant gives `n ≡ 0 (mod 4)`.

This is a single invariant-obligation + one reachability readout: the same structural shape as the E2
`Preserves`/`Invariant`/terminal-readout proof, but on a mod-4 residue observable.

## 8. False candidates to reject

| candidate | verdict | why |
|---|---|---|
| "Total sum of the `a_i` is invariant" | **false** | flipping one element changes the sum by `±2` |
| "Parity of `S` is invariant" | **true but insufficient** | only gives `n` even, not `n` divisible by 4 — the classic "preserved but not separating" case |
| "Product of all `a_i` is invariant" | **not an invariant** | a single flip negates `∏ a_i`; it fails at the preservation step, not at separation |
| "Product of all four-window products is invariant" | **preserved but non-separating** | `∏ (a_i·a_{i+1}·a_{i+2}·a_{i+3}) = (∏ a_i)^4 = 1` — invariant but always `1`, so it never separates the `S=0` start from the all-ones terminal state |

## 9. Structural difference from E3 and ordering

- **E3** (six-sector alternating sum) is a **linear weighted-sum** invariant with adjacent-increment
  moves → needs a weighted-linear observable + adjacency-increment primitive.
- **E7** is a **sum-of-4-wise-products** invariant with sign-flip moves → needs a window-product +
  sum-of-products + sign-flip + mod-4 residue primitive.
- Neither is a special case of the other at the observable-constructor level.

Ordering recommendation (same as operator): **E3** (forces new weighted/cyclic-observable capability),
then **E4** (forces descent/variant method class), then **E7** (another observable shape — modular
residue + window product — but the same invariance method class as E2/E3). E7 is a suitable invariance
test for the G-track generator *after* it supports products and modular residues, not the first target;
it is not a linear-invariant task.

---

## Status

- No E7 production content exists in the tree (no `engel_e7_*.md`, no `packs/engel-e7*.pack.yaml`,
  no training record, no `protocol/E.md` entry). The problem is defined externally (Engel) but
  **unencoded** here.
- **Blocked(E7, Invariance over ResidueMod(SumOfProducts, 4) under FlipSign)** — an invariants
  task whose observable is `ResidueMod(SumOfProducts, 4)`. It is **not** a linear-invariant task;
  the sum-of-products observable is not linear, so this must not be parked under linear-invariant work.
- **Ontology gap — routed separately as a `[SHARED]` request to INT.** `ResidueMod`, `FlipSign`,
  `CyclicWindowProduct`, `SumOfProducts` are **term constructors, not planner methods**. `G1` owns
  `Invariance(observable, moveset)` as a planner alternative; it does **not** own new observable
  vocabulary. Adding these constructors is a `[SHARED]` request to the integrator, not a G-eng addition
  made inside the G block by default.
- Not a runtime solve; recorded as a capability gap for post-tag G-track work, ordered **after** E3/E4.
