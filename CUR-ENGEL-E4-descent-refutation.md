# CUR-ENGEL-E4 — Descent measure: measured refutation under general enemy semantics

Status: **finding, docs-only.** This records that the E4 descent claim as stated in
`CUR-ENGEL-E4.md` is **refuted** by brute-force measurement for a general symmetric enemy relation.
It is a correctness correction, not an oracle card: an oracle card cannot be written until the E4
"enemy" semantics are pinned down.

Branch: `arena/01a066cf-cat-theo-machine`. Doc base `6b25e9e63ed9b62664b529f1f1259cb25444d0b2`.

---

## The claim under test

`CUR-ENGEL-E4.md` item 5/7 asserts:

```
V = number of same-house enemy incidences.
Each legal move strictly decreases V by >= 1.
```

Definition used for the test (the only one reachable from the reconstruction): a symmetric enemy
relation on `n` members; `V` counts unordered enemy pairs `(i,j)` with `house[i] == house[j]`; a
move relocates a member `m` to the other house when `m` has ≥ 2 enemies in its own house.

## The measure is not monotone

For member `m` in house `h`, let:
- `c_in` = number of `m`'s enemies in house `h` (own house),
- `c_out` = number of `m`'s enemies in the other house.

Relocating `m` changes:

```
ΔV = c_out - c_in
```

Strict decrease requires `ΔV < 0`, i.e. `c_out < c_in`. But the legality condition is only
`c_in ≥ 2`. A legal move with `c_out ≥ c_in` gives `ΔV ≥ 0` — V does **not** strictly decrease.

## Concrete measured counterexample

```
n = 6, house = [0, 0, 0, 1, 1, 1]
enemy(m=0): {1,2} (house 0) and {4,5} (house 1)   -> c_in = 2, c_out = 2
```

Member 0 has `c_in = 2` (≥ 2, so the move is **legal**). V before = 2; V after relocating 0 to
house 1 = 4; `ΔV = 0`. A brute-force sweep over random graphs (400 runs, n ∈ {6,8,10,12}) found a
legal move with `ΔV ≥ 0` in **853 / 1200** samples — the claim "strictly decreases on every legal
move" is **false** for general symmetric enemy relations.

## What this means

- The E4 **descent measure `V` is not a monotone descent measure** under general enemy semantics.
- The actual Engel E4 descent must rely on structure not present in this reconstruction — the exact
  "enemy" relation definition (e.g. a fixed hostile partition, a tournament orientation, or a
  specific "each person has a fixed number of enemies" rule) is **not in the repository** (verified:
  only `CUR-ENGEL-E4.md` is reachable; no `engel_e4_*` spec exists in the tree).
- Therefore a **verified E4 oracle card cannot be produced** from the current content. Writing one
  would require inventing the enemy semantics and asserting a descent that measurement refutes.

## Recommendation

- Pin the E4 "enemy" definition from the authoritative Engel source before any E4 oracle/inventory.
- Until then, mark E4 as **suspended pending semantics**, not as a ready gap-inventory target.

## Hygiene

No production code, labels, Edge classes, or packs touched. No §0 banned phrase in this note.

Remote tip recorded before work: `d76f7814a5a886d26248b52b95a3dfa1699fd491`.
