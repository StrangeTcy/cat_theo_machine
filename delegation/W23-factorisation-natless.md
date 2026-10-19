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


## Completion / handoff (2026-10-19)

Done on `arena/c58acfec-cat-theo-machine`; `test35` is occupied. **109/109 checks**,
~26 s; all **35/35** validation suites green sequentially (~27.9 min). W18/test30's
index-growth ratio is 1.00 (0.0674 s/call in both measured batches). No kernel/index
changes except the two appended snapshot-registered labels.

### Arithmetic API

All new operations return `Pair(value-or-[], Pair(registry, []))`. Always thread
the returned registry; `[]` is failure, **not** the natural zero.

- `NatSubtract(a,b,registry)`: partial natural difference. Underflow and invalid
  sorts are refused before `NatFromRep` can clamp a negative to zero.
- `WholeSubtract(x,y,registry)`: signed difference, implemented solely with existing
  `WholeNegate` and `WholeAdd`. Inputs must be kernel `Whole` values; natural atoms
  are not silently coerced into wholes.
- `ExactNatQuotient(a,b,registry)`: division only if `b>0` and existing `Divides(b,a)`
  accepts. Non-exact quotients and all zero-divisor cases (including 0/0) fail.
- `CoprimeCofactors(a,b,registry)`: uses existing `Gcd`, exact quotients and
  `IsCoprime`. Its record is `Pair(CoprimeCofactorsLabel, [a,b,g,u,v])`, where
  `a=g*u`, `b=g*v`, `g=gcd(a,b)` and `gcd(u,v)=1`. Both-zero fails; single-zero
  succeeds with reduced cofactors (0,1)/(1,0). The record never claims the original
  pair is coprime: (2,8) records g=2 and reduced pair (1,4).
- `NatPredecessorFact(n,registry)`: for positive naturals only, compute `p=NatPred(n)`,
  verify `Succ(p)=n` and return the fact `Pair(NatSuccessorLabel,[p,n])`. Zero emits
  no fact; this guard prevents the saturating `NatPred(0)=0` convention licensing
  a strict self-inequality.

### Proof API and boundary

Load `packs/nat-order.pack.yaml` explicitly (also registered in `main.PACK_PATHS`).
It contains only `successor_strict_order` and `nat_less_transitive`, generic authored
Peano schemas with no problem data. Feed the computed successor fact(s) to
`proof.Knowledge`; `graph_task.ForwardDeriveFacts` and
`dialogue.SearchKnowledgeDerivation` can derive `NatLess` facts. Ordinary Checker B
verification accepts these derivations and rejects the same proof against swapped
endpoints, absent starting premises, or withheld rules. No new checker clause or
arithmetic proof action was added.

**Important:** initial computation facts are explicit premises, as `NatSum` is in
W9. Checker B verifies schema application conditional on them; it does not independently
recompute or authenticate their arithmetic provenance. Do not hand-author a false
`NatSuccessor` fact and call the resulting conditional derivation an unconditional
proof of an inequality. Arithmetic provenance checking is a distinct future extension.

New labels `NatSuccessorLabel` and `CoprimeCofactorsLabel` use the existing snapshot
symbol mechanism; test35 re-verifies a real order derivation after codec round-trip.
No new persistent state/roots or second machine-term serialisation was introduced.
`math/peano.py`, `core.py`, W21/W22 modules, Checker B and persistence are unchanged.

### What W28/W29 can and cannot assume

The W21–W23 prerequisite gate is now green. They may use these edges/schemas; they
may **not** assume FTA, prime decomposition, the coprime-square-factors lemma,
Eisenstein UFD, a proved descent measure, EveryStateMoves or FLT. Those are not
consequences claimed by this worker.

`test26` stays unchanged and green, but its old arithmetic-absence prose is historical:
its name checks mention generic legacy symbols, not these sort-specific operations,
and its selected packs exclude `nat-order`. Its negative FLT/descent account was not
upgraded. `test35` is the authoritative test of this new substrate.


## W29-driven endpoint repair (2026-10-19)

NatPredecessorFact previously passed raw NatPred's output directly into the
successor fact. For larger values this can be a cached but off-index atom:
NatEq agrees with NatSubtract(n,1), but identity-sensitive rule matching and
FactsCover reject an independently computed equal-valued endpoint.

The adapter now interns **only its computed predecessor** using existing
NatFromRep/NatValueIndex, threads the returned registry, then checks Succ(p)=n.
It retains the caller's original upper atom n, including an off-index upper
input. Zero/invalid-input refusals are unchanged. There is no new cache, rule,
checker clause, equality relaxation, or kernel/raw NatPred modification.

The test35 follow-up is **146/146** (~44 s): arithmetic-first and adapter-first
interning, repeated calls, natural values 17/41/1000/1000003, independent-endpoint
proofs, reversed-goal rejection, preserved upper identity, distinct anonymous
atoms, transitive joins across small/large representation boundaries and
snapshot-codec proof replay. test41 is **56/56**, and now accepts the exact
independent arithmetic endpoint while still refusing a raw off-index atom.
Full gate: **36/36 green**, ~28.7 min; test30's lookup-growth ratio is **1.04**
(first 0.0638 s/call, third 0.0667), within the unchanged 1.5x bound.

This is a producer-boundary repair for newly computed predecessor facts. It is
not general value-equality transport and does not migrate previously stored
facts or identify arbitrary anonymous atoms. Initial successor facts remain
explicit arithmetic premises; their provenance is not independently rechecked
by Checker B. W29 still cannot discharge EveryStateMoves or prove FLT.
