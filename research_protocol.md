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

## Ledger: defect ten -- compile-once versus structural keys

```text
Defect: mine_compressed_laws keyed motif pairs by IdentityCompare on
compiled rule objects. The live REPL recompiles taught rules per attempt,
so identical laws across traces never shared a key. Mining silently
returned zero motifs on every live session.

Fix: structural pair keys using alpha-normalized rule forms.

Lesson: a test that compiles once and a live path that compiles per
attempt are testing different machines. The divergence is invisible until
a live session is run as a measurement.

Evidence: SameLawTwiceCompiledTest (pinned); live near-transfer rerun
showing motif found and macro proposed.
```

This is the second historical appearance of one class -- head-bucket
memoisation in the search stack, pair keys in the miner. The class is
named rather than the instance, because the verbatim rule prevents a third
appearance more reliably than either specific fix.

### Test-authoring, from the same class

Two rules now govern authoring in this area. Both were found by
measurement, not by review.

```text
Build terms through _research_parse. A test that constructs terms by hand
exercises a simplified analogue; a test that parses them exercises the
live grammar. SameLawTwiceCompiledTest and ReplyAgreesWithGateTest are the
first research tests to go through the full taught-law pipeline rather
than a harness shortcut.
```

```text
A negative fixture must reach the mechanism under test. If the case is
rejected by an earlier filter, the test passes for the wrong reason and
will keep passing after the mechanism breaks.
```

## Ledger: the predicate-identity wall, and the option 1 / option 2 decision

```text
Finding: The induced transport macro retained 'Divides' as its head.
It increased search noise on congruence proofs (8 firings vs 5 masked)
and provided no speedup. Anti-unification generalized arguments while
preserving predicate identity.

Decision: Option 2, narrow scope only.
  - Predicate head position becomes generalizable.
  - Generalization requires motifs from at least two distinct relation
    families carrying a shared extensionality contract.
  - Schemas do not fire directly; they instantiate concrete laws only for
    contracted relations.
  - All instantiated laws pass the existing rent gate, support threshold,
    human approval, and ablation cycle unchanged.
  - One new negative control required before first use: a schema must not
    instantiate for a relation whose argument structure matches but whose
    semantic contract is absent.

Scope explicitly excluded: second-order motifs over predicate positions
in premises; cross-domain predicate abstraction without semantic contracts.

Evidence: near-transfer session on fifth cut showing 8 vs 5 firings;
predicate-identity wall confirmed by independent mechanism (anti-unifier
retains conclusion head).
```

Why the scope is narrow, recorded so the boundary is not quietly widened
later. The wall is confirmed twice by independent mechanisms -- the B1
groundness wall and the Rung 7 alphabet wall -- and that is this project's
standard for naming a capability boundary rather than a defect. But the
confirmation establishes option 2's *justification*, not its *scope*. The
evidence in hand is one transport macro bound to `divides` failing on
`congruent`, and that justifies exactly the narrow reading.

The wide reading -- second-order motifs generally, laws quantifying over
predicate positions anywhere in premises and conclusions -- is a new
expressive tier the rent gate has never been validated against. It moves
the over-generalization failure mode from "the law fires on wrong
instances of the right predicate" to "the law fires on structurally
similar instances of the *wrong* predicate", and the current negative
controls do not cover that shape. If the narrow version pays rent and
survives its controls, the wide version becomes a later, separately-gated
decision.

Experiment 4 remains unspent.

## The FLT programme: curriculum, blind session, and grading instrument

A human reference decomposition of FLT exists in the session notes. It is
an *oracle*, never a curriculum. It is consulted after a transcript is
recorded, to grade what the machine asked for. It is never taught, never
pasted into a live session, and never used to choose what to teach next.
Teaching from the oracle converts the experiment into a rehearsal.

### Two activities, two ledger headers

Activity A -- CURRICULUM. Generic number theory taught in its own right:
divisibility, Bezout, prime factorization, well-ordering, descent. These
sessions never mention FLT and never mention exponents above two. What they
establish becomes LIBRARY_THEOREM for later sessions.

Activity B -- RESEARCH. The target sentence is stated once. The machine
stalls. `suggest dependencies`. Only what a residual actually asks for is
taught, and only when it passes the seven questions. One shot.

The separation is the whole experiment. Teaching a reduction in A because
the oracle says it is coming in B is contamination, and it is invisible
afterwards unless the ledger header says which activity a theorem came
from.

### Substrate facts, measured rather than assumed

The parser accepts arbitrary heads. `(zorblewidget x y)` parses exactly as
cleanly as `(nosolutions ...)`, so a successful parse is evidence of
nothing at all. Vocabulary claims must be checked against pack rules and
against what the search can fire, never against the parser.

Checked this way: `nosolutions` appears in zero pack rules. Neither a
producer nor a consumer exists. This is the B3 finding, confirmed directly
rather than inferred, and it is the first blocker on the path.

### The Layer 0 gap, stated precisely

A rule of the shape "if every candidate yields False then nosolutions"
*produces* `nosolutions` and does not consume it. Teaching only that
direction reproduces the B3 dead end one step later: the machine can
introduce the conclusion and then do nothing with it. Layer 0 needs both
directions, and the consumer is the one that is missing. Any A1 session
that ends with a producer and no consumer has not closed Layer 0,
regardless of whether the toy goal went green.

### Recall-eligible versus discovery-eligible roles

Grading by role coverage is unfalsifiable unless the split below is fixed
in writing *before* the B session runs. A curriculum session that
rehearses a move converts that move from evidence of discovery into
evidence of recall.

Recall-eligible, because Activity A teaches them directly: primitive
normalization, descent, exponent transport. Their appearance in B confirms
the library works and is not evidence about the machine's reach.

Discovery-eligible, because nothing in the library points at them:
exponent structure (splitting `n` by divisibility), impossibility
transport (a `nosolutions` bridge across substitution), and the richer
object (attaching an object whose invariants are forced two incompatible
ways). Only these three are evidence.

A transcript covering all three recall roles and none of the discovery
roles is a negative result, and must be recorded as one.

### The required negative control

Role-coverage scoring cannot by itself distinguish "the machine
characterized this dependency graph" from "the machine emits this request
list for any unsolved Diophantine statement." Before the B transcript is
graded, the identical stall-and-`suggest dependencies` loop is run on a
decoy of matching surface shape and known-easy resolution -- the same
equation restricted to the solvable exponent, or the same shape with the
right side left un-powered. If the residuals come back substantially the
same, the transcript measures the residual generator's default output and
the FLT reading is withdrawn.

### Scope

The reachable target is a complete impossibility proof at the smallest
even exponent. It exercises well-ordering with a strictly decreasing
measure, case split, coprimality, and exponent algebra, and its dependency
graph is small enough to compare against the oracle honestly.

The odd-prime case is out of scope here for a structural reason, not a
difficulty reason: it needs a new number system carrying norm and units.
That is concept acquisition, a different experiment with a different
gate, and it does not belong in a dependency-discovery session.

Everything above the odd-prime case is out of current expressive range.
The machine has no vocabulary in which those objects could be stated, so
"it failed to request one" is not a measurement and must not be scored as
one. Grading is by structural role, never by the human name attached to
the answer.

### Stop condition

The programme stops at the even-exponent result. No FLT explanation is
attempted, and the explanation substrate is not pointed at this target.
The deliverable is a transcript in which every taught theorem traces to a
recorded residual and every unlock is measured, not a claim that a
theorem was proved.

## Ledger: the learned-memory checkpoint failure is not contamination

The `learned_memory_checkpoint_test` failure resisted three successive
explanations. Each was tested and each was wrong. The sequence is recorded
because the errors were methodological, not arithmetic, and they recur.

First explanation: state contamination from a predecessor test. The taught
rules from an earlier research test survived into this one. That much was
real, and `DropRulesByOrigin` fixes it: the test now passes on repeat
in-process and in isolation. It did not fix the suite failure.

Second explanation: eager test registration, so shard membership filters
reporting rather than execution. This was checked with an AST pass over
`install_default_tests` rather than by reading line by line. Every one of
the 226 test constructions sits inside a `TestShardAccept` guard, and the
construction is an argument to `_register_test` inside the taken branch.
Registration is already shard-guarded. Shard membership already is
execution membership. A lazy-registration patch would have been a no-op
against a defect that does not exist, and the pinned test for it would
have asserted an invariant already held.

Third explanation: accumulated registration volume breaks the snapshot.
A probe registered the 109 true predecessors through `_register_test` and
reported `False`, against `True` for the same predecessors constructed
without registration. That looked like a clean A/B. It was not. Repeating
the registration arm with a trivially-serializable test -- 96 registrations
of `Compare(a, a)`, no research state anywhere -- returned `True` on three
consecutive runs, with `n=0` returning `True` on three more. The single
`False` came from a run whose log carried `RuntimeError` spam from spawn
workers. It was a polluted process, not a measurement.

What actually holds: the test is nondeterministic under load in a way that
is not caused by predecessor state, not caused by registration volume, and
not yet characterized. `DropRulesByOrigin` remains correct and stays.

Three method rules, each earned by a wasted cycle:

A single run is not a measurement when the process spawns workers. Every
repeat probe carries an environment-variable parent guard, never a PID
guard -- spawn children recompute `os.getpid()` and pass a PID check,
emitting contradictory result lines into the same stdout. Any conclusion
drawn from one run of a spawning process is provisional until repeated.

Read the guard structure with a parser, not with `grep` and a
previous-line heuristic. The line-based check reported 179 unguarded
constructions; the AST pass reported zero. Multi-line call forms defeat
line heuristics entirely.

Probe scripts live in a subdirectory, never directly in `/tmp`. A file
named `/tmp/bisect.py` shadows the stdlib `bisect` that `random` imports,
and the resulting `ImportError` presents as a circular-import defect in
`provenance.py`. That cost most of a session.

The 8-failure two-shard number stands, with this test named as a known
nondeterministic red rather than a contamination defect.

## Distributing the work: roles, partition, and what actually blocks what

The evidence standard depends on one frozen build per measurement, while
five tracks want to change code at once. The split that survives that is not
one agent per track. It is two kinds of agent over two kinds of artifact.

Engineers change code on track branches and produce the next frozen cut.
Operators run sessions on the current cut and produce measurements. One
integrator merges, runs the full two-shard suite, cuts tags, and owns this
index. Engineers never cut tags. Operators never edit code. The integrator
writes no track features.

Operators run one cut behind engineers, and that is correct rather than
unfortunate: a measurement is only valid against a frozen build, and the
build engineers are changing is by definition not frozen. When a new cut
lands, operators rerun blank controls before any measurement counts.

### The one agent who must stay blind

Every engineer has read the reference decomposition. The operator who runs
the blind session must not have. That operator gets a fresh context, no
reference graph, no curriculum answers, and no other track's logs. The same
discipline that keeps the reference graph out of the machine keeps it out of
that operator.

The exam has the same shape of leak. Whoever authors the curriculum must not
also choose the held-out problems, or the curriculum drifts toward the test
without anyone intending it. The held-out set is selected before curriculum
work begins, its hash is committed here, and problems are revealed one at a
time when the exam runs.

### File partition, installed rather than agreed

Four files would otherwise be fought over every merge. Three now carry
per-track marked blocks -- `labels.py`, `testsuite.py` for both class
definitions and registrations. Append inside your own block; do not edit
another track's. Shared primitives are requested from the integrator, never
forked into a track block.

The registration blocks sit after every existing test, which is not
cosmetic. `TestShardAccept` ticks the shard cursor on every guarded block,
so a registration inserted earlier shifts every later test across the shard
boundary and the failure set stops being comparable to the recorded
baseline. It also keeps `learned_memory_checkpoint_test` at its current
cursor index.

The fourth file is this one. It is now an index; each track writes ledgers
to `protocol/<TRACK>.md`. Two agents never edit the same ledger file.

### What blocks what

The shared baseline fix blocks the next tag cut and every claim that the
suite is green. It does not block engineering on track branches, and it does
not block sessions on the current cut.

The critical path runs strategy wiring, then curriculum sessions, then the
exam, because that chain is where proof volume for mining and for
explanation comes from. Everything else is parallel to it. Staff the front
of that chain first.

Distribution multiplies engineering and session throughput. It does not
shorten the serial chains inside a track, and it makes the integrator the
bottleneck for tag cuts. That role wants the most disciplined agent, not the
most ambitious one: the shared fix, the merge order, the suite, and nothing
creative.
