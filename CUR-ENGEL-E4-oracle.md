# CUR-ENGEL-E4 — Oracle card (two-house partition, descent under max degree ≤ 3)

Docs-only content, CUR branch. Grounds the E4 descent/variant semantics against the pinned ruling.
No production labels, `Edge` classes, packs, or G implementation in this file.

## Canonical / route directive (INT merge)

This file (`CUR-ENGEL-E4-oracle.md`, lowercase) is the **canonical** E4 oracle card. A sibling
variant `CUR-ENGEL-E4-ORACLE.md` (uppercase, on `arena/01a068c2`) uses different notation
(`V`, `ΔV = d − 2s`) but states the same facts. The two are **notation-equivalent, not divergent**
(verified exhaustively: `ΔH = e_out − e_in ≡ ΔV = d − 2s`, identical 4-cycle terminal census
`V ∈ {0,2}` with single-house `V=4` non-terminal, and the same rejected-candidate witnesses).

**INT merge instruction:** adopt this lowercase card as the single canonical E4 doc. Melding the
sibling uppercase card means merging its extra reasoning-failure witnesses (vertex-count invariance,
signed and absolute house-size difference) into this card if a single dense card is wanted — or keep
both only with this file named canonical and the sibling cited as corroborating evidence. Do **not**
merge both `E4` oracle cards as-is without naming a canonical path (the two filenames differ only in
case; content is equivalent).

**Seal identity:** the authoritative E4 content-id is maintained in the **external seal manifest**
(`CUR-ORACLE-SEALING-AND-DISTRIBUTION-HANDOFF.md` on the sibling, and the audit
`CUR-CROSS-BRANCH-AUDIT-2026-09-05.md`), not asserted inside this payload. This card is the thing
being hashed, so a purported current hash is self-referential and goes stale on every edit; it is
**not** recorded here. Prior identities are historical and superseded: `a11ca451e52…` (original
dry-run) and `841a97b7…` (post-reconciliation) are historical markers, not the current content-id.
INT computes the current content-id at seal time from the exact blob bytes.

**Merge-checklist note:** D13 declared in `protocol/CUR.md`; INT mirrors to `protocol/DISTRIBUTION.md` on merge.

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
| measure = vertex count | invariant (constant `n`) under every move | preserved but never descends, so it cannot certify progress toward a target |
| measure = signed house-size difference `\|H0\| − \|H1\|` | non-monotone | changes by `+2` or by `−2` depending on move direction |
| measure = absolute house-size difference `\|\|H0\| − \|H1\|\|` | non-monotone | it can increase (`3/3 → 2/4` makes `0 → 2`) and can decrease; not monotone |
| prove termination of the *process* but call it reaching the global min | conflates "no move legal" with "H minimal" | a state with no legal move need not minimize `H` (4-cycle dual terminals) |
| use an invariant (preservation) | E4 is descent, not preservation | Preservation alone does not provide the strict decrease required by this termination certificate. |

The vertex-count / signed- and absolute-house-size-difference witnesses were melded from the sibling
variant (`CUR-ENGEL-E4-ORACLE.md`) so this canonical card carries the full reasoning-failure matrix.

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
