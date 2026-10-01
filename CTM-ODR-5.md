# CTM-ODR-5 — Dispatch specification for a bounded, checked learning loop

**Status:** repository-grounded coordination specification; **not an implemented feature or a release verdict**.

**Date:** 2026-10-01 (UTC).

**Repository:** `StrangeTcy/cat_theo_machine`.

**Inspected base:** `428ecdc146e38de3481222bed7bddeb3c08e1b2d`; tree `7f3bb80396080a154b99f73ae995745282895b5d`.

**Session branch:** `arena/01a0f75a-cat-theo-machine`.

**Time ceiling:** 16 hours **including** preflight, repairs, and final verification; shorter if the approved deadline is earlier.

**Organization:** one integrator, a contract/test steward, two induction workers, two checker workers, application, admission/residual, persistence, evidence/coordinator workers, and an independent red team. Roles may be combined except the independence boundaries below.

Companion artifacts:

- [Machine-readable DAG, ownership, acceptance IDs, and dispatch defaults](protocol/closed_loop/tasks.json).
- [Measured baseline, limitations, and reproduction procedures](verification/closed_loop/BASELINE_2026-10-01.md).
- [Structured baseline receipt and evidence hashes](verification/closed_loop/baseline.json).
- [Specification validation results](verification/closed_loop/SPEC_CHECKS.md) and [bundle checksums](protocol/closed_loop/bundle.sha256).

This consolidates the two-pass ODR-5 proposal, rather than starting another speculative architecture round. It corrects four load-bearing assumptions: the current checkout has foundation blockers; the trusted rules must **not** be stripped to manufacture a macro-learning problem; hashes do not themselves enforce holdout isolation; and learning a schema is a different claim from making a proof possible under a budget.

## 1. Objective and claim discipline

> On one frozen build, run a supplied-candidate integration experiment, then the same candidate lifecycle with a Machine-generated schema. Independently check every accepted proof, cold-replay it, ablate the candidate, and grade each claim separately. If a prerequisite or induction attempt fails, preserve a precise, reusable failure artifact.

A **candidate schema is an untrusted proof macro/search aid, never a new axiom**. Its every use must expand into the original trusted inference steps. Teaching means submitting a plan candidate, not authorizing its conclusion as mathematical truth.

Predeclare these independent verdicts:

| Field | PASS means | Does not establish |
|---|---|---|
| `integration_demonstration` | Fixture-supplied macro enters supported pilot ingress, is checked and session-admitted, yields checked proofs, survives cold replay, and obeys controls | Machine discovery |
| `auto_schema_induction` | The frozen Machine generates a generalized macro from its own training traces, seals it before holdout access, and uses it in checked held-out proofs | Globally novel mathematics or universal induction soundness |
| `bounded_search_gain` | On at least three preregistered positives, ordinary search misses within the sealed scheduler budget while candidate treatment succeeds; ablation reproduces the misses | Wall-clock speedup, lower total computation, or unprovability without the macro |
| `novelty` | Always `UNASSESSED` in this sprint | A novelty claim requires a separate research review |

**Full one-day target:** all three experimental verdicts PASS, the regression gate passes, and the red team has no unexplained blocker. Each weaker verdict remains reportable under its own name. External teaching can satisfy integration, **never** induction. An Arena worker authoring a candidate at evaluation time is `EXTERNAL_AGENT`, not `MACHINE`.

The minimum useful outcomes form a ladder:

- **M0:** exact source/environment/baseline and a classified blocker.
- **M1:** an ordinary bounded search emits a concrete residual and dependency request.
- **M2:** a submitted macro receives a checked, scoped admission decision.
- **M3:** treatment produces proofs accepted by both checkers.
- **M4:** candidate lifecycle survives cold replay; mutation, scope, and ablation controls pass. Report this as integration only when the candidate was supplied.
- **M5:** repeat M2–M4 with Machine-induced candidates and sealed held-out cases.
- **M6:** establish the paired budget contrast required for `bounded_search_gain`.

M5 can pass without M6. That is honestly bounded schema generalization, **not** a closed search gap. No partial milestone may inherit the full target's label.

## 2. What the actual checkout establishes

The detailed evidence is in the baseline report. These are the planning premises, not promises:

| Observation | Evidence/status | Consequence |
|---|---|---|
| Runtime and planner exist | `runtime.py:MachineRuntime.prove/evaluate`; `planner.py:PlannerRun` | Reuse these layers; do not invent an existing session API |
| Manual schema storage/replay exists | `schemata.py:StoreDerivationSchema/LookupDerivationSchema`; `search/engine.py:SearchBFS._cached_solution` | A replay seam exists; **automatic induction is new work** |
| Explicit bounded search works on a small two-step case | `search.SearchBurst` diagnostic succeeded | Use this seam for the pilot; it is **not** exported as `machine.SearchBurst` |
| Five focused probes pass | Binding consistency, generic edge/character/rule shape, repeated-binding derivation replay | Preserve them; they do not establish end-to-end persistence |
| Cold proof restoration fails in the diagnostic | Saved proof readable before save; after fresh-process activation both derivation entries lack constructors | **F1 is the first repair hypothesis/package** |
| Dynamic registry root is serialized by name | Snapshot root record is `{"id": 1, "name": "AllConstructors"}`; `_record_for` scans every namespace alias | Investigate state aliasing versus stable singleton naming, not the obsolete “Char symbols are never written” claim |
| Full suite is not characterized | `main test` hit a 180-second diagnostic bound after pack loading, without a terminal report | Full-suite baseline remains UNKNOWN; F2 must resolve it before release |
| Ordinary scalar `prove` starts a multi-mode subprocess comparison | Five search workers launched; bounded diagnostics did not terminate | Do not use this as the pilot's unbounded control path or reuse its old result directories |
| No `session.py`, `wire.py`, teaching/admission/research-loop modules | Absent from this tree | Those are deliverables, not existing prerequisites |
| `hyge.py` and `session.txt` form another prototype | String-term rewriting and a taught session, separate from the hypergraph runtime | Do not silently substitute that prototype for the Machine being tested |
| September 12 integration claim | No corresponding tracked evidence found in this base | Unverified; do not use it to pass a gate |

The exploratory environment was Linux/Python 3.11.2 with isolated `gmpy2 2.3.0`/`PyYAML 6.0.3`. The repository environment is Windows/Conda/Python 3.12.13. **These diagnostics are not release verification in the approved target environment.** The August plan's Gates A–D remain load-bearing. No broad curriculum, promotion, language, or distribution program is authorized here.

## 3. Engineering and execution constraints

Read [the repository's August plan](10August2026%20--%20updated%20plan%20by%20sol.md), especially its non-negotiable constraints. For this package:

1. Never edit `core.py`, monkeypatch, add target-specific solver branches, or modify a pack to insert the learned answer.
2. New/revised Machine paths use `Atom`, `Edge`, `Pair`, `EmptyList`, constructor records, and machine truth/failure terms. No Python lists/dicts/bools as machine state; no `isinstance`, `hasattr`, `type`, `__class__`, or `__new__`; no new runtime helper functions or module-global data (including immutable convenience tables and mutable caches).
3. Host CLI, JSON manifests, hashes, and external test bookkeeping are an **I/O boundary**, not an alternative solver. They cannot perform induction, matching, rule application, or mathematical acceptance for the Machine. No new runtime-global vocabulary is required: §5 supplies a record encoding using existing labels and explicit state.
4. No LLM, embedding, network service, or human selection at runtime. All external candidate and training inputs are named before launch.
5. Do not redesign `main.py`, search comparison, persistence, or the planner. A bounded pilot entry point is allowed; it must not replace parallel root-wave search with a serial fallback in the normal program.
6. One active runtime per process. Use fresh processes between experimental legs; namespace synchronization makes threaded/interleaved runtimes unsafe.
7. Runtime verification for release uses the operator-approved environment. Do not discover or activate a different interpreter silently. Record any separately authorized diagnostic environment explicitly.
8. Work only on the session branch. No worker branches, branch switches, or simultaneous git writes. Workers submit base-addressed patches from isolated **non-git** copies; INT alone applies and, when publication is authorized, commits/pushes to `arena/01a0f75a-cat-theo-machine`.
9. A release measurement addresses an exact committed source SHA/tree and a clean semantic tree. No code changes during an experiment. Tags are not required by this session; use immutable SHAs and a content-addressed release label.
10. Keep generated snapshots, corpora, and large logs outside Git, e.g. `.cache/closed_loop/<experiment-id>/`. Archive durable evidence to approved storage; retain small receipts, manifests, and reproduction commands in Git. No overwriting existing snapshots or `.bad` diagnostics.

These constraints apply to both selected and rejected worker attempts. Existing violations are not permission to copy them into new touched Machine paths.

## 4. CL0: an executable GO / FOUNDATION / STOP gate

CL0 is a decision procedure, not a request for the human to reinterpret results. Record each probe's command, deadline, semantic verdict, exit status, source SHA, and artifact digest.

### GO requires

- The approved environment is usable; active-source imports and the relevant focused regressions are reproducible.
- An ordinary, bounded primitive-rule search produces a nontrivial trace for the chosen family without a candidate, cache, or externally supplied plan.
- Its actual saved terms, derivation constructors, rule semantics, and shared identities survive fresh-process load and replay, with no fallback constructor repair.
- The full existing test inventory/result set is complete and identified. Known unrelated failures may be pinned; pilot-critical failures may not be waived.
- An eligible corpus can be generated, candidate-copy/fixture leakage can be excluded, and the bounded application seam is identified. **The new induction/admission implementation need not already exist.**
- Final dual checking, mutation controls, and cold replay fit the remaining window.

### Predeclared non-GO paths

- **`FOUNDATION_REQUIRED`:** dispatch F1 for demonstrated persistence failure and F2 for incomplete/incorrect baseline measurement. They can work in parallel. Re-probe once through CL0R by T+3h. If prerequisites still fail or too little time remains, freeze `claim_profile=FOUNDATION_ONLY`; experimental fields are BLOCKED and the rest of the day hardens the first blocker and its regression artifact.
- **`STOP_ENVIRONMENT`:** approved environment unavailable. Produce M0; do not call Linux smoke tests target release evidence.
- **`STOP_NO_CORPUS`:** neither the existing-rule family nor the predeclared synthetic family can generate valid Machine traces.
- **`STOP_NOT_FEASIBLE`:** verification does not fit. Preserve the exact blocker, not a vague “agent failed.”

A non-needed F1/F2 gets a probe-backed `NOT_NEEDED` receipt; it is not an implicit waiver. CL0R may change dependencies and ownership **before feature dispatch**. Publish a versioned plan delta. A refuted assumption can change the critical path, not merely a filename.

Contract drafts and adversarial vector design may proceed during preflight. Later-gate Machine implementation waits for GO. No re-scope after outcomes may relabel integration as induction, alter budgets, or erase an unsuccessful preregistered attempt.

## 5. Contracts: machine terms, not new host dataclasses

The seven logical record families below are new contracts, **not existing constructors**. CL1 freezes their implementation in `closed_loop/terms.py`. Do not import `main.py` from contract or worker modules.

Use existing primitive vocabulary, with no new runtime-global tags:

```text
Record(kind, fields) = Pair(PairLabel, Pair(version, Pair(kind, fields)))
version             = machine natural 1
fields              = a proper Pair/EmptyList chain with exact arity
kind                = a machine natural from the table below
```

Operation classes return machine terms through `Edge.__call__`. IDs/digests are machine character chains at ingress/egress. Host JSON is decoded once into terms; it is not passed to the solver. Machine `true/false` uses the existing singleton truth values. Unknown version/kind/arity fails closed. CL1 supplies constructor/accessor examples and read-only stubs that return a typed `BLOCKED`, never fabricated success.

| Kind | Logical record and ordered fields |
|---:|---|
| 0 | `Goal(experiment_id, goal_id, start, goal, trusted_rules_digest, budget, task_digest)` |
| 1 | `Residual(goal_id, terminal_class, last_job, remaining_budget, unmatched_goal, provenance)` |
| 2 | `DependencyRequest(request_id, goal_id, request_kind, missing_shape, residual, scope)` |
| 3 | `Candidate(candidate_id, source_kind, start_pattern, goal_pattern, plan, role_bindings, trace_ids, scope)` |
| 4 | `Admission(candidate_digest, verdict, training_checks, development_checks, checker_receipts, scope)` |
| 5 | `ProofReceipt(goal_id, candidate_digest, expanded_derivation, checker_A, checker_B, resource_counters, provenance)` |
| 6 | `Event(sequence, prior_digest, state_from, state_to, input_digest, output_digest, actor)` |
| 7 | `ExperimentState(experiment_id, phase, candidate_store, admissions, residuals, receipts, events)` |
| 8 | `ExperimentReceipt(experiment_id, source_sha, contract_digest, corpus_digest, candidate_receipts, leg_receipts, regression_receipt)` |
| 9 | `Failure(task_id, stage, reason, evidence_digest, retry_precondition)` |

Additional stable contracts:

- **Variable:** existing `Pair(VarTag, Pair(name_atom, EmptyList))`. Repeated occurrences share one role. Generalization must preserve equality constraints; conclusion roles must be premise/start-bound.
- **Trusted rules:** `proof.Rule`/`MultiRule`; unwrap `CompiledRule` through its declared accessor. The action's rule must match a member of the sealed trusted rule table by canonical structure, not a proof-supplied label or success flag.
- **Plan/action:** existing `TheoremAction(rule, bindings)`; the pilot admits only this declared sublanguage. Rewrite actions, opaque cached derivations, cycles, and unknown actions are rejected unless a prospectively amended checker contract supports them.
- **Expanded proof:** existing `Step`/`Derivation` atoms and the accompanying constructor registry. Checkers use `StepCurrent`, `StepAction`, `StepNext`, and `DerivationSteps` or independent equivalent destructors, not replay/search code.
- **Quarantined evaluation:** `ExpandCandidate(goal, candidate, trusted_rules, budget, registry) -> untrusted expanded derivation | Failure`. It cannot activate the candidate, mark a session goal proved, or mutate live/trusted knowledge. Admission evaluates these isolated training/development expansions with both checkers. This removes the apparent admission-requires-application/application-requires-admission cycle.
- **Live application:** `ApplyCandidate(goal, candidate, admission, trusted_rules, budget, registry) -> ProofReceipt | Failure`, with a registry returned through the existing machine result convention when construction changes it. It requires admission, uses the same expander, and independently re-checks the resulting proof.
- **Checking:** `CheckExpandedProof(goal, derivation, trusted_rules, registry, scope) -> machine verdict + offending step/reason`.
- **Persistence:** `SaveExperiment(graph, ExperimentState)`, followed by fresh-process `LoadExperiment` and re-checking. Use `SnapshotCodec.capture(..., extra_roots=...)` at the host I/O boundary; ordinary `SnapshotCodec.save` does **not** currently forward extra roots. No need to add every experiment field to `context.py`.

Canonical hashes omit UUIDs, wall times, and allocation order. Give opaque fixture atoms stable corpus-local names, alpha-normalize roles by first occurrence, encode declared constructor labels, and preserve aliasing/equality. Do not demand byte-identical snapshots across runs; require identical normalized verdicts/proof shapes and separately hash each actual artifact.

## 6. Frozen experiment and trust boundary

### 6.1 Predeclared task families

CL0 tries these in order, without evaluating a learned candidate:

1. **Existing-rule pilot:** `packs/order-sign.pack.yaml` primitives `positive_implies_nonnegative` and `nonnegative_argument_yields_real_sqrt`:

   ```text
   Positive(t) -> NonNegative(t) -> IsReal(Sqrt(t))
   ```

   Those source rules already exist and that pack has no stored schemata. The inspected bounded diagnostic reproduced the two-step path. CL0 must verify the generated candidate pattern is absent from all enabled trusted schemas/caches and characterize supported fact-board variants. Synthetic term assignments are still reported as synthetic tasks over existing-pack rules.

2. **Synthetic relational calculus, if family 1 cannot meet the frozen structural-test contract:** declare and seal primitive axioms `R(x,y) & R(y,z) -> T(x,z)` and `T(x,z) -> S(x,z)` as **fixture axioms**. Train through ordinary search over one frozen primitive set. Test the mechanism on at least three separately relabeled calculus instances, regenerating from each instance's own training traces; do not demand that a macro tied to one trusted-rule digest apply under a different digest. This establishes only bounded generalization in that explicitly declared calculus, not new mathematics in the repository.

Record `rule_origin=EXISTING_PACK|FIXTURE_AXIOMS` and `corpus_provenance=MACHINE_GENERATED_SYNTHETIC`. **Never train with a bridge axiom and then remove it while pretending its macro expansion is justified.** Only candidate stores and caches are absent/ablated. Trusted primitive rules are identical in every leg.

**Checker semantics, frozen before either checker is dispatched:** family 1 is whole-term unary rewriting in a free constructor algebra, justified only by the two sealed rules. `Positive(t)` is an assumption/term, not a host numerical test. Family 2 uses finite sets of positive ground facts, conjunction of all rule premises under one consistent substitution, and addition of the instantiated conclusion; the goal is an atomic fact query, not the runtime's separate consumptive knowledge-board rewrite mode. Duplicates are idempotent; input order is irrelevant; distinct opaque constants are not equated without a declared alias. No implicit arithmetic or unrecorded normalization is allowed. Each step must have exactly the state transition specified by these semantics. If the relevant native path disagrees, CL0 must block or prospectively re-scope the family, not let two checkers invent different calculi. Rule-local variables and schema roles have explicit per-action mappings; matching variable-name text across different rules is not a valid substitute for those mappings.

Minimum split, sealed before feature workers receive data:

- six successful training traces, spanning at least three distinct assignments and a common fragment of at least two trusted steps;
- five unseen positives, including new assignments and a supported structural variation;
- five invalid-application near misses: missing premise/start shape, inconsistent repeated role/join, wrong conclusion/goal, unbound role, and malformed action;
- positive robustness variants: reordered facts, duplicates, and unrelated distractors. **Reordering/distractors are not negative examples** unless they remove required information;
- a public development split for fixture integration, separate from induction holdout;
- two sealed reserve evaluation splits for predeclared repaired-build reruns.

If a family cannot support a category, use a separately labeled contract vector for that category, not an unacknowledged exclusion from the release matrix. This is a small pilot, not implementation of the whole graph curriculum.

### 6.2 Budget v1 (freeze with the corpus)

```text
training search dispatch steps per task: 256
held-out/control/treatment dispatch steps per task: 1
maximum expanded primitive proof steps: 16
maximum expansion substitution/matching attempts: 256
maximum task term nodes: 4096
maximum facts per task: 12
maximum emitted candidates per induction mechanism: 1
per-task wall-clock kill bound: 120 seconds
per-induction-process wall-clock kill bound: 300 seconds
```

The deliberately tight **scheduler** budget makes macro reuse observable; it is not a total-compute metric. One macro attempt consumes one dispatch step, but its primitive replay work and matching attempts must also be bounded and reported. Baseline and treatment have identical proof/matching/wall ceilings and rule sets. Checkers' cost and offline training/induction cost are reported separately. Never claim computational speedup from a dispatch-step contrast alone.

CL0 may diagnose that v1 cannot run; it may not tune the budget after candidate results. A different budget requires a prospectively frozen experiment version and is reported as a different attempt. A timeout is `RESOURCE_EXHAUSTED`, not evidence of missing mathematics or unsatisfiability.

### 6.3 Isolation and seals

The evaluator—not the learner—owns split generation, storage, and the seed commitment. Freeze its selection algorithm, budget, corpus digests, and opaque-seed hash at CL1. Store private values only in evaluator-controlled storage outside Git; `protocol/closed_loop/fixtures/` contains public generation metadata/commitments, never hidden inputs. CL1 supplies native fixture construction; the evidence role performs the small freeze/capability bootstrap during CL1, before its complete CL7 harness exists. This bootstrap is not an acceptance dependency on a future completed harness. Do not let INT pick a favorable seed after seeing patches.

A digest proves content identity, **not chronology, secrecy, or independence**. Enforce the ordering with capabilities:

1. Generator process receives only training tasks/traces and trusted semantics. It cannot read the fixture candidate, holdout, reserve splits, evaluator logs, or another generator's output.
2. Restrict filesystem access with a real isolated runner/read-only input tree and restrict network access. A subdirectory plus an instruction “don't read it” is not strong isolation. Log allowed inputs and denied-access probes. If strong isolation is unavailable, report `seal_integrity=UNVERIFIED`; induction cannot PASS.
3. Each of CL2A/B emits at most one candidate, sealed by the evaluator before holdout is made available to application processes. Seal **both attempts**, including an empty/failed candidate receipt, before either sees holdout results.
4. No repair/refinement of a candidate after evaluation. All attempts are graded; no per-case cherry-picking between candidates. The predeclared aggregation is “either whole candidate passes every induction conjunct.”
5. Checker B receives formal contracts/vectors and the frozen kernel, not Checker A's implementation/results before its first report. Use separate non-git source copies and separate contexts. The same applies to CL2A/B.

The fixture integration pass cannot leak its candidate or M5 holdout into the learner. Use its separate development inputs. Similar algorithm choices are not statistically independent just because workers are separate; report mechanisms and do not infer independence probabilities from two attempts.

### 6.4 Four legs, twice, one build

For each candidate provenance, using disjoint case instances where required:

1. **Control:** start from a clean fixture checkpoint with empty candidate store, derivation/schema caches, search memo/comparison evidence, and no inherited worker results. Run ordinary bounded search. Emit status, concrete frontier/partial trace, unmatched goal, and dependency request. Classify request as `SEARCH_GUIDANCE` when primitive rules are present; do not invent a missing axiom.
2. **Treatment:** submit the candidate through pilot ingress, bind/validate, evaluate on training/development inputs, obtain session admission, and retry. Independently expand/check every use. Seal the candidate **before** held-out admission/application checks; holdout may reject a candidate, never improve it.
3. **Replay:** save actual experiment roots, terminate all processes, cold-load in a new interpreter, re-establish scope and constructors, then verify expanded proofs with both checkers. Replay is deterministic verification, not proof search and not trusting stored checker flags.
4. **Ablation:** load the original clean control checkpoint, omit only the candidate/admission overlay, and clear candidate-derived caches/memos/results. Repeat the same inputs/budgets. No candidate-use event may remain. For the gain claim, at least three paired misses must return. A baseline proof may exist outside that budget.

Run the final frozen build three times and compare normalized verdict vectors. A semantic repair after exposure invalidates that measurement: use the next presealed reserve split, regenerate/seal candidates on the new SHA, and retain the previous failure. At most two reserve reruns; no moving goalposts.

## 7. Runtime protocol and safety invariants

CL8 implements a bounded state machine, not an informal “agent, keep trying” loop:

```text
received -> control-complete -> residual-recorded -> candidate-submitted
 -> candidate-sealed -> evaluated -> admitted -> applied -> dual-checked
 -> checkpointed -> cold-checked -> ablated -> terminal
```

Branch to a typed terminal failure on malformed ingress, rejected candidate, scope mismatch, checker disagreement, resource exhaustion, persistence failure, or safety refusal. Every transition validates the prior state, experiment ID, input digest, and event sequence. Duplicate deliveries are idempotent. No admission means no application; a stored success flag never enables a transition.

“Safety” here is a concrete protocol floor: trusted stores/packs stay unchanged; session scope is enforced; resources and file/network capabilities are bounded; no interactive decisions or external solver; candidate failure cannot trigger durable promotion. Do not claim an existing Fable safety subsystem was verified.

Use an explicit autonomous policy at every possible interaction boundary; close stdin and prohibit interactive readers in the pilot call graph. A prompt attempt produces a machine `INTERVENTION_ATTEMPT` and terminates; EOF must not silently authorize continuation. Source/call-path audit and deny-access tests back this invariant. A hook alone does not prove all possible covert interaction absent.

Admission authorizes **session use**, not truth or promotion. Bind its digest to candidate, source SHA, trusted rules, budget, experiment ID, and scope. Check every held-out expansion before it counts as a proof. Session restores retain that same scope; a foreign experiment or stale SHA must reject. Trusted `all_rules`, pack bytes, and trusted `derivation_schemata` must remain unchanged. A failed induction produces `Failure` plus a persisted `DependencyRequest` naming its exact stage; it cannot fabricate the omitted rule.

## 8. Task DAG, ownership, and real parallelism

The JSON manifest contains the complete DAG. `requires_to_start` means execution prerequisites; `needs_real_inputs_for_acceptance` is not a reason to idle until integration. Use CL1 stubs and sealed vectors for earlier work.

```text
CL0 initial probes
  -> [F1 persistence localization/repair || F2 baseline measurement]
  -> CL0R gate
  -> [CL1 contract/split freeze || CLT acceptance vectors]
  -> contract-ready barrier
     +-- CL2A || CL2B  independent induction
     +-- CL3A || CL3B  independent checkers
     +-- CL4          expansion/application
     +-- CL5          ingress/admission/residual
     +-- CL6          experiment persistence
     +-- CL7          evaluator/sealer/harness/grader
     +-- CL8          coordinator against stubs
     +-- CL9          continuous red team
  -> CL10 integration candidate
  -> CL9 final audit -> REL final frozen experiment/report
```

Independent checkers and generators have explicit blind contexts. Otherwise write permissions, not shared good intentions, prevent merge conflicts.

**INT-only existing semantic surfaces:** `constructors.py`, `labels.py`, `context.py`, `graph.py`, `machine.py`, `runtime.py`, `proof.py`, `schemata.py`, `search/`, `persistence.py`, `main.py`, `testsuite.py`. Changes here need a symbol/line-specific proposal and failing probe. Most pilot code belongs in **new** task-owned files below; these paths do not yet exist. `core.py`, existing packs, and existing snapshots are forbidden surfaces.

| Task | Exclusive patch surface | Acceptance IDs |
|---|---|---|
| CL0/CL0R | `protocol/closed_loop/runs/` gate/environment/baseline receipts | B01–B06 |
| F1 | `validation/closed_loop/foundation/persistence/`; proposal for INT's `persistence.py` edit | B03, B04, N01 |
| F2 | `validation/closed_loop/foundation/baseline/`; no default-suite deletion | B01, B02, B05, B06 |
| CL1 | `closed_loop/__init__.py`, `closed_loop/terms.py`, `closed_loop/fixtures.py` (fixture construction only), `protocol/closed_loop/contracts/`, `protocol/closed_loop/fixtures/` (public metadata only) | C01–C03 |
| CLT | `validation/closed_loop/acceptance/` sealed input/output vectors and probe definitions | C01–C03, H01 |
| CL2A | `closed_loop/induction_a.py`, `validation/closed_loop/unit/induction_a/` | I01–I04 |
| CL2B | `closed_loop/induction_b.py`, `validation/closed_loop/unit/induction_b/` | I01–I04 |
| CL3A | `closed_loop/checker_a.py`, `validation/closed_loop/unit/checker_a/` | V01–V05 |
| CL3B | `closed_loop/checker_b.py`, `validation/closed_loop/unit/checker_b/` | V01–V05 |
| CL4 | `closed_loop/application.py`, `validation/closed_loop/unit/application/` | V01–V05, X01, X02 |
| CL5 | `closed_loop/admission.py`, `closed_loop/residual.py`, corresponding unit directories | A01–A03, R01–R03 |
| CL6 | `closed_loop/checkpoint.py`, `validation/closed_loop/unit/checkpoint/` | P01–P03 |
| CL7 | `closed_loop/harness.py`, `protocol/closed_loop/receipt-schema.json`, `validation/closed_loop/unit/harness/` | H01–H04 |
| CL8 | `closed_loop/coordinator.py`, `validation/closed_loop/unit/coordinator/` | S01–S03 |
| CL9 | `validation/closed_loop/red_team/`, signed audit receipts | N01, H02–H04, V02–V05, A02, P02, S02 |
| CL10/REL | INT-only shared proposals/wiring, candidate/release receipts | all required gates |

### Dispatch cards

Every card inherits §§3–7 and its ownership row; workers do not renegotiate the experiment with the human.

**CL0 / CL0R — Preflight and re-gate.** INT identifies exact source/environment, safe entry points, focused/full test results, clean checkpoint and rule/corpus eligibility. Do not count legacy `hyge` imports or a completion print as a passed assertion. Initial probe window ≤60 minutes; re-gate by T+3h. Output GO/FOUNDATION/STOP with failing evidence and a versioned DAG delta when needed.

**F1 — Preserve state instead of namespace aliases.** Persistence worker localizes the observed missing constructors, starting at `SnapshotCodec._record_for` and `save_runtime`. Distinguish fixed vocabulary singletons from mutable roots such as `AllConstructors`. Submit the smallest normal-constructor-path repair to INT, with a regression that demonstrates the failure before and restored semantic readers/replay afterwards. Do not merely suppress the assertion, remove the registry from the namespace, re-register lost constructors, or rewrite concrete-edge persistence globally. Generic `Edge` restoration is acceptable for supported records **only if their declared semantic accessors work**; Python subclass identity is not this pilot's criterion.

**F2 — Complete and honestly grade the baseline.** Evidence worker inventories actual registered tests and handles eager work performed by `install_default_tests`; implements a bounded host result adapter in its owned directory. `main.py test` does not currently make failed tests a failing exit code. Require per-case verdicts and coverage, not grep of old logs or zero exit. If sharding is needed, prove the union covers the inventory and preserve any order-dependent group; no global monkeypatch/serial search substitution. Escalate an unresolved resource/runner issue to FOUNDATION/BLOCKED, not “all green.” Pin the existing syntax failure in the Windows-only scratch utility separately from active source.

**CL1 — Freeze terms, semantics, splits, budget, and stubs.** Contract steward implements exact records, machine-native examples and fail-closed stubs; seals family, primitives, candidate absence evidence, split protocol and budget. It supplies a **fixture** plan only for the integration development pass, inaccessible to induction processes. Stable terms, not a final storage redesign, are the concurrency barrier.

**CLT — Harness-first acceptance vectors.** Test steward writes each substantive vector/oracle before its implementer is dispatched. Feature probes must demonstrably fail or return typed BLOCKED on the unimplemented baseline; negative probes may already pass. Unit workers may add local tests but cannot weaken sealed acceptance expectations. Maintain vector-to-task mapping and test inventory.

**CL2A — Trace anti-unification.** Build Machine-native shared-fragment detection and least/general bounded role generalization over training trace pairs. Generalize varying assignments, retain fixed rule identities and repeated-role constraints, emit one deterministic candidate and source-trace provenance. No plan pasted from the fixture, runtime constant/seed branches, or holdout read.

**CL2B — Independent trace-template enumeration.** In a blind source/context copy, enumerate bounded action-shape templates from training traces, with a different mechanism than A. Generalize roles supported across traces, deterministically rank by training support, then seal one candidate or a typed failure. It must not obtain a missing axiom from the evaluator or infer truth from a few successful examples.

**CL3A / CL3B — Independent proof checkers.** Verify every expanded step: trusted rule membership, exact premise witnesses, bound substitutions and repeated roles, continuity, next-state meaning, declared constructor shape, scope, and final goal. Both must pass for a proof to count. Sharing elementary Atom/Pair/registry destructors and formal semantics is allowed; sharing matching/substitution/rule-replay implementations is not. Neither calls `Prove`, `Search`, `BuildDerivation`, `InstantiateDerivation`, `ApplyCandidate`, or the inducer as an oracle. Stored receipts are evidence to re-evaluate, not authority.

**CL4 — Expander and budgeted application.** Own all candidate expansion/application code, independently of induction. Validate closed bindings and scope, translate the macro into primitive actions, produce an ordinary expanded derivation, and account for internal replay work. Existing `BuildDerivation` can be a construction aid, **not** the independent checker. Reject a corrupted expansion; checkers must also detect a malicious expander's corruption. Candidate stores remain separate from trusted schema stores. Implement an explicit pilot overlay around bounded `SearchJob`/`SearchState`/`SearchBurst`, not a change to normal comparison policy.

**CL5 — Ingress, admission, useful residuals.** Bind canonical machine candidates, reject malformed/unbound/conflicting roles, check training/development evidence and dual checker receipts, and issue session-only admission. Residuals distinguish parse error, no applicable rule, inconsistent binding, budget exhaustion, checker failure and safety refusal. Requests include the goal/frontier/failed obligation and source evidence; with existing primitives request search guidance, not an invented missing mathematical axiom. Candidate admission cannot modify packs or trusted rules.

**CL6 — Experiment roots and real cold replay.** Save the actual candidate, scope/admission, goal, residual, events, derivation and registry through existing codec extra roots plus the graph. Terminate the saving process; fresh-load through the real activation path; verify semantic accessors/aliasing and invoke both checker processes. Check scope remains untrusted/session-only, reject wrong experiment/SHA, test interrupted atomic writes and preserve the prior valid checkpoint. No constructor-registration fallback.

**CL7 — Sealer, evaluator, one-command harness, grader.** Own holdout capabilities, ordering receipts, fixed-budget comparisons, clean-leg process lifecycle, artifact hashes and scalar verdict calculation. Evaluate **both** sealed generator outputs, not the best candidate per case. Exit nonzero unless the requested claim's complete conjunction passes; failure/NOT_RUN/UNKNOWN cannot pass. Never perform the Machine's induction or proof semantics in host Python. A read-only one-page summary links all raw evidence.

**CL8 — Coordinator.** Implement the state machine against stubs immediately; later replace stubs through declared interfaces. Cover success, every failure edge, duplicate delivery, stale scope, refusal and intervention. On induction failure persist a specific dependency/failure record for the next session, without asking the operator to choose a fix.

**CL9 — Continuous independent red team.** Start vector/call-path attacks at contract freeze. Attack fixture/candidate/holdout leakage, stale caches, foreign rule injection, derivation discontinuity, forged admission/receipt, mutated bindings, wrong experiment/SHA, prompt fallback, untrusted promotion and expander corruption. Rerun the complete final release candidate in an isolated process/storage root. Each attack returns expected/observed/artifact/blocker; unexplained acceptance blocks release.

**CL10 — Integrate exact patches.** INT accepts only owned, base-addressed patches with executable evidence. Merge contract → checker implementations → application/residual/admission → checkpoint → harness/coordinator, with focused and changed-surface regression gates at each seam. Prepare one clean candidate SHA; let the red team measure it. Do not run the full suite after every independent module merge if that serializes hours: run focused gates per merge and one complete baseline-comparable suite per assembled candidate.

**REL — Frozen final measurement.** Freeze release SHA; run three repetitions, both provenance profiles, all controls, full-suite delta and final audit. Publish manifest and one-page verdict. A later code change invalidates this measurement, even if only “a tiny fix.”

## 9. Acceptance inventory (independently judged)

Every probe records inputs, expected/observed machine terms, source SHA, elapsed/resource bounds and evidence digest. These are contracts for CLT to implement, not claims that these new probes already exist.

| IDs | Required assertion/vector |
|---|---|
| B01 | Correct environment/SHA/tree; active imports reproduce; known scratch-source failures named |
| B02 | All existing registered cases covered; complete verdict inventory; a known failing case makes the adapter nonzero |
| B03 | Non-singleton characters, loaded rule variables, shared children, and declared term labels survive snapshot round trip |
| B04 | Bounded two-step trace readable before save; fresh-process load preserves both `Step` and `Derivation` constructors and replay; dynamic root is not replaced by an empty namespace alias |
| B05 | Pilot uses bounded supported entry point; neither worker artifacts nor auto multi-mode comparison are inherited |
| B06 | Original approved baseline repeatable; unresolved timeout/exception/unknown coverage cannot satisfy the release gate |
| C01–C03 | Exact record round trip and version/arity rejection; consistent repeated-role matching; split/trusted-rule/candidate absence digests fixed |
| I01 | Six Machine-generated traces produce a candidate with a ≥2-step fragment, ≥3 assignments, generalized bound role and source IDs |
| I02 | Generator cannot read fixture candidate, holdout/reserves, or another generator; all seals precede evaluator exposure |
| I03 | Five unseen positives verified by both checkers; the same candidate is used in ≥3; not five exact stored training proofs |
| I04 | Near misses reject; constant-renaming and supported structural variants do not trigger source-specific branches; all attempted candidates reported |
| V01 | Valid expansion accepted independently by both checkers; exact step continuity and final goal enforced |
| V02 | Mutated premise, conclusion, action rule, repeated-role binding, intermediate state, and foreign goal each rejected |
| V03 | A rule absent from the sealed trusted table, even if embedded in a plausible action/registry, rejected |
| V04 | Malformed/unbound/unknown/cyclic/over-limit proof rejected; error is not acceptance |
| V05 | Checkers never call search, replay builders, or induction, and disagreement blocks release |
| X01–X02 | Corrupt expander output rejected by both checkers; dispatch and primitive replay/matching ceilings enforced and reported |
| A01–A03 | Correct candidate session-admitted after checks; wrong scope/digest/SHA or absent/rejected admission cannot activate; no durable trusted-store change |
| R01–R03 | Concrete bounded residual/request persists; parse/binding/no-rule/resource/safety classes are distinct; reordering/distractor variants retain valid result class |
| P01–P03 | Fresh-process dual replay matches normalized verdicts; scope/aliasing/constructor identity preserved; interrupted write retains the previous checkpoint or produces an explicit recovery failure |
| H01 | One command grades both profiles, checks completeness and hashes, and fails on a deliberately missing/corrupt receipt |
| H02 | Three clean repetitions match normalized verdict vectors, not timestamps or UUIDs |
| H03 | Ablation has no candidate-derived state/use; identical primitives/budget; ≥3 paired failures return for the gain claim |
| H04 | Code, fixture, scope, or receipt mismatch; source leakage; secret read; or unapproved post-seal refinement blocks the appropriate claim |
| S01–S03 | Stubbed full success and every terminal branch; duplicate/stale delivery idempotent/rejected; prompt/refusal cannot continue to success |
| N01 | No core edit, forbidden touched-path construct, target-specific runtime branch, pack solution, normal-search regression, or fallback constructor repair |

A negative input is a test of **invalid macro application**, not a declaration that its goal is impossible in every logic. Declare the finite positive-rule semantics and derivability oracle for synthetic near misses. Do not use bounded search failure as the oracle for mathematical invalidity.

## 10. Integration, reports, and recovery without a human coordinator

### Patch protocol

On this fixed session branch, INT exports the exact base tree into isolated non-git worker directories. Worker patches are relative to that base; they never run git in the shared checkout. INT is the only writer of shared files and git history. Test-only outputs from a failed worker may be retained without merging its solver.

Each submission supplies:

```text
TASK / ATTEMPT / STATUS (READY | BLOCKED | FAILED)
BASE_SHA / CONTRACT_DIGEST / PATCH_SHA256 / SOURCE_TREE_DIGEST
FILES_TOUCHED / SHARED_CHANGE_REQUESTS
TEST_COMMANDS / EXIT_STATUSES / SEMANTIC_VERDICTS / ARTIFACT_DIGESTS
KNOWN_FAILURES / FAILURE_MODES / REAL_INPUTS_STILL_NEEDED
```

INT verifies path ownership and base/contract version automatically against `tasks.json`. A green workspace or prose report is not a mergeable artifact. When publication is authorized, publish accepted checkpoints to the fixed branch; do not require other branches or assume automatic pushes have already happened.

### Recovery table

| Failure | Deterministic response |
|---|---|
| Inducer fails | Grade and retain its typed failure; use the other **whole** preregistered attempt, never construct a replacement from holdout answers |
| Both inducers fail | Keep valid integration receipts; induction FAIL/BLOCKED with stage/request; do not change its label |
| Checker disagreement | Block proof/release; red team localizes against fixed vectors; neither checker is selected away |
| Interface mismatch | Reject patch or INT supplies a small adapter; versioned change request includes consumer and failing vector; no silent contract edits |
| Shared-file conflict | Reject worker shared edits; INT applies one consolidated proposal; workers retest on exact resulting base |
| Foundation fails | Follow CL0/CL0R FOUNDATION path; persist first blocker; do not dispatch later-gate runtime work |
| Full suite incomplete | Regression verdict UNKNOWN/BLOCKED; smaller green smoke tests do not replace it |
| Time/resource exhaustion | Stop at frozen bound; save frontier/phase/failure; do not increase timeouts to conceal lack of progress |
| Semantic repair after holdout | New source SHA/experiment ID, next presealed reserve split, fresh candidate seals; retain prior attempt; budgets/claim labels unchanged |
| Environment reset | Recover accepted source/receipts from immutable published identifiers; regenerate derived data; missing code/artifact means BLOCKED, not reconstruction from prose |

### Kill/block conditions

A release claim is blocked by a missing conjunct, candidate leakage, unverified isolation, untrusted-to-trusted promotion, absent admission, unchecked step, checker search/replay oracle, retained candidate cache under ablation, code mismatch across legs, fallback constructor registration, new baseline failures, interaction during the run, safety refusal retried, or incomplete evidence. A control success specifically blocks `bounded_search_gain` for that pair, **not** the claim that an induced macro generalizes.

## 11. Commands, artifacts, and final grader

**Future interface to be implemented by CL7** (not available in the current checkout):

```bash
# Run from the repository's parent, in the approved environment.
python -m cat_theo_machine.closed_loop.harness preflight --plan cat_theo_machine/protocol/closed_loop/tasks.json --artifact-dir <outside-git-path>
python -m cat_theo_machine.closed_loop.harness run --experiment <sealed-manifest> --profile DUAL_PROFILE --autonomous --artifact-dir <outside-git-path>
python -m cat_theo_machine.closed_loop.harness verify --manifest <completed-artifact-manifest>
```

Follow the actual checkout package name; do not copy the broken legacy `hyge` imports into a portable runner. Existing supported entry point for the original suite is `python main.py test` from the repo, or `python -m cat_theo_machine.main test` from its parent. Its exit status alone is not sufficient grading.

Minimum artifact pack:

```text
source/environment/baseline receipts
contract + split/budget/trusted-rule manifest
training tasks/traces + provenance
fixture candidate + both induction seal/failure receipts
all candidate/admission/rejection receipts
per-case control/treatment/replay/ablation records
expanded proofs + independent checker results
mutation/isolation/scope/autonomy/red-team results
checkpoint/root/constructor manifests
complete regression delta
event log + file SHA-256 manifest
SUMMARY.md (one page) + verdict.json
```

Manifest verification must detect omissions as well as modified bytes. Every verdict references its supporting artifacts; host summary text never impersonates Machine output. Untrusted pickle/worker files are not admitted as external evidence.

Final host receipt (enum values, no missing keys):

```text
claim_profile: DUAL_PROFILE | FOUNDATION_ONLY
integration_demonstration: PASS | FAIL | BLOCKED | NOT_RUN
auto_schema_induction: PASS | FAIL | BLOCKED | NOT_RUN
bounded_search_gain: PASS | FAIL | BLOCKED | NOT_RUN
novelty: UNASSESSED
full_target: PASS | FAIL | BLOCKED
base_sha / release_sha / source_tree / contract_digest
rule_origin / trusted_rules_digest / corpus_provenance
training_digest / holdout_digest / budget_digest
candidate_A_verdict / candidate_B_verdict / candidate_digests
checker_A / checker_B / cold_replay / ablation
seal_integrity / autonomy_audit / negative_controls / mutation_controls
baseline_inventory_digest / baseline_failures / release_failures / regression_verdict
red_team / manifest_digest / highest_milestone / next_dependency_request
```

PASS definitions in §§1, 6 and 9 are conjunctive. UNKNOWN is never PASS. The final summary must name the exact failed stage when a target fails. No novelty adjective or “months in a day” claim is authorized by these fields.

## 12. Critical path, timing, and human actions

Approximate engineering estimates, not a speed guarantee:

```text
CL0/F1/F2/CL0R       0–3h       genuine foundation dependency
CL1 + CLT           1–1.5h     stable contract and holdout/test freeze
parallel packages   3–4h       two inducers, two checkers, expansion, admission,
                               persistence, harness and stubbed coordinator
CL10                1.5–2h    shared seam integration, not per-worker full-suite waits
CL9 + REL           2–3h      frozen audit, three runs, full regression and archive
```

**Actual critical path:** foundation repair/gate → contract/tests → maximum unfinished acceptance dependency (including both checkers, expansion, admission, persistence, harness, coordinator) → integration → final audit/release. Induction can finish later without blocking the **integration** profile. It cannot be omitted from the full target. Do not use a formula that forgets replay, the second checker, or the full regression run.

Preflight, contract/test freeze, and clean final integration/verification are the genuine serial boundaries. Independent implementations, failure-vector design, induction attempts, stubbed coordinator work, and artifact tooling run concurrently. Incrementally feed accepted modules to INT; do not wait for one giant merge.

At T+3h enforce the gate. Reserve the last two hours before the actual deadline for verification/artifact hardening; if M4 is not reached, stop feature building and preserve the highest honest milestone. If “by midnight” is the approved goal, record that UTC deadline at launch and truncate the 16-hour ceiling accordingly—do not schedule sixteen hours when fewer remain today.

The human has three **decision categories**: authorize the profile/environment/deadline and starting SHA; launch/approve dispatch; review the final one-page receipt. This is not a promise of three UI clicks: Arena fan-out/API availability is not assumed. If manual routing is necessary, use the prefilled cards and report envelopes, count launches and human routing time separately, and do not claim the JSON DAG is an implemented orchestration service. INT resolves routine architecture/patch decisions against this contract, logs them, and never delegates runtime rule selection, seed choice, scope waiver, or checker disagreement back to the human.

**Biggest risks to the one-day objective:** the registry repair may uncover further constructor/state loss; the eager full suite may not fit or yield a complete baseline; strong holdout isolation may not be available on the dispatch platform; both induction mechanisms may overfit trace constants or fail to align rule-local bindings; both checkers may share a faulty low-level assumption; and manual agent routing may consume the nominal parallel advantage. The gate, capability audit, blind implementations, mutation controls, bounded attempts, and explicit partial verdicts mitigate these risks—they do not guarantee a one-day result.

**Dispatch first on this checkout:** CL0 plus F1 localization, F2 baseline characterization, and contract/red-team *drafts*. The measured cold-restore failure means feature dispatch is conditional on CL0R, not authorized by the earlier prose specifications. No fan-out or implementation run is claimed to have occurred merely because this spec and DAG now exist.

**Final test:** did the frozen Machine produce a reusable, independently checked schema from its own traces, apply it outside training, retain its untrusted scope and semantic evidence across a real cold restart, and accurately distinguish that achievement from externally supplied knowledge and from bounded search improvement? Every outcome must leave reproducible evidence and, when needed, the next precise task—not an anecdote.
