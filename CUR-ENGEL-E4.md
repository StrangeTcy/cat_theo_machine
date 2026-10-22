# CUR-ENGEL-E4 — Inventory (descent/variant, two-house partition)

Scope: **read-only content inventory.** Format: 9-item inventory; **reconstructed from session
memory, not the original artifact.** The original E4 inventory was produced in an earlier session and
is not present as an artifact in the tree; this file reproduces its content in the same 9-item shape
so the E3 → E4 → E7 ordering is checkable. No production code changed.

Authoritative source: Engel, Chapter 1, Problem E4 ("Problem 1.4" in the numbering used for this
programme). Remote tip recorded before work: `b7e6c90f739509271585c780684663c5c54f4eff`
(integration branch `arena/01a06542-cat-theo-machine`).

Correction note: an earlier reconstruction of this inventory stated the descent measure `V` (count of
same-house enemy incidences) strictly decreases on every legal move under a **general** symmetric
enemy relation. That claim is **refuted** by brute-force measurement under general semantics and is
now corrected below with the load-bearing given that repairs it: **each member has at most 3 enemies
(max degree ≤ 3)**. The refutation is retained as an in-tree audit trail at
`CUR-ENGEL-E4-descent-refutation.md`.

---

## 1. Problem statement (authoritative)

State = a partition of members into two houses. **Load-bearing given:** each member has **at most 3
enemies total** (max degree ≤ 3). Enemy relation is symmetric. A move: if a member has **≥ 2 enemies
in their own house**, move them to the **other** house. Goal / termination: every member has **≤ 1
enemy in their own house**. Prove the process terminates (a terminal/config state is reached).

## 2. Method classification

**Variant / descent (with bounded-below termination) — not invariant.**

This is a measure-decrease argument: a well-founded measure strictly decreases on each move, with a
lower bound, so the process terminates. It is **not** an invariants argument.

## 3. Ontology / vocabulary required (what is absent)

What the tree lacks (absent in the current encoding): a partition/descent vocabulary. Only
`BoundedBelowLabel` and `BoundedAboveLabel` exist (in `invariance.py`); there is no generic
descent/variant engine or per-member same-house-enemy count. Method class is **variant/descent**, not
invariant.

## 4. Move semantics

One move = if a member has **≥ 2 enemies** in their own house, relocate them to the **other** house.
The move is on a **single member** (like E7's single-element flip), but the measure is a count of
same-house enemy incidences, not a sum/product observable.

## 5. Reference measure (monovariant)

`H` = the number of **same-house enemy edges** (unordered hostile pairs within the same house).

For a member `m` in house `h`, let `e_in` = # of `m`'s enemies in own house `h`, and
`e_out` = # of `m`'s enemies in the other house. The relocating move changes:

```
ΔH = e_out − e_in
```

Under the **degree bound** (each member has ≤ 3 enemies total, so `e_in + e_out ≤ 3`) and the
**legality condition** (`e_in ≥ 2`):

```
e_in ≥ 2 and e_in + e_out ≤ 3  ⇒  e_out ≤ 1  ⇒  ΔH = e_out − e_in ≤ 1 − 2 = −1
```

So every legal move **strictly decreases `H` by at least 1**. `H ≥ 0` always, so `H` is a
well-founded (bounded-below) descent measure and the process terminates.

## 6. Start & terminal states

- Start state: any two-house partition over the given enemy graph (each member has ≤ 3 enemies).
- Terminal state: a state in which **no move is legal**, i.e. every member has `≤ 1` enemy in their
  own house. This is **not** necessarily the global minimum of `H` (termination ≠ global minimum —
  see the 4-cycle dual-terminals negative control in `CUR-ENGEL-E4-oracle.md`).
- `H ≥ 0` always, so the measure is bounded below.

## 7. Proof path (the generic mechanism)

1. Define `H` = count of same-house enemy edges.
2. Under the degree bound + legality condition, every legal move strictly decreases `H` by ≥ 1
   (ΔH = e_out − e_in ≤ −1).
3. `H ≥ 0`, so `H` cannot decrease forever; the process terminates at a state where no move is legal,
   i.e. everyone has `≤ 1` same-house enemy.

## 8. False measures to reject

| candidate | verdict | why |
|---|---|---|
| number of members in house A | **not a descent measure** | a move can either increase or decrease this; it is not monotone and need not fall on every move |
| max same-house enemies of any member | **not a strict descent measure** | need not fall by `≥ 1` on every legal move; only `H` (the edge count) is pinned to fall by `≥ 1` under the degree bound + legality condition |

Note: `H` (same-house enemy **edge** count) is the pinned monovariant. A per-member count (`number of
members in house A`) or `max same-house enemies` does not give the strict ≥ 1 decrease that the degree
bound yields for `H`.

## 9. Structural difference from E3/E7 and ordering

- **E4** is **variant/descent**, a different method class from E2/E3/E7 (all invariants). It needs a
  descent/variant engine, not an observable-preservation engine.
- E3 and E7 are invariance; E4 is descent. So E4 forces a genuinely new mechanism.

Ordering recommendation: **E3** (weighted/cyclic observable), then **E4** (descent/variant method
class), then **E7** (modular-residue + window-product observable, same method class as E2/E3).

---

## Status

- **Blocked(E4, descent under same-house-enemy relocations with max degree ≤ 3)** — a
  variant/descent task requiring a general descent engine (well-founded measure `H` + strict decrease
  + lower bound), absent in the tree. Not a runtime solve; a capability gap for post-tag G-track work,
  ordered second.
- Authoritative statement and reasoning are pinned in `CUR-ENGEL-E4-oracle.md` (eight-part). The
  earlier general-graph refutation is retained as an in-tree audit trail at
  `CUR-ENGEL-E4-descent-refutation.md`.
- This item is **not** to be authored as packs now.
