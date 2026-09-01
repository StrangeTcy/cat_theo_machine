# Live research protocol

The rules of the experiment, fixed before the experiment. Code changes
after the freeze tag are instrument repairs, not research: they cut a new
tag and invalidate any session log that spans two tags.

## Session discipline

- Every session log begins with a contamination ledger header: which laws
  and axioms were operator-supplied, and what prompted each teaching. A law
  taught in response to a concrete residual is recorded as such; a law
  pre-loaded by curriculum design is recorded as such. Nothing supplied may
  later be attributed to discovery.
- Every session log header records the freeze tag it ran on. A log spanning
  two tags is not admissible.
- The git ritual: record the remote tip hash before work, compare before
  any push, never force.

## What research mode is

`research mode on` disables nothing. All knowledge the machine holds is
active — taught rules, domain axioms, loaded theorem packs, prior-session
lemmas, learned policies, the derivation cache — and every use is
provenance-tagged. Purity was never the goal; attribution is.

- `audit knowledge` is the manifest. It states explicitly whether the
  theorem packs are loaded; a transcript must never be misreadable as "the
  machine had the library and found no foothold" when it had nothing.
- The derivation cache answers only after a fresh bounded search
  revalidates the goal against the current rule set, and it answers as
  DERIVATION_CACHE_HIT — retrieved, never counted as SEARCH_DERIVED.
- Decidable ground arithmetic never becomes a request. A fully ground
  evaluable obligation is discharged by evaluation (recorded DOMAIN_AXIOM)
  or refuted (recorded COUNTEREXAMPLE). If a computable request within the
  evaluator's coverage reaches the operator, the evaluator failed and the
  instrument is broken — that is a defect report, not a teaching
  opportunity. Residuals are therefore theorem-shaped or
  evaluator-coverage gaps; the operator distinguishes them by asking
  whether the premise is ground and decidable. A ground decidable
  predicate outside the wired coverage (e.g. primality, absent an edge)
  surfaces as a request and must be treated as a coverage gap, not
  taught as a theorem.

## Where requests come from

Only from genuine footholds of operational rules:

- a partial premise match under the goal-to-rule substitution, or
- the conclusion-to-goal unification of a rule blocked on its premises.

No foothold means UncharacterizedStall: "search stalled, and I cannot
characterize the missing theorem." That answer is preferred to any guess.
Requests are ordered deepest evidence first. Strategy priors, if any are
taught, are quarantined by provenance and displayed as suggestions from a
preinstalled prior.

## How usefulness is established

Approval is a hypothesis. A taught theorem becomes DemonstratedUseful only
through the counterfactual fork: baseline bounded search versus the same
search with the compiled taught rule, same fuel, measured — goal closed,
existing rules newly enabled, residual cost decreased, or new residuals
exposed. Otherwise it is stored as
HUMAN_SUPPLIED_TRUSTED_THEOREM_WITHOUT_UNLOCK_EVIDENCE and the reply says
the theorem was stored but did not unlock the parent goal.

Two independent useful episodes anti-unify into a LearnedDependencyPolicy.
Policy predictions must appear with learned memory enabled, disappear under
`disable learned memory`, reappear under `enable learned memory`, and die
permanently under `reset learned memory`, while the raw residual-derived
requests survive every toggle. Any suggestion that violates this cycle is
hardcoded and is a defect.

## Experiment 4 (the target sentence)

Run once, cold, on the frozen tag:

```text
research mode on
load theorem packs        # mandatory: the research question is what the
                          # machine does with everything it has; a run
                          # without packs answers the blank control instead
audit knowledge           # save output as the cold-start manifest
prove that <the sentence>
suggest dependencies
```

Then, per request: did it arise from an actual foothold; is it formal; is
it non-circular; does temporary assumption produce measured progress; is it
narrower than the conclusion itself; could it transfer. Teach one law per
concrete residual. Reject false requests. A computable request is an
instrument defect. Classify the outcome:

- A — uncharacterized stall (no foothold; a valid result),
- B — blocked but characterized (concrete formal obligations),
- C — policy-predicted (a learned policy instantiates a helpful shape),
- D — closed (report provenance composition: retrieved / derived /
  evaluated / human-supplied).

Post-hoc scoring uses semantic roles against the external reference graph,
which is never stored in the repository, checkpoints, prompts, or tests.
