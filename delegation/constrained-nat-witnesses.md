# Constrained natural witnesses — bounded substrate follow-up

Implemented 2026-10-19 after the W29 endpoint repair. Supplemental suite slot
**test46**; W24–W33's allocated slots test36–test45 are unchanged.

## Delivered API

`playground.FindNatWitness(constraints, variables, bound, budget, registry)`
streams assignments in `[0,bound)^arity`, first variable changing fastest.
Constraints are a machine Pair chain of `ExprEq(lhs,rhs)` / `ExprLt(lhs,rhs)`.
Sides use the existing admitted natural-polynomial fragment: declared formal
atoms, natural constants, ExprInt, ExprAdd, ExprMul, and natural-exponent ExprPow.
Variables must be distinct nonnumeric formal atoms; opaque Thingy variables are
allowed, but binding them does not mutate them into naturals.

Output is `Pair(record, Pair(registry, []))`, with the record fields:

```
NatWitnessSearchLabel(constraints, variables, bound, budget,
                      status, environment, examined)
```

The environment is a chain of `Pair(variable, Pair(Nat, []))` in declaration
order. Four separate status labels distinguish Found, Exhausted, Budget, Invalid.
Only Found carries an assignment. That assignment can itself be empty when
there are no variables; inspect the status, not environment emptiness.

- Exhausted means **this finite box**, never no natural solution.
- Budget means candidate checks ran out, not exhaustion or invalidity.
- Invalid means malformed/unsupported syntax, missing variables, duplicates,
  or invalid bound/budget sorts. The entire request is syntax-validated first.
- The empty-dimensional product contains one empty tuple, even at bound zero.
  Positive arity at bound zero is an empty domain and exhausts with zero checks.
- Budget limits candidate checks, **not** expression depth, exponent magnitude,
  arithmetic size, or wall time. Enumeration is streaming; no Cartesian product
  is materialised. Structural recursion is still used over variables/expressions.

`playground.VerifyNatWitness(constraints, variables, bound, environment, registry)`
checks the caller's exact problem, exact binding shape/order, natural sorts and
bounds, then re-evaluates the assignment using existing arithmetic. It returns
`Pair(true/false/[], Pair(registry, []))`: malformed inputs/assignments yield [],
a well-formed assignment violating a constraint yields false. It does not trust
or consume the search record's success flag, count, or exhaustion claim. It
checks a **positive assignment only**, not a negative-search certificate.

## Validation

- `validation/test46_constrained_nat_witnesses.py`: **185/185**, ~8 s.
  Numeric multi-variable constraints, streamed carries through the last tuple,
  budget/exhaustion distinction, zero-dimensional cases, a solution just outside
  an exhausted box, opaque formal variables, malformed syntax/coverage/bindings,
  out-of-bound and changed-goal refusal, snapshot-codec replay and refusal to
  treat a search record as a proof of universal movement.
- `validation/test41_flt_n4_everystate.py`: **61/61**, ~60 s.
  A clearly human-supplied numeric fixture `2mn=4`, `m²+n²=5`, `0<n<m`
  recovers `(2,1)` after seven checks with bound 4 and budget 9. This is a
  numerical candidate probe, not discovery/completeness of a parametrisation.
- Full sequential gate: **37/37 green** (test1–test35, test41, test46), ~27.5 min.
  test35 remains 146/146. test30 growth ratio 1.07, within the unchanged 1.5x gate.

## Trust boundary and next work

These are **computed arithmetic assignments**, not Checker-B derivations,
existential theorems, trusted source premises, or ledger receipts. The verifier
is independent of enumeration, not independent of the existing arithmetic and
expression evaluator. There is no new checker capability, inference rule, pack,
quartic schema, square-factor lemma, or automatic introduction into knowledge.
Existing arithmetic premise provenance is not strengthened by this change.

W29 still has no EveryStateMoves producer (17 packs / 206 raw rules). Its actual
ledger refusal checks remain green: version 0, no domain promotion. Generic
bounded arithmetic witness search is now available; source-state-uniform witness
construction, parametrisation completeness, coprime-square-factor proofs and a
checked smaller-state construction with coverage of every source remain missing.

Next useful integration: carry explicit numeric bindings and their exact source
constraints into a provenance-checked construction interface. Do not turn a
finite search hit into an unconditional existence schema, substitute it for
parametrisation completeness, or use finite exhaustion as a universal negative.
Do not re-run the unchanged descent attempt as if this cleared those gates.
