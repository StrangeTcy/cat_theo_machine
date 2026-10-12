# W6 (remainder) — Pythagorean parametrization descent for FLT $n=4$

**Dimension 1 · Phase 1 · Suite slot `test26` · Prereq W3 ✅ (done)**

Read `delegation/README.md` first — the shared invariants, environment facts and pitfalls
there are binding here.

## Where this worker actually stands

W6 is **not** unstarted. It is `[~]` in the DAG, and the reason matters:

- A hand-authored `packs/flt-quartic.pack.yaml` was written, then **withdrawn as a
  hardcoding violation** (`524de6f`). Nothing in this tree may contain a quartic rule, a
  solution constant, or a named lemma.
- What survives is machine-derived and verified in `validation/test18_flt_residue_discovery.py`:
  the Cartesian sweep discovers that modulus 4 separates the square image $\{0,1\}$ from
  the odd square-sum image $\{2\}$; the machine's own arithmetic runs the complete residue
  case analysis over all four classes; the discovery record names its own candidate lemma;
  and the promotion ledger **refuses** to ledger it, because a ledger entry requires an
  Independent Checker B receipt over a machine-verified derivation and a sweep discovery
  carries none. Ledger version stays at zero.
- The DAG's own verdict: *"The Pythagorean parametrization descent needed for the full
  theorem is not derivable by the current machinery and stays open."*

**Your job is that open half — and the honest outcome may be a negative result.**

## Goal

Make the descent step machine-derivable: given the residue obstruction already discovered,
drive the classical infinite-descent structure for $n=4$ (a primitive solution yields a
smaller one) far enough that a Checker B receipt exists over a machine-verified derivation,
and the promotion ledger will then accept it.

## Done-definition

Pick the first of these you can actually reach, and say explicitly which one you reached:

1. **Full**: a machine-derived descent derivation, Checker-B-verified, ledger-promoted
   (version > 0), suite green.
2. **Partial**: the descent step derived for the parametrized family the machine can
   represent, with a written statement of exactly which hypotheses are still missing, and
   the ledger refusing for a *stated* reason.
3. **Negative (acceptable, valuable)**: a precise, demonstrated account of *why* current
   machinery cannot express the descent — which constructor, quantifier, or well-founded
   measure is absent — with a suite that asserts the obstruction rather than the theorem.
   Update DAG §4 W6 with that account.

A negative result that is precise beats a positive result that hides a hardcoded step.
Do not smuggle the descent in as authored rules; that is exactly what got withdrawn.

## Files

- Extend, do not duplicate: `playground.py` (sweeps, tensor evaluation), `math/peano.py`,
  `math/arithmetic.py`, `invariant_miner.py`, `evaluator.py`, `promotion_ledger.py`,
  `checker_b.py`.
- `checker_b.py` currently carries knowledge-rewrite verification (`_knowledge_reproduces`,
  `_apply_knowledge_rule`, `FactsCover` goal matching). Preserve it — `test19` depends on it.
- New suite: `validation/test26_flt_descent.py`. Do not modify `test18`; import or reuse it
  if you need its discovery step.
- If you author a pack, it may contain ontology only (sorts, generic schemas). No quartic
  rule, no constant, no lemma name.

## Verification

`PYTHONPATH=/home/user .venv/bin/python -u validation/test26_flt_descent.py` green, plus all
19 existing suites still green — especially `test18` (residue discovery), `test19`
(knowledge rewrite), `test13` (playground), `test9` (promotion loop), `test5` (Checker B).

## Non-goals

$n=3$ (that is W7, a different brief), the full FLT, and any change to `core.py`. Do not
weaken the ledger's receipt requirement to make promotion succeed — that requirement is the
point of Dim 4.
