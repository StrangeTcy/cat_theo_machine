# W29 — FLT $n=4$: `EveryStateMoves` retry (closed, precise negative)

**Dimension 1 · Phase 5 · Suite slot `test41` · Prereqs W21, W22, W23, W6 `[~]`**

> **Reported 2026-10-19:** test41 passes 54/54 with a precise negative. No
> EveryStateMoves discharge or FLT theorem. Do not re-dispatch this brief
> unchanged. W21–W23 were green for this retry; W6/test26 remains historical.
> See the completion note below for the remaining gaps.

Read `delegation/README.md` first. Read DAG §4 W6, §6.5, §7.1 and §8 (W29).

## Goal

`test26` reduced the theorem to `EveryStateMoves(descent)`. Retry each missing item
with the new machinery:

- Witness introduction for $(m,n)$ / $(u,v,w)$ (W21).
- Ring normalisation of the grid identities (W22).
- Factorisation / `NatLess` (W23).

Do not author a quartic rule, a parametrisation, a constant or a lemma about squares.
The parametrisation remains a human-stated candidate until the machine discovers or
derives it; `test26` already said so.

## Done-definition

First reachable of {full, partial, precise negative}, as in W6. New suite
`validation/test41_flt_n4_everystate.py`. **Do not modify `test26`'s claims** — it is
the historical negative account. If you discharge `EveryStateMoves`, this suite
asserts that, and DAG §4 W6 is updated to point here.

## Files

New `test41`. Consume `playground.py`, `graph_task.py`, `math/arithmetic.py` as they
stand after W21–W23. No `core.py`. No revival of `flt-quartic`.

## Non-goals

$n=3$ (W28), the full FLT, weakening the ledger, rewriting history in `test26`.


## Completion / coordinator handoff (2026-10-19)

Outcome: **precise negative** (the permitted third outcome), not a mathematical
counterexample and not a statement that no future prover could do it.
`validation/test41_flt_n4_everystate.py`: **54/54**, ~67 s. Full sequential gate:
**36/36 green** (test1–test35 plus test41), ~28.9 minutes. No production module,
pack, test26 claim, checker policy or ledger gate was changed.

### Retry results

1. **Witness introduction:** W21 allocates fresh recorded handles; they are not
   naturals. NatSubtract and CoprimeCofactors refuse those handles. It does not
   solve the equations a parametrisation or square-root construction requires.
   The suite mints only an opaque template as a capability probe, not a trusted
   mathematical existence schema.
2. **Algebra:** both grid-derived W6 identities have real Checker-B grid proofs
   under the explicit W22 capability. The same proofs fail against the movement
   goal. The default RewriteEquals still lacks symbolic normalisation, but grid
   certification is no longer the immediate obstacle.
3. **Factorisation:** gcd extraction is available. On the concrete square inputs
   4 and 9 it returns cofactors 4 and 9, not roots. The (2,8) decoy retains gcd 2.
   These are data-level probes, not an authored square-factor lemma. Neither
   parametrisation completeness nor the coprime-square-factor theorem is derived.
4. **Measure:** a human-selected W6 family input (2,1) computes 5 and 41 and an
   arithmetic verdict 5<41. No derivation of the universal measure drop follows.
   The immediate predecessor of 41 reveals a further integration gap: the 40-valued
   predecessor atom and the 40-valued independently subtracted atom are NatEq-equal
   but not identical. The generic successor schema yields a Checker-B-verified
   order fact for the former. Verifying that same proof against the latter gives
   GoalMismatch. No equality-transport step is silently inserted.

### Why this is more than an exhausted search budget

The suite loads **all 17 registered packs**, audits **all 206 raw rule replacement
terms**, including constructors hidden behind atoms, and finds zero occurrences of
EveryStateMovesLabel and ExistsLabel. The initial source knowledge does not contain
the movement label either. Ordinary knowledge rewriting substitutes source subterms
and fresh handles into those templates; it cannot introduce that absent label.
This is a structural obstruction for the audited ordinary transition system, not
a formal invariant-kernel certificate or a claim about every planner method, external
grid action, future tactic or mathematical proof. One-step search/forward retries
are separately labelled bounded. The Exists term is an obligation marker using the
existing vocabulary; no new quantifier semantics is claimed.

The strategy skeleton still needs EveryStateMoves as an explicit premise. Its
receipt verifies only with that premise, and the scope guard rejects relabelling
it as unconditional. The actual movement claim and a skeleton replay missing that
premise are both submitted to the real evaluator/ledger: GoalMismatch /
PromotionRejected, version **0**, no active promotion. Verified polynomial or
conditional order receipts must not be promoted as a verified descent macro.

### What must change before another retry

- Generic constrained arithmetic witness construction (not anonymous allocation).
- Derived parametrisation completeness and the coprime-square-factor argument.
- Natural-value equality/transport for facts and goals, with Checker-B provenance
  preserved; do not fix this by making arbitrary anonymous atoms compare equal.
- A checked construction that preserves source-solution membership and strictly
  decreases a well-founded measure, plus coverage of **every** source state.

No new rule concludes EveryStateMoves, no smaller solution is asserted, no quartic
pack is revived, and no result here proves FLT. The isolated receipts do not clear
W30's domain-macro gate as an FLT success.
