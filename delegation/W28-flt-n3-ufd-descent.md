# W28 — FLT $n=3$: UFD scaffolding and cubic descent (gated)

**Dimension 1 · Phase 5 · Suite slot `test40` · Prereqs W21, W22, W23, W7 `[~]`**

> **Do not start this brief until W21, W22 and W23 have reported on the integrated
> tree.** Starting it against the 2026-10-15 substrate will reproduce W7's partial.
> Read `delegation/W07-flt-n3-eisenstein.md` as history, not as the brief to re-run.

Read `delegation/README.md` first. Read DAG §4 W7, §7.1 and §8 (W28).

## Goal

Use the new substrate (witness introduction, algebraic rewriting, factorisation /
`NatLess`) to push W7 past "mod-9 obstruction + $N(1-\omega)=3$":

1. Unique-factorisation *scaffolding* over the generic quadratic ring, not a stated
   cubic lemma. If UFD cannot be derived, the suite demonstrates which constructor
   is still missing (precise negative).
2. Cubic descent attempted with minted witnesses, not authored $(x,y,z)$.
3. Same discipline as `test18` / `test20`: no cube identity, no named lemma, no
   solution constant in the tree. Ledger refuses without a receipt.

## Done-definition

First reachable of: full (Checker-B-verified descent, ledger version > 0); partial
(stated missing hypotheses); precise negative (which new substrate still does not
suffice). Update DAG §4 W7. `test20` remains green and unchanged in claims.

## Files

New `validation/test40_flt_n3_ufd_descent.py`. Extend playground / arithmetic only
if W22/W23 left a hole you can name. No `core.py`. No `packs/flt_eisenstein.pack.yaml`
as a lemma dump.

## Non-goals

$n=4$ (W29), the full FLT, weakening the ledger.
