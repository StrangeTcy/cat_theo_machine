# CUR-ENGEL-E4 — Inventory (descent/variant, two-house partition)

Scope: **read-only content inventory.** Format: 9-item inventory; **reconstructed from session
memory, not the original artifact.** The original E4 inventory was produced in an earlier session and
is not present as an artifact in the tree; this file reproduces its content in the same 9-item shape
so the E3 → E4 → E7 ordering is checkable. No production code changed.

Authoritative source: Engel, Chapter 1, Problem E4. Remote tip recorded before work:
`b7e6c90f739509271585c780684663c5c54f4eff` (integration branch `arena/01a06542-cat-theo-machine`).

---

## 1. Problem statement (authoritative)

State = a partition of members into two houses. A move: if a member has **≥ 2 enemies in their own
house**, move them to the **other** house. Goal: every member has **≤ 1 enemy in their own house**.
Prove termination / that the goal is reachable.

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

## 5. Reference measure

`V` = the number of **same-house enemy incidences**. Each move strictly decreases `V` by `≥ 1`:
relocating a member with `≥ 2` same-house enemies removes at least that many incidences from their
old house and adds at most that many `−`1 in the new house, net change `≤ −1`.

## 6. Start & terminal states

- Start state: any two-house partition.
- Terminal state: every member has `≤ 1` enemy in their own house (minimum `V`).
- `V ≥ 0` always, so the measure is bounded below.

## 7. Proof path (the generic mechanism)

1. Define `V` = count of same-house enemy incidences.
2. Each legal move decreases `V` by `≥ 1`.
3. `V ≥ 0`, so `V` cannot decrease forever; the process terminates at a state where no move is legal,
   i.e. everyone has `≤ 1` same-house enemy.

## 8. False measures to reject

| candidate | verdict | why |
|---|---|---|
| number of members in house A | **not monotone** | a move can either increase or decrease this; it is not a descent measure |
| max same-house enemies of any member | **not strictly decreasing** | need not fall by `≥ 1` on every move |

## 9. Structural difference from E3/E7 and ordering

- **E4** is **variant/descent**, a different method class from E2/E3/E7 (all invariants). It needs a
  descent/variant engine, not an observable-preservation engine.
- E3 and E7 are invariance; E4 is descent. So E4 forces a genuinely new mechanism.

Ordering recommendation: **E3** (weighted/cyclic observable), then **E4** (descent/variant method
class), then **E7** (modular-residue + window-product observable, same method class as E2/E3).

---

## Status

- **Blocked(E4, descent under same-house-enemy relocations)** — a variant/descent task requiring a
  general descent engine (well-founded measure + strict decrease + lower bound), absent in the tree.
  Not a runtime solve; a capability gap for post-tag G-track work, ordered second.
- This item is **not** to be authored as packs now.
