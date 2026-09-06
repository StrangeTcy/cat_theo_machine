# CUR-E-ENG — Wave 1 instruction block (E1 held-out transfer test)

Provenance: authored on lane `arena/01a066cf-cat-theo-machine` at `43369fd` (the E4-route
reconciliation parent, docs-only). This is program context, not a role assignment: CUR-ORACLE
authors it; the human owns one-time setup and agent spawning. Paste to the E-eng agent when
spawned.

---

```text
# E-ENG — WAVE 1 INSTRUCTION BLOCK

Subject : E1 held-out transfer test
Mode    : read + run; NO production edits; NO pack authoring; NO label/Edge/constructor change
Discipline : substrate inspection FIRST, then stop-on-failure. Never reach the transfer test
             through a substrate that is not at parity.

--------------------------------------------------------------------------
Step 0 — explanation-substrate inspection (mandatory, FIRST)
--------------------------------------------------------------------------
Inspect the explanation substrate and confirm parity before any E1 work. The substrate is the
`E-CODE-EXPLAIN-FROM-PLAN` capability plus its constructors:

  ExplanationPlan(audience, goal, spine, core_idea, key_invariant)
  ExplanationSpine(goal, steps, baseline_cost)
  CoreIdea(goal, idea)                 KeyInvariant(problem, invariant)
  RepresentationShift(source, target, reason)
  BridgeLemma(lemma, role)             NaiveFailure(goal, obstacle)
  SpineStep(rule, verdict, fanout)     AudienceLevel(...)

Confirm, in order:
  1. the module defining the above constructors is present and loadable;
  2. the E2 parity target in `CUR-EXPLAIN-E2.md` is satisfiable by construction:
       E2 retained plan   -> non-empty ExplanationPlan
       zero-step success  -> valid plan with zero steps
       non-closing plan   -> explicit refusal (not an empty-silent EmptyList)
       RenderPlan         -> at least one sentence
       no call into `evaluated_search` on the explain path
  3. the substrate reference is the one the E-track sequencing assumes (so E builds against
     real closed G/I derivations, not synthetic fixtures).

Current observed state on this lane at `43369fd`:
  NO module defining ExplanationPlan et al. is present (the source of the substrate is ABSENT).
  Therefore parity is NOT met. This is the gate that parks E1.

--------------------------------------------------------------------------
Step 0 outcome (stop gate)
--------------------------------------------------------------------------
- If any of 1/2/3 fails: STOP. Do NOT run the transfer test. Report the failing criterion as
  the locus. Do not resolve it here; do not synthesize fixtures to mask the gap.
- If all pass: proceed to Step 1.

--------------------------------------------------------------------------
Step 1 — E1 held-out transfer test (ONLY after Step 0 passes)
--------------------------------------------------------------------------
Run through the independent checker:
  1. replay the E1 invariant derivation on the source corpus (the E1 coin substrate
     in `packs/engel-coins.pack.yaml`: flip an adjacent pair; Phi = `HeadsCountParity(?p)`;
     `PreservesLabel` / `InvariantLabel` reused from the E1 coin work unchanged);
  2. validate the invariant against held-out structurally-similar E1 variants;
  3. confirm adversarial near-miss variants are rejected;
  4. confirm proof replay through the independent checker validates transfer;
  5. confirm no regression on the established corpus.

Acceptance (only after Step 0 passes, Gate G criteria):
  - a candidate cannot become trusted without independent proof replay;
  - held-out success improves without regression on the established corpus;
  - search-policy promotion cannot alter proof validity;
  - every promotion is reversible and attributable to evidence.

--------------------------------------------------------------------------
Stop-on-failure rule
--------------------------------------------------------------------------
Any failure in Step 0 or Step 1 (substrate absent, parity gap, replay mismatch, regression)
STOPS the wave. Return the locus. Do not tag. Do not author E1 packs. Do not touch the oracle.

--------------------------------------------------------------------------
Verification
--------------------------------------------------------------------------
- recorded source of the substrate (module path or the failing criterion);
- Step 0 verdict: parity MET / NOT MET;
- if Step 1 ran: replay result, held-out result, adversarial result, corpus delta.

--------------------------------------------------------------------------
Classification
--------------------------------------------------------------------------
NON-SEMANTIC. No constructor, label, rule, matcher, codec, or registry change. No new
behaviour reachable from machine execution. No operator re-baseline required.

--------------------------------------------------------------------------
Report
--------------------------------------------------------------------------
  lane  : arena/01a066cf-cat-theo-machine
  step0 : parity NOT MET (substrate module absent)   [re-run gate]
  step1 : NOT RUN (gated)
  stop  : <failing criterion>, locus <path>
  re-run: after the first closed G/I derivation merges the explanation substrate
```
