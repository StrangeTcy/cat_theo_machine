# W22 — Algebraic rewriting (grid identities become derivations)

**Substrate / Dim 1 · Phase 4 · Suite slot `test34` · Prereq none**

Read `delegation/README.md` first. Read DAG §7.1 and §8 (W22). File ownership: you own
`invariance.py` (`RewriteEquals`) and `playground.py`. **Do not edit `math/arithmetic.py`**
— that is W23. If you need subtraction, move it across the equation as `test26` already
does, or use existing `WholeNegate`.

## Why this worker exists

`playground.PolynomialIdentityByGrid` decides identities in the admitted fragment
(`ExprAdd` / `ExprMul` / `ExprPow`) by evaluation on `{0..d_i}` — sound by the finite-grid
identity lemma, so a truth verdict is a proof over $\mathbb{Z}$, not evidence. W6 used it
for $p^2 + 4(p+n^2)n^2 = (p+2n^2)^2$. Separately, `invariance.RewriteEquals` with the
default distributivity/associativity rules is *stuck* on those same identities: ring
normalisation is absent. So the machine can *know* an identity and still be unable to
*rewrite* its way there. That blocks FLT algebra (W6/W7) and d'Alembert (Dim 2).

## Goal

Connect the two: a grid-true identity in the admitted fragment must be dischargeable as
a rewrite derivation that Checker B will verify, or the suite must demonstrate a precise
remaining obstruction (which constructor, which fuel, which rule shape).

1. Extend `RewriteEquals` and/or the playground so a grid-true identity produces a
   rewrite certificate (a path of `RewriteHere` steps, or a recorded grid proof that
   Checker B has a clause for — pick one and say which). Prefer reusing existing
   algebra rules over adding a parallel engine.
2. Refuse what the grid refuses: `ExprNeg`, `ExprFrac`, `ExprDiv` stay out of the
   admitted fragment until W23 provides edges. The suite pins the refusal.
3. Show the grid size is still load-bearing (`a²+a` vs `2a` on `{0,1}`), as `test26` does.
4. No identity about cubes, fourth powers, or Pythagorean triples is authored. Generic
   polynomial identities only.

## Done-definition

- `validation/test34_algebraic_rewriting.py` green. At least one identity `test26` currently labels *derived-by-grid* is now also a
  rewrite (or a Checker-B-verified grid certificate). At least one non-identity is
  refused. `RewriteEquals` on the default rule set is either no longer stuck on that
  identity, or the suite names the remaining missing constructor.
- `test13`, `test16`, `test18`, `test26` still green. Do not change `test26`'s claims.
- Partial is allowed: if rewrite still cannot reach the identity, the suite asserts the
  obstruction rather than hiding a host-side "just believe the grid" skip.

## Files

- Extend: `invariance.py`, `playground.py`, `labels.py` (append-only).
- New: `validation/test34_algebraic_rewriting.py`.
- Do not edit `math/arithmetic.py`, `core.py`, or FLT packs.

## Verification

`PYTHONPATH=/home/user .venv/bin/python -u validation/test34_algebraic_rewriting.py`
green, plus `test13`, `test16`, `test18`, `test26`.

## Non-goals

Subtraction/factorisation edges (W23), FLT discharge (W28/W29), d'Alembert as a named
equation (W24/W31). `core.py` edits.
