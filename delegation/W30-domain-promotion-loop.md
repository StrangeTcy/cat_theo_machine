# W30 — Domain packs through the closed loop (gated)

**Dimension 4 · Phase 6 · Suite slot `test42` · Prereqs W12 ✅, and receipts from W24–W27
(W28–W29 if present)**

> **Do not start until at least one of W24–W27 has produced a Checker-B-verifiable
> derivation.** Running this against the 2026-10-15 tree only restates that W8/W10
> suites do not exercise the loop.

Read `delegation/README.md` first. Read DAG §7.5 and §8 (W30).

## Goal

The closed loop (miner → Checker B → ablation → ledger) has run end-to-end on
combinatorics family 1 (`test22`). Drive it over **geometry, Engel, and funceq/NT**
derivations that Phase 4b produced.

1. For each domain that has a receipt: promote or refuse for a stated reason.
2. Ablate via `evaluator.py` on at least one domain (withhold the derived macro /
   construction / strategy; performance drops).
3. Do not weaken the receipt requirement. Do not simulate a holdout the evaluator
   did not run — W15 already reports "not run" honestly; keep that honesty.

## Done-definition

`validation/test42_domain_promotion_loop.py` green. `test7`, `test8`, `test9`,
`test28` still green. DAG §4 W8/W10/W9 notes updated if their "not claimed" items
are now met.

## Non-goals

New geometry schemas (W26), new Engel instances (W27), FLT (W28/W29), `core.py`.
