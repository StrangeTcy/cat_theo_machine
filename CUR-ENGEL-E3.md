# CUR-ENGEL-E3 — Inventory (six-sector alternating sum)

Scope: **read-only content inventory.** Format: 9-item inventory; **reconstructed from session
memory, not the original artifact.** The original E3 inventory was produced in an earlier session and
is not present as an artifact in the tree; this file reproduces its content in the same 9-item shape
so the E3 → E4 → E7 ordering is checkable. No production code changed.

Authoritative source: Engel, Chapter 1, Problem E3. Remote tip recorded before work:
`b7e6c90f739509271585c780684663c5c54f4eff` (integration branch `arena/01a06542-cat-theo-machine`).

---

## 1. Problem statement (authoritative)

A circle is divided into six sectors, with numbers `1, 0, 1, 0, 0, 0` around it. A move adds `1` to
each of two adjacent sectors. Question: can the six sectors ever be made all equal? Answer: **no.**

## 2. Method classification

**Invariance — a linear weighted (signed) sum invariant** under an adjacent-increment move.

Not descent, not extremal. The invariant is a signed sum assigned by a 2-colouring of the cycle.

## 3. Ontology / vocabulary required (what is absent)

What the tree lacks (absent in the current encoding): cycle/adjacency primitive for a structure that
is a cycle (not a linear board), even-cycle 2-colouring terms, sign assignment, a signed-sum
observable, and a move-in-kernel primitive ("add to each of two adjacent sectors"). Only
`ParityLabel`/`IsEvenLabel` exist; there is no general signed-sum / adjacency vocabulary.

## 4. Move semantics

One move = add `1` to each of two **adjacent** sectors. Unlike E2 (which reduces two numbers to one)
and unlike E7 (which flips one element's sign), E3's move increments two adjacent cells by `1`.

## 5. Reference invariant

`I = a1 − a2 + a3 − a4 + a5 − a6` (alternating signed sum over the cycle). For the start state
`1, 0, 1, 0, 0, 0`, `I(start) = 2`. Under the adjacent-increment move the signed sum is preserved
(the two adjacent increments affect opposite signs, cancelling). If all six sectors were equal to `x`,
`I(x,x,x,x,x,x) = 0`. Since `I(start) = 2 ≠ 0`, all-equal is unreachable.

## 6. Start & terminal states

- Start state: `1, 0, 1, 0, 0, 0`; `I = 2`.
- Terminal (putative): all sectors equal `x`; `I = 0`.
- `2 ≠ 0`, so the terminal state is unreachable from the start under the move.

## 7. Proof path (the generic mechanism)

1. Compute `I(start) = 2`.
2. Preservation: any adjacent-increment move changes `I` by `+1 − 1 = 0`, so `I` is invariant.
3. The all-equal state has `I = 0`; since the invariant is constant at `2`, it is unreachable.

## 8. False candidates to reject

| candidate | verdict | why |
|---|---|---|
| plain `Sum(a1+…+a6)` | **not invariant** | each move adds `2` to the total, so the sum changes by `+2` |

## 9. Structural difference from E3/E7 and ordering

- **E3** is a **linear weighted-signed-sum** invariant over a **cycle** with **adjacent-increment**
  moves → needs a weighted-linear observable + adjacency primitive.
- **E7** is a **sum-of-products** invariant with **sign-flip** moves → a different observable
  constructor (window product + sum-of-products + mod-4 residue). Neither is a special case of the
  other.

Ordering recommendation: **E3** first (forces the generic weighted/cyclic-observable substrate), then
**E4** (descent/variant method class), then **E7** (modular-residue + window-product observable, same
method class as E2/E3).

---

## Status

- **Blocked(E3, Invariance over signed-sum against adjacent-increment moves)** — an invariants task
  requiring a cycle/adjacency 2-colouring + signed-sum observable, absent in the tree. Not a runtime
  solve; a capability gap for post-tag G-track work, ordered first.
- This item is **not** to be authored as packs now.
