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

## Checkpoint discipline

Three artifacts, kept distinct:

1. the frozen production-code tag (shared by everything);
2. a library-only control checkpoint -- the empty research state whose
   manifest declares the packs load on demand;
3. the Set-B cumulative checkpoint -- the research state carrying the
   approved Set B episodes and learned policies.

A cold process is not a blank learned state. A baseline session boots
the control checkpoint; a cumulative-transfer session boots the Set-B
checkpoint; the audit names everything restored either way. Experiment
4's audit must state which of the two it loaded -- testing accumulated
learning requires the cumulative checkpoint, and erasing Set B learning
immediately before Experiment 4 would test the library-only machine
instead.

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

## The explanation substrate

A derivation is a certificate; an explanation is a *selection* over that
certificate aimed at a reader. They are different objects and the code
keeps them different objects. Three artifacts stay distinct, exactly as
Proved/Supported/Hypothesized do:

```text
Derivation        -- the trusted certificate, never modified by this layer
ExplanationSpine  -- a measured load-bearing subset, tagged as such
ExplanationPlan   -- the chosen idea, example and order: a rendering choice
```

An explanation that drops steps is not a shorter proof. If the spine ever
becomes the *stored* proof, soundness has been weakened to satisfy a
presentation preference, and `explanation_is_not_a_proof_test` is the pin
that forbids it.

### The spine is rule-ablation, not step-deletion

The natural design -- "remove step S, see whether the goal still closes"
-- cannot be implemented against this machine and must not be faked.
`proof.Step` carries `(current, action, next)` and the steps form a
*linear* chain: each step's `current` is the previous step's `next`.
Deleting a middle link does not produce a smaller valid derivation, it
produces a severed chain, so re-running it reports "does not close" for
every step regardless of whether that step mattered. Every step would look
essential and the measurement would be vacuous.

What is genuinely ablatable is the rule set. The spine withholds one
fired rule at a time and re-runs the same bounded search at the same fuel
from the same facts. A rule whose removal breaks closure is load-bearing;
a rule the proof routes around is not. This is
`research.counterfactual_evaluation` run subtractively -- that function
measures a rule's addition, `explanation.extract_spine` measures its
removal -- and both bottom out in the same `evaluated_search` fork so the
two directions stay commensurable.

A spine over a goal that never closed is noise, not a smaller proof:
`extract_spine` returns an empty spine and a false flag rather than
reporting every rule as essential.

### Render laws, and the rule against prose

No sentence may be generated. A render law is an Edge keyed on a term
shape; it answers either EmptyList -- declining -- or one
`RenderedSentence` carrying the law's name and its source term, so
`why did you say that` resolves to a specific law and a specific spine
step.

A sentence is a chain of pieces: word atoms and *embedded machine terms*.
A law that names an invariant embeds the invariant term itself, never a
printed copy of it, so the sentence stays connected to the object it is
about and a test can ask -- by identity, through `SentenceMentions` --
whether the real observable is present. Printing happens only at the
display edge, never inside the substrate.

There is no fallback sentence: a plan no law recognises renders as an
empty chain, and the caller must say so plainly rather than improvise. A
law that cannot name its subject declines to fire; it never emits a
placeholder such as "the invariant". An explanation sentence that cannot
cite its law is indistinguishable from generated prose, which is the
failure mode this substrate exists to make mechanically impossible.
`rendered_sentence_cites_its_law_test` pins both halves: the citation must
exist, and the sentence must embed the observable the obligation is about.

### The idea library is closed and refuses

Governing-idea classification uses a fixed, inspectable library, the same
discipline as the invariant observables. Today exactly one shape is wired:
`Invariant`, recognised by `invariance.IsPreserves`. The other shapes named
in the design -- Extremal, Bijection, Descent, Contradiction,
RepresentationChange -- are deliberately NOT stubbed. An unimplemented
classifier that returns a plausible label manufactures agreement in the
transfer test, corrupting the one measurement that decides whether the
explanation works. Each new shape arrives with its own recogniser, its own
held-out evidence, and human gating.

### Test-authoring: a fixture must exercise the mechanism it names

Found by mutation, recorded so it is not repeated. The first draft of
`spine_excludes_routed_around_rule_test` used an unrelated `noise` rule as
the thing the spine should exclude. The test passed -- and kept passing
when the ablation was mutated to "every fired rule is load-bearing",
because the noise rule never fired and was excluded by the fired-set
filter before ablation ran. The test measured nothing.

The rule, stated verbatim so it generalises past this instance:

```text
A negative fixture must reach the mechanism under test. If the case is
rejected by an earlier filter, the test passes for the wrong reason and
will keep passing after the mechanism breaks.
```

The repair was a decoy that genuinely fires: two rules deriving the same
fact by different premises, so whichever the search picks is provably
routed-around. Every test in this layer was then checked by mutation --
six mutations, each caught by exactly one test. A pinned test in this
substrate is not accepted until a mutation of the code it covers is shown
to fail it.
