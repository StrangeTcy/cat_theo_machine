# CTM-ODR-6 — Verified Autonomous Loop (VAL)

**Spec ID:** `CTM-ODR-6`
**Date:** 2026-10-01
**Target repo:** `StrangeTcy/cat_theo_machine`
**Base commit inspected:** `428ecdc146e38de3481222bed7bddeb3c08e1b2d`
**Timebox:** 16 h hard stop
**Supersedes:** ODR-1 … ODR-5 (rounds 1–5 of the spec chain)
**Claim discipline:** two independent claims, two independent grader fields, one shared harness. No claim may wear the other's name.

---

## §0 Why this is not "another plan"

ODR-1 through ODR-5 were written against a repository nobody had executed. I executed it. Six load-bearing assumptions in that chain are false or inverted, and one of them — not the choice between "integration demonstration" and "autonomous induction" — is the binding constraint on your one day.

| # | Assumption in ODR-1…5 | Status | Measured reality |
|---|---|---|---|
| V3 | "No human decision may occur after the experiment begins" (stated as a design property to be enforced) | **False today, in code, on the hot path** | `search/compare_subprocess.py:248` prints a prompt and calls `input()`. The non-interactive switch (`graph._search_disable_console`) *defers* derivation materialisation instead of approving it (`:236`). Also `main.py:226`, `main.py:273`. |
| V5 | "Independent checker … must not call the top-level prover" | **Necessary but insufficient** | There is no step-level checker at all. The only check is `Search._derivation_reaches_goal` (`proof.py:1126`) = `DerivationEnd == goal`. Nothing validates that a single step is justified. |
| V6 | (unstated) checking a derivation requires search | **False — checking is feasible** | `Step(current, action, next_term)` (`proof.py:1814`) plus `StepAction`/`ActionRule`/`ActionBindings`/`ActionPath` (`proof.py:454–480`) mean a step *records which rule and which bindings*. Verification is replay, not search. |
| V4 | CL2/CL3/CL4/CL5 (checker, teaching binding, admission, dependency characterisation) are integration work | **They are greenfield** | `grep` for `Residual\|DependencyRequest\|TeachingCandidate\|AdmissionDecision\|ProofReceipt` over `*.py` returns one unrelated hit (`ResidualHeadBucketLabel`). None of that vocabulary exists. Terminal classes are only `Search{Success,Failure,TimedOut,AbortedByUser,Running}Label`. |
| V7 | Schema induction (M5) is "the only greenfield research-risk task" | **Inverted — the substrate exists** | `schemata.py` + `graph.add_derivation_schema`/`lookup_derivation_schema` (`graph.py:174–186`) + consumption in the engine (`search/engine.py:2093`) + persistence root `derivation_schemata` (`persistence.py:426`) + pack-authored schemas (`packs.py:280–296`). Missing pieces: a **producer** and a **checker**. |
| V14 | "Full sharded suite after every semantic merge" | **Not executable** | No test sharding exists (the only sharding is `constructor_registry` restore, `persistence.py:269`). `main test` emits no incremental output and did not terminate in **>35 min at 100 % CPU** in this environment. |

Two further facts that change the work plan:

- **V10 — there are two disconnected systems in this repo.** (A) the hypergraph prover: `main.py`, `proof.py` (173 KB), `search/` (~0.5 MB), 48,606 LOC, 256 test objects, 12 packs, 159 rules. (B) `hyge.py` + `session.txt`: a **standalone** string-term rewrite machine (zero imports) with a teaching grammar (`lemma` / `proc` / `step` / `query`) that **runs successfully end-to-end right now** and prints two taught procedures agreeing over a span with a cited lemma. Every round of the chain specified work for a third, imaginary system. Lineage B already contains the concept the chain called "teaching."
- **V11 — a name collision that blocks naive unification.** `hyge.py` shadows the former `hyge` package name, so all four `validation/*.py` planner tests die at `from hyge import machine as M` (ImportError). `validation/` is dead evidence and must not be counted as a passing suite.

**Consequence for the plan.** The highest-value work is not "choose a stronger claim." It is: (1) make the loop *actually* unattended at the one real seam, and (2) make every proof step *independently checkable*. Both are cheap, both are prerequisites for every stronger claim, and neither appears in any prior round. Induction is the *research* risk, but it is **not the schedule** risk — nobody can evaluate an induced schema until a checker exists.

---

## §0.1 Operator ruling and measured correction (2026-10-01, after dispatch)

Two changes void parts of what follows. Both are operator/measurement facts, not inferences.

**Ruling — `hyge.py` is irrelevant.** The lineage-B teaching surface is withdrawn. §1's "teaching surface = B's grammar" decision is **void**, and the CL5 card that ports `session.txt`'s `lemma`/`proc`/`step`/`query` grammar is **struck**. The teaching artifact is now authored directly in A's native declarative form — the pack-format candidate of §1 ("candidate representation = A's pack format"), admitted through the same gate. Nothing else in the DAG changes; CL5 keeps its slot, its owner and its acceptance tests, with the compiler replaced by a pack-format validator. `hyge.py`, `session.txt`, and every argument that leaned on them are out of scope.

**Measurement — cold restore fails today.** The dispatched baseline (`verification/closed_loop/BASELINE_2026-10-01.md`, bundle commit `435ea71`) ran the snapshot round trip I had left as open probe #3. It **fails**: proofs are readable before save, and after fresh-process activation both restored derivation entries lack constructors, so readers return `EmptyList`. Working hypothesis recorded there: `SnapshotCodec._record_for` searches all namespace aliases before writing, while `save_runtime` synchronises a namespace containing `AllConstructors` — a mutable state root named as if it were fixed vocabulary, so the importing process's registry can overwrite it on restore.

Consequences, applied below:
- **F1 (persistence localisation) is on the critical path**, ahead of CL4, and ahead of M2's cold-replay half. It is not a CL0 probe any more.
- My CL2 mutation case #10 (identical verdicts after cold restore) and CL4's acceptance are **blocked on F1** and must be reported as `BLOCKED` rather than `FAIL` if it is not repaired in time.
- The bundle's own rule stands and is now binding: repair must **not** be achieved by registering missing constructors or deleting the assertion.
- The bundle's unexplained observation — `MachineRuntime.prove` entering multi-mode comparison and not terminating within 60/180/90 s — **has a located cause**. `Prove._maybe_seed_search_comparison` (`proof.py:3166`) seeds `CompareSearchModes` unless `graph._search_disable_console` is truth; `search/compare_subprocess.py:638` calls `_approval_to_materialize_best_attempt`; `:248` prompts and `:236` defers when console is off. Confirmed by direct run: `main cold` with stdin closed stops at that prompt. This is CL1's seam.

## §1 The architectural decision the chain never made

ODR-1…5 oscillated between "the active lineage has a session loop" and "the session file is a sketch." Both are true, of *different* artifacts. Decide once, in CL0, with probes:

- **System of record = A** (the prover). It has the rule corpus, the search engine, the persistence codec, the schema registry, and the test suite.
- **Teaching surface = A's own declarative pack format**, authored as a standalone artifact and handed to the machine-term compiler (see §0.1: lineage B is withdrawn by operator ruling; `hyge.py` and `session.txt` are out of scope).
- **Candidate representation = A's pack format.** A candidate rule is `{"id", "pattern", "replacement"}`; a candidate schema is `{"id", "start", "goal", "plan"}`. Both already compile through `PackLoader` and are already the format the engine consumes and the codec persists.

If CL0 cannot confirm any of these three by probe, it returns `RE-SCOPE` — see §4.

---

## §2 Success conditions

### Track I — `INTEGRATION_LOOP` (mandatory, the deliverable)

> Starting from a frozen commit and a cold boot, with no interactive input available, the Machine runs a bounded experiment end to end: a goal fails, the failure produces a **machine-term residual**, a canonical teaching artifact **enters via the teaching channel** (not a source edit, not a `packs/` write), is **admitted for this session only** after passing positive/negative checks, the retry yields a derivation, **an independent step-level checker validates every step**, the run **replays from a fresh process**, and the **ablation returns the original failure**. One command, hashed artifacts, non-zero exit on any failed conjunct.

### Track II — `AUTO_SCHEMA_INDUCTION` (sealed, the autonomy claim)

> Given only a frozen training corpus and its traces, the Machine itself emits a generalised derivation schema, the candidate is **hashed and sealed before holdout exposure**, the holdout is released, expanded proofs pass **both** checkers, negative/mutation controls reject, ablation under a **sealed budget** restores failure, and cold replay reproduces the verdicts.

### Explicit non-claims

- Track I is **not** discovery. An externally supplied rule that passes admission means `AUTO_SCHEMA_INDUCTION: FAIL` even when `INTEGRATION_LOOP: PASS`.
- Neither track claims global novelty. `novelty: UNASSESSED`, adjudicated outside the automated gate.
- Passing neither track is still a reportable result **if** M0–M2 artifacts are complete.

### Ladder (each rung is a standalone artifact)

| Rung | Condition | Grader field |
|---|---|---|
| M0 | Frozen tag, bounded baseline, failure ledger, environment record | `base` |
| M1 | A failing goal emits a concrete machine-term residual without human input | `INTEGRATION_LOOP` partial |
| M2 | **Minimum viable fallback.** Loop runs unattended; a persisted derivation is replay-checked step-by-step by an independent checker that rejects mutations. **Cold replay requires F1 (persistence repair) first** — see §0.1. If F1 is unlanded, M2 is met by in-process replay and the cold half is reported `BLOCKED`, not `FAIL` | `INTEGRATION_LOOP` partial |
| M3 | A taught rule enters through the channel, is admitted session-scoped, and closes the gap | `INTEGRATION_LOOP: PASS` |
| M4 | Four legs — control / treatment / replay / ablation — all verified causally | `INTEGRATION_LOOP: PASS` (full) |
| M5 | Machine-induced schema, sealed before holdout, passes both checkers | `AUTO_SCHEMA_INDUCTION: PASS` |

**MVF is M2.** Rationale: M3–M5 depend on a teaching channel and an admission gate that do not exist; M2 depends only on machinery that does (V6, V8). If the day collapses, M2 is the rung that is still worth showing someone.

**Headline sentence, fixed in advance (every outcome is accurate):**
> "The loop runs unattended and every proof step it produces is independently checked. It reached M⟨n⟩; the next blocking step is ⟨machine-readable residual⟩."

---

## §3 Frozen contracts

**Rule (R1): no parallel vocabulary.** Constructs must be expressed in existing ontologies, mapped to existing constructors by CL1. Two specific mandates:

1. **Residual / dependency** must be built on the **planner ontology** that already exists: `PlannerProblem`, `PlannerProblemGoal`, `PlannerProblemMethods`, `PlannerObligation`, `PlannerAlternative*` (`AlternativeStatus`, `AlternativeEvidence`, `AlternativeParent`, `AlternativeMethod`, `AlternativeChildren`), `PlannerStateAlternatives`, **`PlannerDependency`**, `PlannerJob` (`planner.py:9–527`; usage example `validation/test4_planner_lifecycle_regressions.py:72`). A residual is an obligation with evidence; a dependency request is a `PlannerDependency`. Do **not** invent `ResidualRecord`/`DependencyRequest` classes. Note: planner state is **not** persisted today (V8) — persistence of the residual is CL4's job and is a finding, not an assumption.

2. **Candidates** use the pack format (§1). Admission is a *gate before load*, not a new class.

**Rule (R2): no test-visible fixture constants.** The generated fixture family (§8) may not be branched on by app code.

**Rule (R3): every claim names its artifact** (path + sha256). No prose evidence.

**Rule (R4): no code change between experiment legs.** Legs differ by inputs and by the admission gate, never by source.

**Rule (R5): `core.py` is not edited.** If `core.py` must change, the sprint is over — that is a `STOP` condition, not a merge.

---

## §4 Preflight: CL0 with a `GO / RE-SCOPE / STOP` gate

CL0 is executable, not descriptive. It must *run* these probes and record raw output:

| Probe | Command | Record |
|---|---|---|
| Importability | `python3 -m cat_theo_machine.main --help` | must print usage; **requires `gmpy2` + `PyYAML`** (V1) |
| Cold boot | `python3 -m cat_theo_machine.main cold` with stdin closed | pack count, rule/schema/example counts, wall time, and **whether it terminates** |
| Autonomy | same, plus the CL1 flag once landed | terminates without `input()` or raises `InterventionError` |
| Non-interactive search | `search-worker` two-phase protocol: `HYGE_SEARCH_WORKER_DEFER_DERIVATION=1` then `HYGE_SEARCH_WORKER_RESUME_DERIVATION=1` | a materialised derivation, by path |
| Snapshot round trip | `boot_from_packs` → `save_runtime` → `boot_from_snapshot` in a fresh interpreter | derivations + `derivation_schemata` identical (V8) |
| Rule admission seam | add a rule + rule chain to a **booted** graph without touching `packs/` | the exact call path, or `RE-SCOPE` |
| Fixture vehicle | load a generated pack, drive `_theorem_agenda` (`main.py:377`) | control case fails, treatment case proves |
| Bounded baseline | named subset + low `HYGE_SEARCH_WORKER_TIMEOUT`; **and** the full suite as a background watchdog with incremental receipts | baseline failure set, and evidence the suite itself is unbounded (V14) |

Recorded environment (measured 2026-10-01, this sandbox): Python **3.11.2**; `gmpy2` **2.3.1**; `PyYAML` **6.0.3**. Pinned `environment.yml`: Python **3.12.13**, `gmpy2` **2.3.0**, `pyyaml` **6.0.3**, Windows conda env `hyge`. **The delta is a recorded precondition, not a footnote.**

Measured baseline facts to carry into the report: pack load **23.60 s** (geometry alone 6.94 s); cold summary **rule_count 159 / schema_count 4 / example_count 27** across 12 packs; the agenda reached "SearchBFS found a plan" and then **blocked at the prompt**; total LOC 48,606; 256 test objects; `validation/` unreachable (V11).

### Predeclared outcomes

- **`GO`** — importability, cold boot, non-interactive search→derivation, snapshot round trip, rule-admission seam, and fixture vehicle all probe green.
- **`RE-SCOPE: FOUNDATION_ONLY`** — any of the above fails. Scope becomes: the failing probe, its minimal fix, and a written account. `INTEGRATION_LOOP: BLOCKED`. **Do not** quietly substitute a weaker goal for the one you declared.
- **`STOP`** — `core.py` must be edited, or the fixture cannot be expressed in existing machine terms, or the environment cannot be pinned to a reproducible interpreter.

**CL0 may not silently weaken the claim after seeing results.** It may issue a *versioned* re-scope **before** dispatch.

### Measurement hygiene (new, mandatory)

`python3 -m cat_theo_machine.main cold` **rewrites the tracked 18 MB `snapshots/hyge_snapshot_v8.json`** and writes `snapshots/search_compare/run-*/`. A "frozen tag, rerun, same result" claim is fiction unless runs are isolated. All measurement runs must use a scratch snapshot directory, and every leg must be followed by `git status --porcelain` on tracked paths; a dirty tree invalidates the leg. (Observed: `M snapshots/hyge_snapshot_v8.json` after a single cold run.)

---

## §5 File ownership

**Integrator-only shared surfaces** (worker patches touching these are rejected and returned as change requests):

```
labels.py            machine.py         graph.py
persistence.py       runtime.py         main.py
testsuite.py         packs.py           proof.py
search/compare_subprocess.py            search/engine.py
```

**Worker-owned surfaces** (new files, chosen to avoid collisions):

| Task | Owned paths |
|---|---|
| CL1 | `main.py`, `search/compare_subprocess.py` (**integrator-owned task**: keystone, shared files) |
| CL2A | `verification/step_checker_a.py`, `verification/probes_a/` |
| CL2B | `verification/step_checker_b.py`, `verification/probes_b/` |
| CL3 | `research/residual.py`, `research/planner_bridge.py`, `research/probes/` |
| CL4 | `research/replay_harness.py`, `research/probes_replay/` |
| CL5 | `teaching/session_grammar.py`, `teaching/compile_candidate.py`, `teaching/probes/` |
| CL6 | `research/admission.py`, `research/probes_admission/` |
| CL7 | `experiments/closed_loop_experiment.py`, `experiments/fixtures/` |
| CL8 | `induction/generalize.py`, `induction/seal.py`, `induction/probes/` |
| CL9 | `redteam/` |
| CL-D | `plans/decomposition-probe-{1,2}.md` |
| F1 | `research/probes_persistence/`; `persistence.py` only as an **INT-applied** line-specific change request |
| CL10 | integration + release only |

New shared labels needed by any task are requested as: `required symbol / required layout / consumer / persistence requirement / test that fails without it`.

---

## §6 Task DAG

### 6.1 Serialization audit — performed against this DAG, with results

The rule: **an edge must name the artifact it transfers, not the task it comes from.** An edge whose transferred artifact can be stubbed, fixtured, hand-built, or generated in isolation is not a dependency — it is a preference, and preferences do not consume critical-path hours.

| Edge as first drawn | Transferred artifact | Stub / fixture / generator available? | Verdict |
|---|---|---|---|
| CL0 → CL1 | knowledge of which files hold the seam | file list obtainable in ~5 min; baseline can run in an isolated worktree | **DISSOLVED** — CL1 starts at T+0 |
| CL1 → CL2A/B | *none named* | a derivation term of known shape is hand-buildable; the checker never needs how it was materialised | **DISSOLVED** — CL2A/B start at T+0 |
| CL2 → CL3 | *none named* | residual reads `SearchAttemptStatus` / completion reason; independent of the checker | **DISSOLVED** — CL3 starts at T+0 |
| CL2 → CL5 | *none named* | pack-format compiler touches nothing the checker owns | **DISSOLVED** — CL5 starts at T+0 |
| CL3 → CL4 | a residual term | a hand-written `PlannerObligation` fixture | **PARTIAL** — CL4 construction unstubbed; acceptance waits |
| CL5 → CL6 | a candidate term | a hand-written pack-format candidate | **PARTIAL** — CL6 builds against the stub, acceptance waits |
| CL2/CL3/CL4 → CL7 | component verdicts | harness built first against stubs = the ignored "harness-first" rule | **PARTIAL** — CL7 construction at T+0 |
| CL7 → CL8 | training traces | CL8 generates its own by running the family through the prover | **DISSOLVED** — CL8 starts at T+0 |
| CL7 → CL9 | *none named* | red team needs only the frozen contract | **DISSOLVED** — CL9 starts at T+0 (this contradicts "continuous", which was already written) |
| CL9 → CL10 | red-team verdicts | — | **REAL** |
| CL0 baseline → any "failure set did not grow" claim | the pristine failure set | — | **REAL** (a difference needs a before-measurement) |
| F1 → CL4 cold-replay acceptance | a working codec | **none** — cold restore is *measured failing*; no stub round-trips a broken codec | **REAL** |
| frozen fixtures → CL6 acceptance | frozen positive/negative sets | — | **REAL** (R4: legs may not differ in code, so fixtures freeze first) |

**Result.** Nine of thirteen drawn edges were preferences. The critical path I published one turn ago (`CL0 → CL1 → CL2 → CL3 → F1 → CL4 → CL7 → CL9 → CL10`) was wrong twice over: CL2 was never downstream of CL1, and CL4/CL7 were carrying construction time that belongs at T+0.

### 6.2 Revised DAG — dissolution applied

```
T+0  ┌ CL0   probes + baseline (pristine worktree)            [serial, INT]
     ├ CL1   approval seam + InterventionError hook           [keystone, INT]
     ├ CL2A/CL2B  dual step checkers                          [redundant, isolated]
     ├ CL3   residual as planner obligation
     ├ CL5   pack-format artifact → candidate
     ├ CL7   harness skeleton against stubs + fixture family   [harness-first]
     ├ CL8A/B    induction, self-generated traces              [redundant, isolated]
     ├ CL9   red team against the frozen contract              [continuous]
     └ CL-D  decomposition probe (two independent rewrites)    [new, see 6.3]

T+~2 └ F1   persistence localisation + repair                 [blocks cold replay]
T+~4 └ CL4  replay: in-process first, cold half after F1
T+~5 └ CL6  admission: built on stub, acceptance on frozen fixtures
T+~7 └ CL7F four-leg run, real inputs wired
T+~9 └ CL9F final adversarial pass
T+~12└ CL10 integration + tag                                  [serial, INT]
```

**Revised critical path:** `CL0 baseline ∥ CL1 → F1 → CL4(cold) → CL7F → CL9F → CL10` ≈ **7–9 h**, down from the 10–13 h I published. The keystone and the checkers are no longer on it at all; F1 is.

### 6.3 The deeper prize: can the swarm find a decomposition you did not know beforehand?

Nothing in the previous draft provided a mechanism for this. Two are added.

**Standing mechanism — `DependencyDissolution` records.** Any worker, at any time, may file a first-class record: `{edge, transferred artifact, stub/fixture that dissolves it, cost, risk}`. INT adjudicates within the hour. Asymmetry, deliberately: **dissolving an edge is auto-accept when the stub is cheap and the artifact is named; adding an edge requires justification of why no stub exists.** A DAG that can only accrete edges is how a one-day plan becomes a two-week plan.

**One-shot probe — `CL-D`.** Two agents independently rewrite this DAG from the goal and constraints alone, without reading each other or §6. Deliverable is not their DAGs; it is their **disagreements**. They converge by T+2, cost 45 min each, and INT folds in what survives. This is the only task in the spec whose output is a better plan rather than a better artifact, and it is the literal answer to the question.

### 6.4 Ownership table

| Task | Owner | Serial? | Est. |
|---|---|---|---|
| CL0 | integrator | yes | 1.0–1.5 h |
| CL1 | integrator | yes | 0.5–1.0 h |
| CL2A / CL2B | 2 auditors, isolated | no | 2.0–3.5 h |
| CL3 | residual engineer | no | 1.5–2.5 h |
| CL4 | persistence engineer | no | 1.5–2.5 h |
| CL5 | teaching engineer | no | 2.0–3.0 h |
| CL6 | admission engineer | no | 1.5–2.5 h |
| CL7 | evidence engineer | no | 2.0–3.0 h |
| CL8 | induction engineer ×2 (A/B, isolated) | no | 3.0–5.0 h |
| CL9 | 2 red-teamers | continuous | 3.0–6.0 h |
| CL-D | two independent planners | one-shot, 45 min each | 1.5 h |
| F1 | persistence engineer | no | 2.0–4.0 h |
| CL10 | integrator | yes | 1.5–2.5 h |

---

## §7 Task cards

### CL1 — Unattended approval seam + autonomy audit hook  *(the keystone)*

**Why first.** Every later leg is meaningless until the loop completes with no stdin. Today "no human decision after launch" is not a property of the system; it is a property of the operator's patience.

**Procedure.**
1. Introduce an explicit non-interactive approval policy: `HYGE_APPROVAL_POLICY ∈ {interactive, auto-proceed, deny}` (env or CLI flag; mirror the existing `HYGE_SEARCH_WORKER_*` env protocol).
2. At `search/compare_subprocess.py:248`, replace the unconditional prompt with: policy `interactive` → current behaviour; `auto-proceed` → proceed to the resume worker; `deny` → decline. The approval is recorded as a **machine-term event with provenance naming the policy**, not "a human said yes."
3. Distinguish this from `graph._search_disable_console` (`:236`), which currently **defers** replay. Keep both semantics explicit and documented in-code: "console off ≠ approval granted."
4. Add a **runtime audit hook**: with `auto-proceed`, reaching *any* `input()` call (`compare_subprocess.py:248`, `main.py:226`, `main.py:273`) raises `InterventionError` rather than blocking. A claim becomes an invariant.
5. Add a focused test to `testsuite.py`: run the two-phase `search-worker` protocol with `auto-proceed` and stdin closed; assert a materialised derivation and zero prompts.

**Acceptance.**
- `main cold` with stdin closed terminates and materialises a derivation (measured before/after wall time recorded).
- With `auto-proceed`, an injected prompt raises `InterventionError`; the test fails loudly if a new prompt is added later.
- Default (`interactive`) behaviour is byte-identical for a human at a terminal.
- The diff is small enough to review in one pass; no change to search semantics, rule selection, or verification.

**Kill condition.** If `CL1` cannot be done without touching `proof.py` search logic, stop and `RE-SCOPE` — that is evidence the seam is not where the code says it is.

---

### CL2A / CL2B — Dual independent step-level checkers

**Objective.** Decide, for a persisted derivation plus the trusted rule set, whether **every step is justified** — without invoking search and without invoking the builder.

**Interface (machine-term, mapped to existing constructors by CL1).**

```
StepCheck(derivation, trusted_rules, registry) -> machine-term verdict
verdict ∈ {
  check-ok,
  reject-untrusted-rule,     # step names a rule not in the trusted set
  reject-premises-unsatisfied,
  reject-conclusion-mismatch, # applying rule+bindings to current ≠ next
  reject-binding-inconsistency,
  reject-broken-chain,        # StepNext[i] ≠ StepCurrent[i+1]
  reject-goal-mismatch,       # DerivationEnd ≠ goal
  reject-empty
}
```

**Inputs available (V6):** `DerivationSteps`, `StepCurrent`, `StepAction` (= `StepRule`), `StepNext`, `DerivationStart`, `DerivationEnd`; action side: `ActionRule`, `ActionBindings`, `ActionPath`, `TheoremAction`, `RewriteAction`; rule side: `RulePremises`, `RuleReplacement`; primitives: `M.Match`, `M.MergeBindings`, `M.Instantiate`, `M.TermEqual`, `M.GetConstructor`.

**Forbidden — this is the whole point.** A checker may not import or call: `Search`/any search mode, `Prove`, `BuildDerivation`, `InstantiateDerivation`, `_apply_action`, `_match_premises`, `ExplainDerivation`. Reason (V6): `BuildDerivation._build` produces steps by calling `self._apply_action(...)`; a checker that reuses `_apply_action` or `_match_premises` re-uses the *producer's* semantics and can never disagree with it. Independence means re-deriving rule application over the **trusted primitives only**.

**Acceptance (mutation suite — each mutation is a structural edit to a persisted derivation).**

| # | Mutation | Required verdict |
|---|---|---|
| 1 | Untouched derivation | `check-ok` |
| 2 | Replace one step's `next_term` | `reject-conclusion-mismatch` |
| 3 | Swap a binding in `ActionBindings` | `reject-binding-inconsistency` or `reject-conclusion-mismatch` |
| 4 | Change `ActionRule` to a rule outside the trusted set | `reject-untrusted-rule` |
| 5 | Delete a middle step | `reject-broken-chain` |
| 6 | Insert a fabricated step | reject (any) |
| 7 | Check against a different goal | `reject-goal-mismatch` |
| 8 | Empty step list | `reject-empty` |
| 9 | **Builder-semantics probe:** a derivation that the builder accepts but whose premise was never satisfied in accumulating knowledge | reject — this is the case the builder's own matcher hides |
| 10 | Re-run 1–9 after cold restore | identical verdicts |

**Redundancy policy.** CL2B never sees CL2A's code, card, or results. Both ship. `INT` selects one as *the* release checker by (a) smaller trusted surface, (b) mutation coverage, (c) fewer shared-file requests; the other becomes the adversarial oracle. **Both** must pass mutation 9 or the track is not released.

---

### CL3 — Residual as a planner obligation

**Objective.** Turn a failed proof attempt into a concrete, machine-term, persisted residual — built on `planner.py`, not on new vocabulary (R1).

**Available failure surface (V4):** `SearchAttemptStatus`, `SearchAttemptSearchCost`, `SearchAttemptGoal`, `SearchAttemptHeuristic`; terminal classes `SearchFailureLabel`, `SearchTimedOutLabel`, `SearchAbortedByUserLabel`; reason strings via `HeuristicPerformanceCompletionReason` / `SearchStatusText` (e.g. `"success-plan-found"`, `"abnormal-exit-during-search exit=…"`).

**Required distinctions** (terminal class ≠ "something went wrong"):
`no-applicable-rule` · `applicable-rule-with-unmet-premise` · `binding-inconsistency` · `resource-exhaustion` (distinct from #1) · `malformed-goal` · `safety-refusal`.
Timeouts must **never** be reported as missing mathematics.

**Acceptance.** Five generated seeds yield residuals of the same structural class; a distractor fact does not change the residual; fact order does not change it; removing a required fact changes it appropriately; a parse failure is not reported as missing mathematics; no fixture constant appears in code; the residual round-trips through persistence (CL4).

---

### CL4 — Persisted replay from a fresh process

**Objective.** Prove the loop survives a real cold restart — reusing the codec, not rebuilding it (V8).

**Existing roots to use:** `constructor_registry`, `all_rules`, `rule_order`, `derivations`, `derivation_schemata`, `search_history` (`persistence.py:421–433`). Planner state is **not** among them — persisting the residual is new work; record it as a finding.

**Acceptance.** Save → terminate → fresh interpreter → restore → the same derivation is present, `StepCheck` returns the same verdict, shared-child identity holds where expected, no fallback registration is required, ablation can disable the session-scoped rule, and a checkpoint digest plus class manifest is emitted.

---

### CL5 — Teaching artifact → candidate  *(revised per §0.1; lineage B struck)*

**Objective.** A canonical teaching artifact, authored in **A's pack format** as a standalone file outside `packs/`, compiles into a **candidate** rule or schema: `{"id", "pattern", "replacement"}` via `PackLoader`'s rule compiler, or `{"id", "start", "goal", "plan"}` for a schema. Output is a candidate only — never activated, never written into `packs/`, never touching a durable promoted root.

**Rules.** The compiler is invoked against a throwaway loader namespace, not the booted graph, so compilation cannot mutate live knowledge. Candidate identity is structural (canonicalised ordered form), because admission compares structure, not labels.

**Acceptance.** A two-premise rule authored in the pack format compiles to a candidate with the expected structural digest; premise order does not change the compiled rule; a wrong join variable compiles to an **observably different** rule; an unbound conclusion variable is rejected; a malformed submission cannot modify knowledge; no target-specific relation name appears in implementation logic; the compiled candidate is byte-identical across two runs (determinism).

---

### CL6 — Session-scoped admission gate

**Objective.** Evaluate a candidate and admit it for the current run only. Admission is a gate **before** load.

**Admission requires all of:** well-formed; every conclusion variable premise-bound; satisfies all positive generated cases; violates no declared negative case; the wrong-variable decoy is distinguishable; a resulting proof passes CL2; scope is the current run; the safety floor reports no violation.

**Trust boundary:** `session admission ≠ durable promotion`. Admitted rules and schemas live in a scratch snapshot context; `packs/` is never written; a durable-promotion attempt must report that human authorisation is required.

**Acceptance.** Correct candidate → admitted; wrong-variable candidate → rejected; overbroad candidate that proves a negative case → rejected; activation before a decision is impossible; ablation disables it; a `packs/` write attempt is detected and fails the run.

---

### CL7 — Four-leg experiment harness + artifact manifest

One command shape (repository conventions may adjust names, not semantics):

```
python -m cat_theo_machine.experiments.closed_loop_experiment \
    --base-checkpoint <path> --fixture-seed <sealed> --artifact-dir <path> \
    --approval-policy auto-proceed
```

Artifacts: `manifest.txt`, `environment.txt`, `base.txt`, `fixture-digest.txt`, `control-{transcript,receipt}`, `treatment-{transcript,receipt}`, `checkpoint-receipt`, `replay-{transcript,receipt}`, `ablation-{transcript,receipt}`, `checker-a`, `checker-b`, `mutation-tests`, `baseline-suite`, `sha256.txt`.

**Acceptance.** One command runs all four legs; each leg has its own exit verdict; machine output is distinguishable from harness commentary; the manifest hashes every artifact; any failed conjunct yields a non-zero exit; **no artifact depends on uncommitted state** (measurement hygiene, §4).

---

### CL8 — Sealed induction (autonomy track)

**Objective.** The Machine — not a worker, not the fixture — produces `{start_pattern, goal_pattern, plan}` from training traces, via `graph.add_derivation_schema` (V7). This is the only genuinely research-risky task.

**Two mechanisms, built in isolation, each sealing independently:** `CL8A` anti-unification over trace pairs; `CL8B` template enumeration over the residual's missing-shape grammar. Either passing suffices; the grader reports which mechanism produced the sealed candidate.

**Seal.** Hash the candidate **before** the holdout is exposed (CL1 commit carries the holdout hash and the fixed search budget; both are sealed together). Sealing is the primary anti-gaming device; grep-for-constants and multi-instance breadth remain secondary.

**Trust boundary.** A schema is a **macro, not an axiom**: every use expands through `InstantiateDerivation` and must pass CL2 against pre-existing trusted rules. The schema never needs to be *true*, only admissible as compression.

**Ablation must be a release conjunct.** Under the sealed budget, holdout positives must fail **without** the candidate and pass **with** it. Without this, a useless-but-applicable candidate passes.

**Expander ownership.** The expander belongs to the evaluator (CL7), not to CL8, and gets its own mutation test: a deliberately corrupted expansion must be rejected by both checkers.

**Corpus.** If CL0 finds no eligible corpus, CL7 *generates* training traces by running the fixture family through the baseline prover with the bridging rule present, then stripping it — and the grader records `corpus_provenance: synthetic`. `STOP` is reserved for the case where trace generation itself fails.

---

### CL9 — Red team

Attacks (each: attack / expected / observed / artifact / classification / release-blocking yes-no): grep for fixture constants and for the sealed seed; mutate premise, conclusion, and shared-variable binding; submit the decoy and the overbroad teaching; activate without admission; restore under a foreign experiment id; replay against a different goal; demand success with teaching disabled; three repeats; interrupt after checkpoint write and test atomic recovery; verify neither checker imports search, `BuildDerivation`, `_apply_action`, or `_match_premises`; verify `packs/` is untouched at exit; verify a stray `input()` raises `InterventionError`.

Any unexplained successful attack blocks release.

---

### CL10 — Integration and release

Merge order: contract/label registration → selected checker → residual → replay → teaching → admission → induction → harness → red-team tests. Fetch exact SHAs, never moving tips.

**Gates after every semantic merge:** import/compile; changed-module probes; focused closed-loop suite; **bounded** baseline suite; `git status --porcelain` clean on tracked paths; fresh blank controls; frozen semantic tag. The **full** suite runs once as a background watchdog with incremental receipts (V14) — never as a per-merge gate.

Release tag: `ctm-val-6-<shortsha>`. Release report = **one page, machine-filled**.

---

### F1 — Persistence localisation and repair  *(on the critical path; from the dispatched baseline)*

**Objective.** Make the snapshot round trip preserve derivations, so cold replay is possible at all. Measured failing today: after fresh-process activation both restored derivation entries lack constructors and readers return `EmptyList`.

**Hypothesis to localise, not assume.** `SnapshotCodec._record_for` searches all namespace aliases before writing pair/edge/value structure, while `save_runtime` first synchronises a namespace containing `AllConstructors` — naming a mutable state root as if it were fixed vocabulary, so the importing process's registry can replace its contents on restore. Localise or refute; a different root cause is a valid outcome.

**Forbidden repairs.** Registering the missing constructors on load; removing or weakening the assertion; special-casing derivation entries. Those convert a broken codec into a hidden one.

**Acceptance.** `boot_from_packs → save_runtime → boot_from_snapshot` in a fresh interpreter yields identical `derivations` and `derivation_schemata`; `StepAction`/`ActionBindings`/`ActionPath` survive the round trip (required by CL2's cold-restore mutation); a regression test pins the failure; a before/after digest pair is recorded.

---

### CL-D — Decomposition probe  *(the swarm's chance to out-plan the planner)*

**Objective.** Produce a better DAG than §6, or evidence that §6 is already minimal.

**Procedure.** Two agents independently rewrite the DAG from §2's success conditions and §3's constraints **only** — they do not read §6, each other, or the audit in §6.1. Each delivers: every edge with the artifact it transfers, a dissolution verdict per edge, a revised critical path, and one new serial hazard the original missed. Deadline T+2, 45 min each.

**The deliverable is the disagreement.** Edges both rewrote identically are pruned. Edges they disagree on are adjudicated by INT against the test: *can the transferred artifact be stubbed, fixtured, or generated in isolation?* Adopted dissolutions are applied as a versioned re-scope before W2 — never after outcomes are seen.

**Acceptance.** Two independent plans on disk; a diff table of edges; at least one dissolution or addition adopted, or a written finding that the audit in §6.1 is already complete.

---

## §8 Fixture, acceptance matrix, and the causal protocol

**Fixture vehicle (V9):** a *generated* pack whose `examples` carry the start/goal pairs and whose `rules` entry for the bridging rule is present or absent per leg. Two-hop relational family: `R(a,b)`, `R(b,c)` ⊢ `S(a,c)` with the bridging rule `R(x,y) ∧ R(y,z) → S(x,z)`. Family must include ≥5 constant triples, ≥3 relation-name combinations, a repeated-variable join, a wrong-shared-variable decoy, a right-arity/wrong-conclusion decoy, an unrelated distractor fact, reordered facts, and one missing-premise negative. Seeds are generated at CL0, committed as a hash at CL1, and revealed after patches freeze.

| Run | Teaching rule | Expected proof | Checker | Terminal result |
|---|---:|---:|---:|---|
| Control | absent | no | n/a | concrete residual + dependency |
| Treatment | admitted | yes | both pass | success |
| Wrong-variable decoy | admitted attempt | no | n/a | rejected |
| Overbroad | admitted attempt | must not count | reject | rejected |
| Mutated derivation | n/a | stored proof altered | reject | verification failure |
| Cold replay | restored | yes | both pass | replay success |
| Ablation | disabled | no | n/a | original residual |
| Safety refusal | n/a | no | n/a | safety terminal (no retry) |
| Hidden-seed holdout | Machine-induced (CL8) | yes | both pass | induction success, sealed |

---

## §9 Grader and kill conditions

Report fields are **separate**; a script fills them; a human reads one page.

```
claim_profile: INTEGRATION_LOOP | AUTO_SCHEMA_INDUCTION | FOUNDATION_ONLY
integration_loop:            PASS | FAIL | BLOCKED
auto_schema_induction:       PASS | FAIL | BLOCKED | NOT_RUN
novelty:                     UNASSESSED
base_sha / release_sha
fixture_digest / holdout_digest / candidate_digest / corpus_provenance
checker_a / checker_b        (mutation matrix pass counts)
cold_replay
negative_controls / mutation_controls / ablation
baseline_failure_set / release_failure_set
red_team
packs_touched: false
intervention_events: 0
```

`INTEGRATION_LOOP: PASS` requires: all four legs verified; both checkers pass the mutation matrix including builder-semantics probe 9; zero intervention events with `auto-proceed`; cold replay reproduces verdicts; ablation restores the control residual; `packs/` untouched; bounded baseline failure set does not grow; every artifact traces to a pushed SHA.

`AUTO_SCHEMA_INDUCTION: PASS` additionally requires: CL0 returned `GO`; the candidate was produced by the Machine from traces; it was sealed before holdout exposure; the ablation conjunct holds under the sealed budget; corpus provenance recorded. An externally supplied candidate ⇒ `FAIL`.

**Kill conditions.** Control proves the goal · the target solution is present in source or packs · a checker imports search or the builder · a rule activates without an admission decision · the experiment needs a human choice after launch · legs differ in code · replay needs fallback registration · ablation still succeeds without a justified alternate proof · the bounded baseline failure set grows · the sealed seed changes runtime logic · a safety refusal is retried instead of terminating · the release cannot be reproduced from pushed SHAs · a leg leaves tracked files dirty.

---

## §10 Recovery, hygiene, and report envelope

- **Worker failure.** Preserve the failed attempt and its tests; dispatch a redundant implementation against the *same* contract version; the replacement may not reinterpret the interface. A failed implementation still contributes adversarial tests.
- **Interface mismatch.** `INT` writes a narrow adapter or returns the patch for contract correction. If two workers need incompatible term layouts, CL1 adjudicates before either merges.
- **Shared-file conflict.** Exclude both semantic patches; request minimal change proposals; `INT` applies one consolidated shared commit; workers rebase.
- **Sandbox reset.** Fetch the last pushed commit; compare tree SHA against the worker report; regenerate derived artifacts only. Never reconstruct unpushed semantic code from prose.
- **Unbounded suite.** If the watchdog suite exceeds its box, classify as `UNBOUNDED_BASELINE`, and gate on the bounded suite — stated explicitly in the report, never silently.
- **Performance failure.** Instrument the stalled phase. Do not raise timeouts unless logs show forward progress; the default search-worker timeout is `HYGE_SEARCH_WORKER_TIMEOUT=6000 s`, and changes to it are **sealed decisions** recorded in `DECISIONS`.

**Worker report envelope** (a report without a pushed commit, executable tests, and artifacts is not merge-ready):

```
TASK:            STATUS: ready|blocked|failed
BASE_SHA:        HEAD_SHA:        COMMITS:
FILES_TOUCHED:
SHARED_CHANGE_REQUESTS:
CONTRACT_VERSION:
TEST_COMMANDS:   TEST_RESULTS:   KNOWN_FAILURES:
ARTIFACTS:       (path + sha256)
SEMANTIC_CHANGE: yes|no
MERGE_ORDER_REQUIREMENT:
FAILURE_MODES:   BLOCKED_ON:
```

---

## §11 Schedule, dispatch order, human role

| Time | Work |
|---|---|
| 00:00–01:00 | **W0 fan-out**: CL0 (probes + baseline, pristine worktree), CL1 (seam), CL2A/B, CL3, CL5, CL7-sk, CL8A/B, CL9, CL-D — all in parallel. GO/RE-SCOPE/STOP issues by 01:00; only CL10 is gated on it |
| 00:45–02:00 | CL-D converges; dissolutions folded as a versioned re-scope |
| 01:00–04:00 | **F1 persistence repair** — the real critical path |
| 03:00–06:00 | CL4 replay: in-process now, cold half as soon as F1 lands |
| 04:00–06:30 | CL6 admission against stubs, then against frozen fixtures |
| 06:00–08:00 | CL7F wire real inputs; four legs |
| 07:00–11:00 | CL8 induction (off critical path) |
| 08:00–11:00 | CL9F final adversarial pass; targeted repairs |
| 11:00–13:00 | CL10 integration, watchdog suite, artifact freeze, one-page report |
| 13:00–16:00 | Buffer + M2 fallback hardening. **At T+14 if M4 is not reached, stop building and harden M1–M3 artifacts.** |

**Dispatch order.** W0 is a genuine fan-out: with the nine dissolved edges of §6.1, ten tasks can start at T+0, because none of them consumes another's artifact — they consume contracts and stubs. The two things that must *not* happen: no task may edit an integrator-only shared surface (§5), and no task may wait on another task when a stub would let it proceed. If a worker believes it is blocked, the required action is a `DependencyDissolution` record, not an idle turn. A swarm dispatched before the keystone produces eight incompatible diffs — that is the failure mode this chain has been circling; a swarm dispatched *with* the keystone and contracts is CL0+CL1 running concurrently with everything else.

**Human decisions — exactly three, all before launch, none during:**

1. **H1** Approve the system of record and the teaching-surface decision (§1).
2. **H2** Authorise the session-scoped admission profile (no `packs/` writes, no durable promotion).
3. **H3** Approve the environment pin, the measurement-hygiene rules, and the sealed seed/budget commit.

After launch the human does not choose a rule, repair state between legs, decide whether a checker failure is ignorable, or reinterpret a transcript.

---

## §12 The core test, final form

> **By midnight: the loop runs with nobody at the keyboard, and every proof step it produces is independently checked. It either induces a reusable schema from its own traces — under a seal it did not choose — or it hands back a machine-readable account of exactly why it could not.**

That is the version of "do the impossible" this repository can actually support in one day: not a bigger promise, but a day in which **every** outcome — pass, partial, or fail — is a checked artifact instead of an anecdote, and in which the one real blocker (a system that still asks a human whether it may continue) is finally gone.

---

## Appendix A — Critical path

`CL0 baseline ∥ CL1 seam → F1 persistence → CL4 cold replay → CL7F four-leg run → CL9F final adversarial → CL10 tag`
≈ **7–9 h**. Every other task starts at T+0 (see §6.1). The two items the previous draft placed on the critical path that do not belong there: **CL2** (never needed CL1) and **CL4/CL7 construction** (belongs at T+0 against stubs). The one item that does belong and was missing: **F1**.

## Appendix B — Parallel work packages

| Wave | Tasks (all may start together) | Gate to leave the wave |
|---|---|---|
| W0 (T+0) | CL0, CL1, CL2A, CL2B, CL3, CL5, CL7-sk, CL8A, CL8B, CL9, CL-D | CL0 issues GO / RE-SCOPE / STOP |
| W1 (T+2) | F1 | codec round-trips derivations in a fresh interpreter |
| W2 (T+4) | CL4 (in-process → cold after F1), CL6 (stub → frozen fixtures) | CL2 mutation matrix green incl. probe 9 |
| W3 (T+7) | CL7F wire real inputs | four legs each carry a verdict |
| W4 (T+9) | CL9F | no unexplained successful attack |
| W5 (T+12) | CL10 | bounded suite green, tree clean, tag cut |

`CL7-sk` = harness skeleton: CLI, leg isolation, manifest, hashing, exit codes — built and tested against stubs before any real component exists. This is the harness-first rule from round 2 of the spec chain, which the previous draft of this document ignored.

## Appendix C — Required interfaces

Workers build against these; nobody may change one without a `[SHARED]` change request through INT. Each is a machine-term mapping owned by CL1.

| Interface | Shape | Owner | Consumers |
|---|---|---|---|
| Step check | `StepCheck(derivation, trusted_rules, registry) → verdict`; verdicts `check-ok` / `reject-untrusted-rule` / `reject-premises-unsatisfied` / `reject-conclusion-mismatch` / `reject-binding-inconsistency` / `reject-broken-chain` / `reject-goal-mismatch` / `reject-empty` | CL2A/B (each independently) | CL6, CL7, CL8 |
| Residual | `PlannerObligation` + `PlannerDependency`; terminal class from `no-applicable-rule` / `applicable-rule-with-unmet-premise` / `binding-inconsistency` / `resource-exhaustion` / `malformed-goal` / `safety-refusal` | CL3 | CL4, CL6, CL7, CL8 |
| Candidate | rule `{"id","pattern","replacement"}` or schema `{"id","start","goal","plan"}`, compiled through `PackLoader` against a throwaway namespace | CL5 | CL6, CL7, CL8 |
| Admission | verdict vocabulary `admit-for-session` / `reject-malformed` / `reject-unbound-variable` / `reject-negative-control` / `reject-safety` / `requires-human-promotion`; gate sits **before load** | CL6 | CL7, CL8 |
| Batch agreement | digest of the frozen rule set both checkers must accept as trusted | F1 | CL2A/B, CL6, CL7 |
| Seal | `{candidate_digest, holdout_digest, budget, commit}` committed at CL1, revealed after patches freeze | CL7 | CL8, CL9, CL10 |
| Harness CLI | `python -m cat_theo_machine.experiments.closed_loop_experiment --base-checkpoint --fixture-seed --artifact-dir --approval-policy` | CL7 | CL10 |

## Appendix D — Acceptance tests (consolidated)

| Task | Key acceptance | Artifact that decides it |
|---|---|---|
| CL1 | `main cold` with stdin closed terminates and materialises a derivation; an injected prompt raises `InterventionError`; `interactive` behaviour byte-identical | before/after transcripts + focused test |
| CL2A/B | 10-row mutation matrix incl. **probe 9** (builder-accepted premise-unsatisfied derivation must be rejected) | checker verdict log per mutation |
| CL3 | five seeds → same structural class; order-insensitive; distractor-invariant; timeout ≠ missing mathematics | residual receipts |
| CL4 | save → terminate → fresh interpreter → same verdicts; no fallback registration | checkpoint digest + class manifest |
| CL5 | premise order invariant; wrong join compiles observably different; unbound variable rejected; byte-identical across two runs | compile receipts |
| CL6 | correct admitted, wrong-variable rejected, overbroad rejected, activation-before-decision impossible, `packs/` untouched | admission decisions + alert on `packs/` write |
| CL7 | one command, four legs, per-leg verdicts, manifest hashes every artifact, non-zero exit on any failed conjunct, no artifact from uncommitted state | artifact manifest + `sha256.txt` |
| CL8 | candidate sealed before holdout; holdout ablation conjunct holds under sealed budget | seal record + ablation receipts |
| CL9 | every attack classified; none unexplained-successful | red-team table |
| CL10 | bounded suite failure set does not grow; tree clean; tag reproduces | release report, one page |

## Appendix E — Integration procedure

`contract/label registration → selected checker → residual → F1 persistence → replay → teaching → admission → induction → harness → red-team tests`. Fetch exact SHAs, never moving tips. After every semantic merge: import/compile; changed-module probes; focused closed-loop suite; **bounded** baseline suite; `git status --porcelain` clean on tracked paths; fresh blank controls; frozen semantic tag. The full suite runs once as a background watchdog with incremental receipts — never as a per-merge gate. Release tag `ctm-val-6-<shortsha>`. Release report is machine-filled and one page.

## Appendix F — Biggest risks to the one-day objective

| # | Risk | Trigger | Mitigation fixed in advance |
|---|---|---|---|
| 1 | **F1 not repaired in time** | probe still fails at T+4 | CL4 reports `BLOCKED`, not `FAIL`; in-process replay counts toward M2; cold half explicitly deferred |
| 2 | **The `input()` seam is deeper than the three known sites** | `InterventionError` fires somewhere new | the hook is the detector; policy env-var generalises; each new site is a finding, not a blocker |
| 3 | **Checker independence collapses** | either checker fails mutation probe 9 | track cannot be released on that checker; the other stands alone; probe 9 is the sentinel, not the suite size |
| 4 | **Bounded suite is not actually bounded** | watchdog exceeds its box | gate on the bounded suite; classify `UNBOUNDED_BASELINE` explicitly; never silently |
| 5 | **Fixture cannot express the planted gap through pack `examples` + `rules`** | CL0 probe returns red | predeclared `RE-SCOPE: FOUNDATION_ONLY`; a silent weaker substitute is forbidden |
| 6 | **Agents fan out before the keystone** | more than CL0+CL1 dispatched first | dispatch order is binding; nine of thirteen edges are already dissolved, so the cost of waiting is lower than it looks |
| 7 | **Dirty tree invalidates legs** | `main cold` rewrites the tracked 18 MB snapshot | scratch snapshot dir + `git status` assertion per leg |
| 8 | **CL-D returns a better DAG at T+2** | plausible | allowed and wanted, but as a **versioned** re-scope before dispatch — never a post-outcome relabel of the claim |
| 9 | **Claim inflation** | anyone calls Track I discovery | grader fields are separate; external candidate ⇒ `AUTO_SCHEMA_INDUCTION: FAIL`; `novelty: UNASSESSED` |

The objective survives risks 1–4 and 6–8 as a partial, graded, honest day. Risks 5 and 9 are the two that can produce a dishonest one, and both are pre-empted by a rule rather than a judgement.

---

## Appendix G — Evidence log (commands run and what they showed)

| # | Command | Observed |
|---|---|---|
| 1 | `git log --oneline -5` | single commit `428ecdc "Add files via upload"`; no tags |
| 2 | `python3 -m cat_theo_machine.main --help` | `ModuleNotFoundError: gmpy2` at `machine.py:34 ← gmprep.py:3` |
| 3 | `pip install gmpy2 pyyaml` then `--help` | usage printed: modes `cold · warm · test · inspect · search-worker` |
| 4 | `python3 -m cat_theo_machine.main cold` (stdin closed) | packs load 23.60 s → `rule_count 159 / schema_count 4 / example_count 27` across 12 packs → "SearchBFS found a plan" → **blocked on prompt**, killed at 200 s |
| 5 | `git status --short` after the cold run | `M snapshots/hyge_snapshot_v8.json` (tracked, 18 MB) |
| 6 | `grep -rn "found a plan"` | `search/compare_subprocess.py:248` prompt + `input()`; `:236` console-off ⇒ replay *deferred* |
| 7 | `grep -rn "Residual\|DependencyRequest\|TeachingCandidate\|AdmissionDecision\|ProofReceipt" --include=*.py .` | exactly one unrelated hit (`labels.py:282 ResidualHeadBucketLabel`); none of the chain's constructs exist |
| 8 | `grep -rn "CheckDerivation\|VerifyDerivation\|ReplayDerivation"` | no matches; only `_derivation_reaches_goal` (`proof.py:1126`) and its twin (`search/compare_rules.py:153`) |
| 9 | `sed -n '1814,1875p' proof.py` | `Step(current, action, next_term)`, `StepAction`/`StepRule`, `ActionRule`/`ActionBindings`/`ActionPath` |
| 10 | `sed -n '2536,2556p' proof.py` | `BuildDerivation._build` → `self._apply_action(...)` ⇒ checker must avoid it (independence trap) |
| 11 | `sed -n '420,433p' persistence.py` | `ROOT_NAMES` = constructor_registry, all_rules, rule_order, derivations, derivation_schemata, search_history, search_comparisons, search_comparison_jobs, search_jobs, search_memo, nat_value_index |
| 12 | `sed -n '173,190p' graph.py`; `search/engine.py:2093` | `add/lookup_derivation_schema` exist; engine consults schemata and validates only `_derivation_reaches_goal` |
| 13 | `python3 hyge.py` | **runs**: sieve + trial over 1..9, `sqrt-divisor-bound` cited, agreement line printed; `hyge.py` has zero imports |
| 14 | `python3 cat_theo_machine/validation/test1_planner_minimal.py` | `ImportError: cannot import name 'machine' from 'hyge'` — `hyge.py` shadows the former package; all four `validation/` scripts are dead |
| 15 | `python3 -m cat_theo_machine.main test` | pack boot completes in ~24 s; **no incremental output**; still running at 100 % CPU after 35 min; killed |
| 16 | `sed -n '377,410p' main.py` | `_theorem_agenda` maps `pack.examples` → provable cases (the fixture vehicle) |
| 17 | `yaml.safe_load('packs/order-sign.pack.yaml')` | `rules: [{id, pattern:{sym}, replacement:{call:…}}]`; `sqrt-real` also carries `schemas: [{id,start,goal,plan}]` |
| 18 | `sed -n '515,530p' planner.py` | `PlannerDependency`, `PlannerJob`, `PlannerAlternative*`, `PlannerObligation` exist (R1 mandate) |
| 19 | `sed -n '305,315p' core.py` | `__all__` names `IsPairCell`; the class is `IsPair` — latent star-import bug; **record only, do not fix mid-sprint** |

## Appendix H — Claim ledger: rounds 1–5 vs. measured reality

| Claim | Round | Verdict |
|---|---|---|
| "Active lineage has a session loop; persistence works" | ODR-1 | **Partly true** for lineage A's codec; **false** for the loop (blocked by `input()`) |
| "`session.txt` … taught through generic readers" | ODR-2 | **True**, but of lineage B (`hyge.py`), which is unconnected to A |
| "Persistence issues with character symbols / base `Edge`" | ODR-4 | Open probe; the codec's symbol table is `SNAPSHOT_SYMBOL_NAMES` (`persistence.py:437`), round trip must be probed (CL0) |
| "Induction belongs to later gates; runtime/persistence must be trusted first" | ODR-4 | **Correct and confirmed** — schemata exist, but no producer and no checker |
| "Seal-before-holdout" | ODR-5 | **Adopt verbatim** — the cleanest anti-gaming device in the chain |
| "Macro, not axiom" | ODR-5 | **Adopt verbatim** — and it is what the code already does (`InstantiateDerivation` + goal check) |
| "Dual checker as a release conjunct" | ODR-5 | **Adopt**, strengthened by mutation 9 (builder-semantics probe) |
| "Full sharded suite after every merge" | ODR-1/2 | **Refuted** — no test sharding; suite unbounded (V14) |
| "Integrator picks the seed after patches freeze" | ODR-1 | **Refuted/dangerous** — seed committed as a hash at CL1, revealed after freeze |
| "Paths `session.py`, `wire.py`, `tools/`, `protocol/`" | ODR-1 | **Absent from base `428ecdc`, present on the carrier branches.** `session.py`, `wire.py`, `vocabulary.py`, `verbalizer.py`, `language.py`, `nl_parser.py`, `protocol/`, `researcher_v0/`, `training_records/` all exist on `origin/arena/01a0eca3`. My earlier "do not exist" was a fact about my branch, not the repository — see `CTM-ODR-7.md` §0 |

## Appendix I — Open probes CL0 must close (nobody has verified these)

1. The exact minimal call path that adds a rule + rule chain to a **booted** graph without touching `packs/` (the admission seam).
2. Whether a generated pack's `examples` + `rules` can express the two-hop fixture with a *missing* bridging rule such that control fails deterministically and treatment proves (V9 is verified for format, not for this case).
3. The snapshot round trip for `derivations` and `derivation_schemata` in a fresh interpreter (V8 root list is verified; behaviour is not).
4. Whether planner state can be persisted for the residual (V8 says planner is absent from `ROOT_NAMES`).
5. The real bounded-baseline cost: a named subset plus `HYGE_SEARCH_WORKER_TIMEOUT` capped, measured; the full suite's true completion time on a machine that can give it one.
6. Whether `StepAction` survives the codec round trip with `ActionBindings` and `ActionPath` intact — required for CL2's cold-restore mutation case.
7. The environment delta's effect: Python 3.11.2 vs pinned 3.12.13, `gmpy2` 2.3.1 vs 2.3.0.

---

*Dispatch this one. Ground every claim in a command you ran.*
