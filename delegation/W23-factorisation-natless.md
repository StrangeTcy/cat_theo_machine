# W23 — Factorisation substrate and derived NatLess

**Substrate / Dim 1 · Phase 4 · Suite slot `test35` · Prereq none**

Read `delegation/README.md` first. Read DAG §7.1 and §8 (W23). You own
`math/arithmetic.py` and `math/peano.py`. Do not edit `invariance.py` / `playground.py`
(W22) or `graph_task.py` (W21).

## Why this worker exists

W6's missing list: `math/arithmetic` has no subtraction, root or factorisation edge, so
the coprime-square-factors lemma (unique factorisation) has no substrate; no loaded
schema concludes a `NatLess` fact, so the descent measure is evidenced, not derived.
`NatLess` already *exists* as a host edge in `math/peano.py` (`NatPred`, `NatEq`,
`NatLess`). What is missing is a *schema that concludes a `NatLess` fact* inside the
knowledge-rewrite / pack world, and generic factor/subtract edges the rest of the
machine can fire.

`Divides`, `Gcd`, `Modulo`, `IsCoprime`, `WholeNegate`, `WholeAdd`, `Ring*` already
exist. Extend them; do not parallel them.

## Goal

1. **Subtraction (or add-of-negate) as an arithmetic edge** over nats/wholes, sort-generic.
   If nats stay subtraction-free (partial order only), say so and put subtraction on
   `Whole`. Do not special-case cubes or fourth powers.
2. **A factorisation-related edge** that is not "the FTA": e.g. given `Gcd`/`Divides`,
   a constructor for "coprime cofactors" or "square-free kernel" that the machine can
   apply to *any* pair of nats. Unique factorisation in $\mathbb{Z}$ or $\mathbb{Z}[\omega]$
   is **not** the deliverable — W28 owns Eisenstein UFD.
3. **A pack-or-schema that concludes `NatLess`** from machine arithmetic (for example
   from `NatPred`, or from a measure drop along an existing `Add`/`Multiply` identity),
   so a knowledge-rewrite derivation can contain a `NatLess` fact Checker B will accept.
   A sweep that *observes* $a < b$ is evidence, not this deliverable.

## Done-definition

- `validation/test35_factorisation_natless.py` green.
  - Subtraction (or documented refusal with WholeNegate composition) works on several
    values and fails on a stated domain (e.g. nats below zero).
  - A factor-related edge is shown on instances *and* a decoy (non-coprime $(2,8)$ is
    the decoy `test26` already uses — reuse the idea, do not import FLT).
  - A derivation whose conclusion is a `NatLess` fact is Checker-B-verified; the same
    derivation against the swapped pair is refused.
- `test18`, `test20`, `test26`, `test30` still green. Arithmetic must stay flat-rate
  under W18's bound — do not reintroduce a linear scan of interned nats.
- The suite states what is *not* derived (FTA, Eisenstein UFD, FLT).

## Files

- Extend: `math/arithmetic.py`, `math/peano.py` if a schema must live next to `NatLess`.
  Keep sort-generic. `labels.py` append-only. A pack is permitted as ontology only
  (`packs/` + `main.py:PACK_PATHS`).
- New: `validation/test35_factorisation_natless.py`.
- Do not edit `core.py`, `playground.py`, `invariance.py`, `graph_task.py`.

## Verification

`PYTHONPATH=/home/user .venv/bin/python -u validation/test35_factorisation_natless.py`
green, plus `test18`, `test20`, `test26`, `test30`. Watch `test30`: new interned nats
must not restore quadratic lookup.

## Non-goals

Witness introduction (W21), rewrite normalisation (W22), Eisenstein UFD (W28),
discharging `EveryStateMoves` (W29), `core.py` edits.
