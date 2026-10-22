# W7 — FLT $n=3$: Eisenstein UFD factorization and cubic descent

**Dimension 1 · Phase 1 · Suite slot `test20` · Prereq W3 ✅ (done)**

Read `delegation/README.md` first — shared invariants, environment facts and pitfalls are
binding here.

## Context you must respect

The DAG's original deliverable was `packs/flt_eisenstein.pack.yaml`. **Do not hand-author
that pack.** The sibling worker W6 did exactly that for $n=4$ and the pack was withdrawn as
a hardcoding violation (`524de6f`); the lesson is recorded in DAG §4 and §5.3. Build the
machinery and let the machine derive the instance.

The precedent to imitate is `validation/test18_flt_residue_discovery.py`: a bare machine
with **no packs loaded**, where the Cartesian sweep discovers the relevant modulus, the
machine's own arithmetic runs the complete residue case analysis, the discovery record names
its own candidate lemma, and the promotion ledger is asked to promote it and **refuses**
without a Checker B receipt. Read that suite before writing anything.

## Goal

Give the machine the Eisenstein integers $\mathbb{Z}[\omega]$ as *generic* algebraic
structure — not as stated cubic facts — and let it discover the obstruction for $n=3$ the
same way it discovered the modulus-4 obstruction for $n=4$:

1. Represent $\mathbb{Z}[\omega]$ generically: elements as pairs of integer coordinates,
   multiplication by the relation $\omega^2+\omega+1=0$ expressed as a generic schema, and
   the norm $N(a+b\omega)=a^2-ab+b^2$ as a derived quantity, not an asserted lemma.
2. Use `playground.py` sweeps to discover which modulus / which residue-class structure
   separates the cube image from the relevant sum image. Discovery must be a sweep result,
   not a constant you wrote.
3. Run the complete residue case analysis with the machine's own arithmetic (Peano +
   `GMPRep`; `NatPred`, `NatEq`, `NatLess` are in `math/peano.py`).
4. Produce a candidate lemma named by the discovery record, then ask
   `promotion_ledger.py` to promote it and record what it says.

## Done-definition

- A discovery suite in which nothing cubic is written by hand: no cube identity, no named
  lemma, no solution constant appears in the tree.
- Whatever the machine derives is Checker-B-verifiable; if a receipt exists, the ledger
  promotes it (version increments). If no receipt exists, the ledger refuses and the suite
  asserts the refusal — that is a passing outcome, exactly as in `test18`.
- The suite states plainly what is **not** derived (e.g. full unique factorization in
  $\mathbb{Z}[\omega]$, the descent itself). Ambiguity here is a defect.

## Files

- `math/arithmetic.py`, `math/peano.py` — extend with generic ring/norm scaffolding if
  needed. Keep it sort-generic; if it only works for cubes it is hardcoding.
- `playground.py` — sweeps and tensor evaluation (already has both; see
  `validation/test16_tensor_evaluation_mining.py` for the idiom).
- `labels.py` — new labels go here (append; both lineages added ~84 lines recently).
- `invariant_miner.py`, `evaluator.py`, `promotion_ledger.py`, `checker_b.py` — consume, do
  not weaken.
- New suite: `validation/test20_flt_eisenstein_discovery.py`.
- A pack is permitted only as ontology (the sort, constructors, generic schemas). If you add
  one, register it in `main.py:PACK_PATHS` and keep it problem-agnostic.

## Verification

`PYTHONPATH=/home/user .venv/bin/python -u validation/test20_flt_eisenstein_discovery.py`
green, plus all 19 existing suites green. Watch `test3_pack_load.py` if you add a pack, and
`test13`/`test16` since you are extending the playground.

## Non-goals

$n=4$ (W6's brief), the full theorem, `core.py` edits, and any relaxation of the ledger's
receipt requirement.
