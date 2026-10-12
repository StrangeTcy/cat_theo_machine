# W9 — IMO combinatorics, functional equations, number theory

**Dimension 2 · Phase 1 · Suite slot `test22` · Prereq W4 ✅ (done)**

Read `delegation/README.md` first — shared invariants, environment facts and pitfalls are
binding here.

## What already exists

- `graph_task.py` — canonical graph-task ingestion, `NormalizeGraphFacts`, and
  `ForwardDeriveFacts` **with multi-premise support** (`MatchQueryConjunction`, added by the
  newer lineage; the older one only had unary rule application). This is your main engine for
  combinatorial configurations: facts as a hypergraph, rules firing over conjunctions.
- `curriculum.py` + `curriculum/tier0`, `tier1` — a card/decoy/heldout structure covering
  pigeonhole, extremal, invariance, symmetry and divide-and-conquer families, verified by
  `test10_graph_curriculum.py`. **Read this before designing anything**: your combinatorics
  work should slot into it, not parallel it.
- `invariant_miner.py`, `evaluator.py` — invariant discovery with ablation and holdout
  gates (`test8`, `test7`).
- `promotion_ledger.py` — dual-ledger promotion, refuses entries without a Checker B receipt
  (`test9`).
- Packs: `arithmetic.pack.yaml` (generic arithmetic-progression knowledge),
  `sequence-order.pack.yaml`, `algebra-distribute.pack.yaml`, `real-closure.pack.yaml`,
  `order-sign.pack.yaml`, `sqrt-real.pack.yaml`.

## Goal

Three families, in this priority order — deliver the first well rather than all three
shallowly:

1. **Discrete combinatorial configurations** (extremal sets, tournaments, graph-colouring
   style counting): express configurations as fact hypergraphs, let `ForwardDeriveFacts`
   close them under multi-premise rules, and let `invariant_miner.py` find the monovariant or
   invariant that terminates the argument. The curriculum's tier0/tier1 cards are ready-made
   instances — use them as *evaluation data*, never as encoded answers.
2. **Functional equations** (Cauchy, d'Alembert): derive additivity/multiplicativity
   consequences from the equation as a rewrite schema over the existing arithmetic and
   real-closure packs. The equation itself is the input; the consequences must be derived.
3. **Number theory** (coprimality, divisibility, residues): reuse the Peano + `GMPRep`
   machinery in `math/peano.py` (`NatPred`, `NatEq`, `NatLess`) and the sweep idiom from
   `playground.py` that `test18_flt_residue_discovery.py` demonstrates.

## Done-definition

- At least one configuration per family solved end to end: derived by machine rules, verified
  by Checker B, and either promoted by the ledger or refused *for a stated reason* (a refusal
  with a reason is a pass; a silent skip is not).
- **Held-out evidence**: the curriculum's `heldout/` cards must be solved without appearing in
  anything you authored, and the `decoys/` must be rejected. `test10` shows the idiom. This
  is what separates discovery from memorization, and it is the §5.3 hardcoding rule in
  operational form.
- Ablation via `evaluator.py`: the derived invariant must measurably help.
- The suite states what fails and why. Partial coverage of the three families is fine;
  claiming coverage you do not have is not.

## Files

- New: `validation/test22_imo_combinatorics_funceq.py`, plus whatever module the work needs
  (a functional-equation schema module is a reasonable candidate).
- Extend: `graph_task.py`, `invariant_miner.py`, `curriculum.py`, `labels.py` (append-only).
- Packs: ontology/generic schemas only; register any new pack in `main.py:PACK_PATHS`.
- Do not edit `core.py`. Do not weaken `checker_b.py` or the ledger's receipt requirement.
- Do not add cards to `curriculum/` that encode a solution; cards are evaluation data.

## Verification

`PYTHONPATH=/home/user .venv/bin/python -u validation/test22_imo_combinatorics_funceq.py`
green, plus all 19 existing suites green. Highest regression risk: `test10` (curriculum),
`test8` (invariant miner), `test7` (evaluator/ablation), `test9` (promotion loop),
`test15` (planner, if you touch `graph_task.py` interfaces it consumes).

## Non-goals

Geometry (W8's brief), Engel's strategies as a *general* framework (W10's brief — coordinate
if you both touch `invariant_miner.py`), `core.py` edits, and any per-problem special case.
