# CUR-ENGEL-E7 — Oracle card (cyclic 4-product sign flip)

Docs-only content, CUR branch. Grounds the semantics of E7 as a concrete oracle so a planner
alternative (`Invariance(observable, moveset)`) can be evaluated against it and so the rejected
candidates have explicit witnesses. No production labels, no `Edge` classes, no pack, no G
implementation in this file.

Branch: `arena/01a066cf-cat-theo-machine`; doc base `b8b822adca5faf13ee3c6464daf4b72d28163cda`.
Landing-time integration tip: `d76f7814a5a886d26248b52b95a3dfa1699fd491`.

Problem (Engel Ch.1 E7): `a_i ∈ {1, -1}`, indices cyclic, `S = Σ a_i·a_{i+1}·a_{i+2}·a_{i+3} = 0`,
prove `4 | n`. Assumed `n ≥ 4` so the four cyclic windows touched by one flip are distinct.

Inputs use the corrected signatures:
- `CyclicWindowProduct(sequence, width, offset)` — one 4-product term.
- `SumOfProducts(product_terms)` — the machine sequence of `CyclicWindowProduct` terms.
- `ResidueMod(reading, modulus, residue)` — reading = `SumOfProducts`, modulus 4, residue 0.
- `FlipSign(state, position)` — the legal move on one element `a_i`.

---

## 1. Reference observable

```
O = ResidueMod(SumOfProducts(CyclicWindowProduct(state, width=4, offset=1..n)), 4, residue)
```

The reference residue value is `0`. The claim is: `O` is invariant under `FlipSign`, and the
terminal (all-ones) reading forces `residue = 0`.

## 2. Start and target readings

| state | `S` reading | `ResidueMod(S, 4)` |
|---|---|---|
| start (hypothesis `S = 0`) | `0` | `0` |
| target (all `a_i = +1`) | `n` | `n mod 4` |

Since the residue `0` is invariant, the target reading requires `n mod 4 = 0`, i.e. `4 | n`.

## 3. Preservation of the observable

One `FlipSign(state, position)` sits in exactly `width = 4` consecutive products (distinct for
`n ≥ 4`). Let the four affected product values be `p1, p2, p3, p4`; their partial sum
`s = p1 + p2 + p3 + p4`. Flipping the element negates each of the four, so the partial sum becomes
`-s`, and the total change is:

```
ΔS = -2·s ,   s ∈ {-4, -2, 0, 2, 4}  (sum of four ±1 products)
⇒ ΔS ∈ {0, ±4, ±8}
⇒ ΔS ≡ 0 (mod 4)
```

So `ResidueMod(S, 4)` is preserved. The generic principle: `-2·s ≡ 0 (mod 4)` exactly when `s` is
even; `s` (a sum of `width` ±1 terms) is even exactly when `width` is even.

## 4. Preservation / separation matrix

| observable | preserved by `FlipSign`? | separates start (`S=0`) from target (`S=n`)? | verdict |
|---|---|---|---|
| `ResidueMod(SumOfProducts, 4)` | yes | yes — forces `n mod 4 = 0` | **reference** |
| `Parity(SumOfProducts)` | yes | no — only forces `n` even, not `n mod 4 = 0` | **preserved but non-separating** |
| `Σ a_i` | no | n/a | **rejected (not invariant)** |
| `∏ a_i` | no | n/a | **rejected (not invariant)** |
| `∏ (4-window products)` = `(∏ a_i)^4 = 1` | yes | no — constant `1` | **preserved but non-separating** |

## 5. Concrete witnesses for the rejected candidates

- **`Σ a_i` not invariant.** State `[1,1,1,1]`: `Σ a_i = 4`. `FlipSign(position=1)`
  → `[-1,1,1,1]`: `Σ a_i = 2`. Changed by `-2`, so `Σ a_i` is not preserved.
- **`∏ a_i` not invariant.** State `[1,1,1,1]`: `∏ a_i = 1`. `FlipSign(position=1)` → `[-1,1,1,1]`:
  `∏ a_i = -1`. Flipped sign, so not preserved. (Contrast the *window-product* aggregate:
  `∏(each 4-window product) = (∏ a_i)^4 = 1`, which is invariant but constant.)
- **`Parity(SumOfProducts)` non-separating.** For `n = 6`, the all-ones target has `S = 6`,
  `Parity = even`, but `ResidueMod(6,4) = 2 ≠ 0`. A parity-only invariant would accept `n = 6`
  (`S = 6` even), yet `6` is not divisible by `4`. So parity is preserved but cannot separate the
  admissible (`4 | n`) from inadmissible (`n` even but `6`-style) cases.

## 6. Negative control — window width explicit

Keep the same reference observable but change the window width to an odd value:

- `width = 3`: one `FlipSign` element sits in 3 cyclic windows. `s = p1+p2+p3` is a sum of three
  ±1 terms, so `s ∈ {-3, -1, 1, 3}` (always **odd**). Then `ΔS = -2·s ∈ {±2, ±6}`, and
  `±2 ≡ 2 (mod 4)`, `±6 ≡ 2 (mod 4)`, i.e. **`ΔS ≢ 0 (mod 4)`** (specifically `ΔS ≡ 2 (mod 4)`).
  The observable is **not** preserved at odd width.

This is the distinguishing control: the mod-4 preservation holds precisely for **even** window width
(so the four-window reference works), and fails for odd width (three-window). It isolates that the
reference invariant is a *width-, modulus-, and moveset-coupled* property rather than a property of
the modulus alone.

Negative-control candidate to reject, with width explicit:
- `ResidueMod(SumOfProducts(CyclicWindowProduct(state, width=3)), 4)` — **not invariant** under
  `FlipSign`.

### Checked witness (measured this session)

Independent brute-force computation for `n = 5`, width = 3:

- Start `[1,1,1,1,1]` (all ones): `S₃ = 5`, residue `5 mod 4 = 1`.
- Flip any one element → `[-1,1,1,1,1]` (or any single-flip state): `S₃ = -1`, residue `-1 mod 4 = 3`.
- `ΔS₃ = -6`, `ΔS₃ ≡ 2 (mod 4)`, and residue moves `1 → 3` (not preserved).

This matches the general formula (`ΔS = -2·s` with `s = -3` for a single `-1` among three terms →
`ΔS = 6`; sign convention gives `-6`, both `≡ 2 mod 4`). The concrete witness and the general
algebra agree from two directions. Note `n = 5` has overlapping three-windows, so the "sits in
exactly width distinct windows" claim does not hold here — but the preservation failure still
registers: the residue is not invariant, which is the point of the control.

A minimal odd-width control with a residue-0 start (`width = 3`, `n = 6`) confirms the same failure
mechanism from a separation standpoint:

- Start `(1,1,1,1,1,-1)`: `S₃ = 0`, residue `0` (matches the reference hypothesis `S = 0`).
- `FlipSign(position=0)` → `(-1,1,1,1,1,-1)`: `S₃ = 2`, residue `2`, `ΔS₃ = +2 ≡ 2 (mod 4)`.
- So from a residue-0 start, an odd-width observable does **not** preserve the residue — a direct
  separation counterexample. Three ±1 terms give odd `s`, so `ΔS = -2·s ≡ 2 (mod 4)`.

## 7. Conclusion for the oracle

- The reference observable `ResidueMod(SumOfProducts(CyclicWindowProduct(.,4,.)), 4)` is invariant
  under `FlipSign` and separates the target, forcing `n mod 4 = 0`.
- Rejected: `Σ a_i` (not invariant), `∏ a_i` (not invariant), `Parity(SumOfProducts)` (preserved but
  non-separating), `∏(4-window products)` (preserved but constant).
- Negative control (odd width) demonstrates the preservation is width-and-modulus coupled.
