# CTM-ODR-FINAL — bounded autonomous research-loop task specification

**Repository:** `StrangeTcy/cat_theo_machine`  
**Branch for this specification:** `arena/01a0fe4e-cat-theo-machine`  
**Status:** dispatch specification; not a claim that every referenced component is already present on this branch  
**Timebox:** one day / 16 hours after preflight  
**Primary deliverable:** one frozen-cut experiment producing a reproducible, independently checked, inert research artifact

## 1. Mission

On one reconciled, immutable repository cut, the Machine must attempt to generate a reusable **untrusted proof schema or invariant** from its own successful traces, apply it to withheld tasks, and produce independently checked proofs that survive replay, mutation, and ablation.

This is a bounded autonomy experiment. It is not a claim of AGI, global mathematical novelty, completion of the Machine, or an FLT proof.

The experiment distinguishes three claims:

```text
INTEGRATION_ONLY
    An externally supplied candidate passes ingress, session admission,
    proof use, independent checking, persistence, replay, and ablation.

AUTO_CANDIDATE
    The frozen Machine itself emits the candidate from its own traces,
    the candidate is sealed before holdout exposure, and it passes the
    same checking, replay, mutation, and ablation gates.

RESEARCH_ARTIFACT
    The run produces an inspectable, content-addressed, inert evidence
    graph and report. It does not automatically promote knowledge.
```

An externally supplied candidate can pass the integration milestone but **must never count as autonomous induction**. The candidate is a proof macro/schema, not a new trusted axiom. Every use must expand to steps justified by pre-existing trusted rules.

## 2. Five protocol dimensions

The programme has five tracks. They are parallel development and measurement lanes, not a sequential feature list.

| Track | Meaning | Boundary |
|---|---|---|
| **S** | Self-improvement through contracted relation schemas | Bounded schema/policy induction; no unrestricted self-modification |
| **E** | Explanation substrate | Faithful explanation transfer with held-out cases |
| **F** | FLT programme tooling and audit | Attemptability, checked derivations, residuals, checkpoints, controls, and audit; not a claim of proving FLT |
| **G** | Engel strategies as planner methods | Method payloads, obligation skeletons, episodes, and planner wiring |
| **I** | IMO problems as the held-out exam | Curriculum Pool A and sealed examination Pool B |

G has exactly five permitted v2 planner methods:

```text
Invariance
Extremal
Pigeonhole
Divide
Symmetry
```

`Bijection` and `DoubleCount` are not additional v2 G methods. If they occur in older planner code, CL0 records the drift and INT resolves it before G/I measurement.

### S

S proceeds through adopted macro-laws, relation contracts, and schema mining. An S2 `RelationSchema` requires distinct relation heads, alpha-equivalent dataflow, matching contracts, and at least two distinct source goals. Schemas live outside the fireable `FireAny` rule store and are not automatically admitted.

### E

E uses a held-out explanation-transfer design. C1–C3 are training fixtures, C4 is held out for E1, and C5 is reserved for E4. A passing explanation must identify the actual invariant, representation shift, law name, and source term from the derivation spine in every rendered sentence.

### F

F grades three separate claims:

```text
A1: exact goal is parseable and attemptable
A2: a derivation exists from disclosed trusted leaves and replays
A3: blind target-specific discovery differs from controls
```

The decoy/target experiment must not promote A1 or A2 into A3. If target and decoy produce the same residual class, the discovery reading is withdrawn.

### G and I

G supplies method payloads and obligation skeletons; S owns policy induction. The critical curriculum path is:

```text
G planner wiring → G/I curriculum → I sealed exam
```

I separates training/curriculum Pool A from sealed exam Pool B. Once a Pool B item is released for training, it is retired from future held-out claims.

## 3. Two-pipeline operating model

```text
                         INT preflight / cut N
                                  │
              ┌───────────────────┴───────────────────┐
              │                                       │
              ▼                                       ▼
    ENGINEERING PIPELINE                    MEASUREMENT PIPELINE
    build next cut N+1                       measure frozen cut N
              │                                       │
     S-eng / E-eng / G-eng / F-tools          G/I-op / E-op / F-run /
                                               researcher_v0
              │                                       │
              └───────────────┬───────────────────────┘
                              ▼
                   INT merge → full suite
                              ▼
                       immutable cut N+1
```

Engineers may work concurrently against versioned contracts, stubs, and fixtures. Operators may only measure an immutable tag. INT alone admits shared-interface changes, performs the full integration suite, and publishes the next measurement cut.

Parallel-safe work includes S/E/G/F engineering, independent checkers, curriculum preparation, F control tooling, and researcher experiments in separate sandboxes. Serialized work includes cut creation, shared semantic changes, integration admission, full-suite tagging, cumulative learned-memory sessions, and evidence promotion.

## 4. CL0 — frozen-cut reconciliation and preflight

**Owner:** INT  
**Serial:** yes  
**Time budget:** 2 hours maximum

The current checkout does not contain all remote protocol and researcher material. CL0 must reconcile and verify, rather than assuming that branch prose describes the active tree.

### Inputs

```text
current session branch: arena/01a0fe4e-cat-theo-machine
protocol mapping:       origin/arena/01a05cb0-cat-theo-machine
researcher prototype:   origin/arena/01a0eca3-cat-theo-machine
optional track ledgers: origin/arena/01a06cca, 01a06274, 01a049fa, 01a068c2
```

### Outputs

```text
cut-0 commit/tag containing the selected implementation inputs
repository-map.md       active vs parked files and real entry points
drift.md                 branch/interface/method vocabulary drift
baseline.json            focused and full-suite baseline
verification-table.md   every external protocol claim and its probe
route-probe.json        G4 and S2 eligibility results
go-record.json           GO, RE-SCOPE, or STOP
```

### Required probes

1. Record commit SHA, tree SHA, parent SHA, environment, and dependencies.
2. Identify active code versus `.py.txt`, blueprint, ledger, and report files.
3. Verify persistence and fresh-process replay for the terms used by the experiment.
4. Verify the existing planner method vocabulary against the five-method charter.
5. Verify whether `researcher_v0` can be lifted or must be adapted.
6. Probe both autonomy routes in parallel:
   - G4 invariant mining;
   - S2 contracted relation-schema mining.
7. Check for an eligible training corpus and held-out split.
8. Run focused tests, full tests where available, and blank controls.

### Outcomes

```text
GO
    the selected route, replay path, and experiment seam are executable.

RE-SCOPE
    a named foundation or integration item blocks autonomy; work only on
    that item and report AUTO_CANDIDATE=BLOCKED.

STOP
    no usable runtime, corpus, or reproducible cut exists within the budget.
```

A refuted repository assumption may change the critical path. It must not be silently ignored.

## 5. CL1 — contract and seal freeze

**Owner:** contract steward / INT  
**Depends on:** CL0  
**Time budget:** 1 hour

Freeze the following machine-readable envelopes before implementation dispatch:

```text
TaskRecord
TraceRecord
CandidateRecord
CertificateRecord
ProofReceipt
CheckerReceipt
ExperimentReceipt
ArtifactManifest
AgentReport
```

Workers must be able to use stubs and fixtures without waiting for the final runtime wiring.

### Shared seal registry

Create `protocol/SEALS.txt` in the cut-0/CL1 commit with digests for every holdout or fixed budget:

```text
E.C4
I.PoolB
F.target
S.holdout
PG.holdout
fixed search budget
```

A digest alone is not an information-flow boundary. Plaintext holdouts must not exist in worker-visible checkouts, prompts, task artifacts, or generated context before the relevant candidate/explanation/tag is sealed.

The controlled sequence is:

```text
operator-only holdout
    → candidate or explanation artifact generated
    → artifact hash committed
    → INT logs reveal
    → evaluator receives plaintext
```

Premature exposure invalidates the relevant held-out claim.

### Route selection

If exactly one of G4 and S2 is eligible, use it. If both are eligible, select exactly one using this fixed order:

1. smaller trusted surface;
2. stronger existing test coverage;
3. fewer shared-file changes.

The unselected route becomes follow-up work. Do not turn one day into two simultaneous autonomy experiments.

## 6. Task DAG

```text
CL0  frozen-cut reconciliation
 │
 ▼
CL1  contracts, fixture, seals, route selection
 │
 ├──────────────┬──────────────┬──────────────┬──────────────┐
 ▼              ▼              ▼              ▼              ▼
CL2A           CL2B           CL3A           CL3B           CL4
candidate A   candidate B   checker A      checker B      evaluator,
(independent) (independent) (independent)  (independent)  holdout,
                                                          mutation,
                                                          ablation
 │              │              │              │              │
 └──────────────┴──────────────┴──────────────┴──────────────┘
                              │
                              ▼
                         CL5 replay /
                         persistence
                              │
                              ▼
                         CL6 harness /
                         grader
                              │
                              ▼
                      INT integration cut
                              │
                              ▼
                         CL7 red team
                              │
                              ▼
                         final report/tag
```

The selected candidate route is implemented twice independently by CL2A and CL2B. The candidate mechanisms must not share code or see each other’s first reports. The candidate is selected only after both have emitted or failed under the same contract.

### Parallel track measurements

These run on the current frozen cut where their prerequisites exist:

```text
G-eng → G/I curriculum → I exam
E training → held-out C4 explanation
F tools → blank controls → decoy → target
S contracts → S2 probe or schema measurement
researcher_v0 G0–G6 laboratory
```

A concrete residual/dependency characterization component is a shared dependency for both the core loop and F:

```text
residual characterization → closed-loop experiment
residual characterization → F decoy/target classification
```

## 7. Executable task cards

Every dispatched task must use this envelope:

```text
TASK:
OWNER:
DEPENDS_ON:
INPUTS:
OUTPUTS:
MAY_MODIFY:
MUST_NOT_MODIFY:
CONTRACT_VERSION:
TIME_BUDGET:
ACCEPTANCE_TESTS:
ARTIFACTS:
REPORT_ENVELOPE:
```

### CL2A / CL2B — Machine-generated candidate

**Depends on:** CL1  
**May modify:** task-owned candidate module, probes, and tests only  
**Must not modify:** trusted schema/rule stores, holdout plaintext, shared runtime files

The candidate must be emitted from the Machine’s own training traces, cite those traces, remain untrusted, and generalize a role or structure across distinct training instances. A hardcoded fixture answer fails.

If the selected route is G4, the candidate is an invariant certificate. If it is S2, it is a contracted relation schema. In either case the candidate must remain outside durable trusted memory.

### CL3A / CL3B — independent proof checkers

**Depends on:** CL1  
**May modify:** isolated checker module, mutation probes, tests  
**Must not modify:** proof search, candidate generation, trusted rules

Each checker verifies expanded derivation steps using only premises and trusted rules. Neither checker may call search, the prover, or the candidate generator. Both must reject:

- mutated premises;
- mutated conclusions;
- wrong repeated-variable bindings;
- fabricated premises;
- unbound variables;
- foreign-goal derivations;
- candidates outside the admitted session scope.

### CL4 — evaluator, holdout, mutation, and ablation

**Depends on:** CL1 and checker contracts  
**May modify:** evaluator, expander, fixtures, probes, and reports  
**Must not modify:** candidate generation or trusted rule stores

The evaluator owns expansion of the untrusted candidate into proof steps. It must expose the candidate digest before holdout plaintext is revealed. It runs:

- at least three withheld positive instances;
- near-miss negatives;
- wrong-variable and missing-premise cases;
- mutation tests;
- no-candidate ablation;
- ruleset-scope mismatch tests.

### CL5 — persistence and cold replay

**Depends on:** CL1 and receipt contracts  
**May modify:** persistence probes and a minimal INT integration proposal  
**Must not modify:** the experiment claim or holdout policy

Save and restore:

```text
goal and task digest
training traces
candidate and provenance
admission/scope decision
expanded proof
checker receipts
ruleset digest
experiment state
```

Terminate the process, load in a fresh process, and reproduce the checker verdict without fallback registration or silent promotion.

### CL6 — harness and grader

**Depends on:** CL2–CL5  
**May modify:** experiment runner, artifact utilities, report schema

One command must run the applicable experiment and write content-addressed artifacts. A failed conjunct must produce a non-zero result.

### CL7 — red team

**Depends on:** integrated candidate  
**May modify:** adversarial probes and reports only

Attack:

- holdout leakage;
- candidate hardcoding;
- premature activation;
- checker/search coupling;
- mutated proofs;
- stale certificates after ruleset change;
- ablation that still succeeds;
- replay with a different goal;
- target-specific branches;
- G5 writing into live knowledge;
- G6 graph edges into live knowledge.

### INT — integration

Only INT edits shared semantic surfaces. It merges exact worker SHAs in this order:

```text
contracts and fixtures
→ selected checker pair
→ residual/dependency path
→ candidate adapter
→ persistence/replay
→ evaluator/harness
→ red-team probes
```

After each semantic merge: focused tests, full suite, blank controls, and a fresh immutable tag where required.

## 8. Researcher-v0 and invariant playground

The invariant playground is a G-based cross-track laboratory, not a sixth dimension. The remote `researcher_v0` prototype provides the reference shape:

```text
G0 inspect and reuse existing machinery
G1 bounded Engel-style domain
G2 task generation/canonicalization
G3 baseline without mining
G4 invariant mining
G5 independently checked, session-scoped use
G6 inert discovery/provenance graph
```

The prototype domain uses an even-reachability ruleset with `Add2`, `Remove2`, and `Swap`/identity, plus an `Add1` scope-changing variant. Its purpose is to test candidate generation, counterexamples, exact-ruleset checking, pruning, and scope invalidation—not to claim FLT discovery.

G5 is temporary session-local use only. G6 is the persisted inert record. Neither stage may admit a new permanent rule. A certificate must be invalidated when the ruleset digest changes.

The researcher output graph may include:

```text
Task, Attempt, Transition, Outcome,
CandidateInvariant, BrokenOn, Certificate,
PruneEvent, ScopeMismatch
```

The researcher is an execution/evidence layer:

```text
task manifest
    → baseline attempts
    → candidate mining
    → independent checking
    → session-local use
    → counterexamples/scope checks
    → inert graph
    → morning report
```

It does not replace INT, does not promote knowledge, and does not establish global mathematical novelty.

## 9. Track-specific operator checks

### S

- Probe whether the law store contains an S2-eligible pair.
- If not, report `S=BLOCKED` rather than fabricating a corpus.
- Verify schema-store objects are not shared with `FireAny`.
- Require at least two source goals and deterministic reset/remine behavior.

### E

- Keep C4 plaintext operator-only until the explanation artifact is hashed.
- Every sentence must resolve to a law name and source term.
- Corrupt a derivation-spine term and verify the explanation changes or fails.

### F

- Run blank controls, decoy, then target on an immutable tag.
- A3 requires target-specific residual/dependency behavior distinct from the decoy.
- Equal residuals support A1 at most and withdraw the discovery reading.

### G

- Verify exactly the five charter methods.
- Each method must have a non-vacuous obligation generator on at least one card.
- Divide and Symmetry count targets require count-shaped obligations.

### I

- Hash Pool A and Pool B manifests.
- Keep Pool B plaintext outside worker-visible state.
- Retire any exam item released for training.

## 10. Acceptance and grader

`AUTO_CANDIDATE=PASS` requires all of the following:

1. CL0 returned `GO`.
2. The Machine emitted the candidate from its own training traces.
3. The candidate was sealed before holdout exposure.
4. The candidate was absent from trusted stores before the run.
5. The candidate generalized across distinct training instances.
6. Multiple withheld positives passed.
7. Declared negatives and near-misses were rejected where required.
8. Both independent checkers accepted valid expanded proofs.
9. Both checkers rejected mutation cases.
10. Neither checker invoked search or proof generation.
11. Cold replay reproduced the verdict.
12. Ablation restored failure or the predeclared baseline behavior.
13. No durable trusted-memory promotion occurred.
14. Baseline failure sets did not silently worsen.

The final report must contain:

```text
cut_sha
release_sha
drift_status
claim_profile
integration_demonstration
candidate_route
auto_candidate
sealed_before_holdout
checker_A
checker_B
cold_replay
mutation_controls
ablation
researcher_graph_inert
S_result
E_result
F_classification
G_result
I_result
baseline_delta
novelty = UNASSESSED
```

Possible status values include:

```text
PASS
FAIL
BLOCKED
NOT_RUN
INTEGRATION_ONLY
HOLDOUT_INVALID
CHECKER_FAIL
REPLAY_FAIL
ABLATION_FAIL
INFRASTRUCTURE_FAIL
```

## 11. Milestone ladder and schedule

```text
M0  frozen cut, repository map, drift table, baseline, GO/RE-SCOPE/STOP
M1  contracts, fixture, and seal registry
M2  independent checkers and cold-replay machinery
M3  fixture-supplied integration loop
M4  Machine-generated candidate emitted
M5  held-out candidate generalization
M6  mutation, ablation, and replay pass
M7  inert overnight-research graph
M8  reproducible morning report
```

Suggested schedule:

```text
00:00–02:00  CL0
01:00–03:00  CL1 in parallel with final CL0 probes
03:00–08:00  CL2–CL5 parallel work
06:00–09:00  CL6 harness and first integration
09:00–11:00  INT frozen candidate cut
11:00–14:00  held-out evaluation and red team
14:00–16:00  replay, ablation, grading, artifact sealing
```

No feature work begins after the integration cutoff. The final quarter is reserved for verification and reporting.

## 12. Human role and recovery

After launch, the human does only:

1. approve the frozen cut and launch configuration;
2. review the final grader and one-page report.

The human does not select candidates, reveal individual holdouts, choose implementations, interpret transcripts, or decide whether a checker failure counts.

Worker failure causes a replacement attempt against the same contract. Interface mismatch causes a versioned change request. A sandbox reset causes recovery from pushed SHAs and regeneration of derived artifacts. No unpushed semantic work is considered part of the experiment.

## 13. Claim discipline

A fixture-supplied candidate passing the trust loop is reported as:

```text
integration_demonstration = PASS
```

It is not reported as autonomous discovery.

A Machine-generated candidate passing the sealed held-out, dual-checker, replay, mutation, and ablation gates is reported as:

```text
auto_candidate = PASS
```

This is bounded autonomous schema/invariant generalization. It is not a claim of global mathematical novelty. Novelty remains:

```text
UNASSESSED
```

The remote protocol ledgers and `researcher_v0` branch are inputs to CL0, not evidence that the current checkout already implements the entire programme.
