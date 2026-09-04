# CUR-ENGEL-E4 — Oracle card (two-house partition, descent under max degree ≤ 3)

Docs-only content, CUR branch. Grounds the E4 descent/variant semantics against the pinned ruling.
No production labels, `Edge` classes, packs, or G implementation in this file.

Branch: `arena/01a066cf-cat-theo-machine`. Doc base `34208cc69144dff3c926cbb1d475a13ebbfb751d`.
Landing-time integration tip: `e0853a915baf260b7d1e9d3678c8f9d78300655b`.

Notes on the math for the oracle card are the pinned facts from the prior ruling: monovariant
`H = same-house enemy edges`; `ΔH = e_out − e_in ≤ −1` under the **max degree ≤ 3** bound
(`e_in ≥ 2` legal + `e_in + e_out ≤ 3` ⇒ `e_out ≤ 1` ⇒ `ΔH ≤ −1`). The prior general-graph
refutation (`CUR-ENGEL-E4-descent-refutation.md`) is retained as an audit trail and does **not**
apply once the degree bound is in force.

---

## 1. Problem statement (with degree bound)

Each member is in house 0 or 1. The enemy relation is symmetric. **Load-bearing given:** each member
has **at most 3 enemies total** (max degree ≤ 3). A move: pick a member with **≥ 2 enemies in its own
house** and relocate it to the **other** house. Prove the process terminates (it reaches a state where
no move is legal: every member has ≤ 1 enemy in its own house).

## 2. Method classification

**Variant / descent (bounded-below termination).** Not an invariant; the monovariant `H` strictly
decreases on every legal move and is bounded below by 0.

## 3. Ontology / vocabulary required (what is absent)

Descent/partition vocabulary: two-house partition, symmetric enemy relation, same-house enemy-edge
count, the max-degree bound. The tree has only `BoundedBelowLabel`/`BoundedAboveLabel`
(`invariance.py`); there is no generic descent/variant engine and no per-member same-house enemy
count.

## 4. Move semantics

One move = pick a member `m` in house `h` with `e_in ≥ 2` (its enemies in its own house) and relocate
it to the other house. The enemy relation is fixed; only the house assignment changes.

## 5. Monovariant

```
H = # of unordered enemy pairs (i,j) with house[i] == house[j]
```

For member `m` in house `h`: `e_in` = enemies of `m` in `h`; `e_out` = enemies of `m` in the other
house. Relocating `m` changes:

```
ΔH = e_out − e_in
```

## 6. ΔH table under the degree bound

```
degree bound:  e_in + e_out ≤ 3   (each member has ≤ 3 enemies)
legality:      e_in ≥ 2

e_in | e_out | ΔH = e_out − e_in | legal?
 2   |  0    |   −2              | yes
 2   |  1    |   −1              | yes
 3   |  0    |   −3              | yes
(any e_in ≥ 4 is impossible under the bound)
```

In every legal case `ΔH ≤ −1`, so `H` strictly decreases on every legal move. Bounded below by 0, so
termination.

## 7. Grading matrix — reasoning failures (not observable failures)

This matrix scores how a learner/engine might fail to conclude termination, as reasoning errors rather
than observable-constructor errors:

| failure mode | what goes wrong | why it does not yield termination |
|---|---|---|
| ignore the degree bound | using the general `e_in ≥ 2` alone | a legal move can have `e_out ≥ e_in`, so `ΔH` is not guaranteed `< 0` (refutation note) |
| measure = # members in house A | count is non-monotone | a move can increase or decrease it; no strict decrease |
| measure = max same-house enemies | not guaranteed to fall by ≥ 1 | the max need not drop on every move |
| prove termination of the *process* but call it reaching the global min | conflates "no move legal" with "H minimal" | a state with no legal move need not minimize `H` (4-cycle dual terminals) |
| use an invariant (preservation) | E4 is descent, not preservation | no quantity is invariant; the argument is a strict decrease |

## 8. Negative controls

**Negative control A — degree-4 break of the bound.** If the degree bound is relaxed to max degree ≤ 4,
the descent fails: a member can have `e_in = 2` and `e_out = 2` (`e_in + e_out = 4`), giving
`ΔH = 0`, i.e. a legal move that does **not** decrease `H`. This is the concrete counterexample from
the refutation note (n=6, house=[0,0,0,1,1,1], enemy(0)={1,2,4,5}, ΔH = 0). The bound is load-bearing.

**Negative control B — 4-cycle dual terminals (termination ≠ global min).** Construct a 4-cycle
enemy graph where two different terminal states (no legal move) have different `H` values, so the
first terminal reached is not the global minimum of `H`. This shows the descent gives *termination*
only, not *minimality*; the termination argument is correct, the minimality claim is not to be made.

## 9. Structural difference from E3/E7

- **E3** — invariance, linear weighted (signed) sum observable over a cycle, adjacent-increment moves.
- **E4** — descent/variant (bounded-below monovariant `H`), single-member relocation under a max-degree
  bound. A genuinely different method class from E2/E3/E7 (all invariance).
- **E7** — invariance, modular residue over a sum-of-products observable, sign-flip moves; reaches the
  conclusion via a reachability readout.

Ordering: **E3** (weighted/cyclic observable), **E4** (descent/variant method class), **E7**
(modular-residue + window-product observable). E4's descent engine is the distinct new capability that
E3 and E7 do not require.

---

## Status

- **Blocked(E4, descent under same-house-enemy relocations with max degree ≤ 3)** — requires a general
  descent engine (monovariant `H`, strict ≥ 1 decrease, lower bound). Absent in the tree; capability
  gap for post-tag G-track work, ordered second.
- Authoritative statement, monovariant, ΔH table, grading matrix, and both negative controls as above.
- No production code, labels, Edge classes, packs, or G implementation touched.
