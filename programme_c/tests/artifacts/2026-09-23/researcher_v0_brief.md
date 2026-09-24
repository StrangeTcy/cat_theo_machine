# Recording wrapper (not part of the brief)

- source: gpt 5.5 brief text, pasted by operator verbatim
- recorded: 2026-09-24 by arena agent
- branch: arena/01a0352a-cat-theo-machine
- HEAD at record time: e724177
- status: specification only — no code, no tag move, no activation

---

# MACHINE RESEARCHER v0 — inert overnight research worker

**Status:** specification only.
**Purpose:** prove the Machine can perform bounded, checked research work overnight without admission, activation, or live-knowledge mutation.
**Target:** Engel-style invariance / reachability microdomain, not theorem packs.
**Output:** inert discovery archive + report.
**Forbidden:** activation, rent, human approval, live knowledge writes, Programme L, FLT route, prime route.

---

## 0. Standing constraints

```text
You are Agent Researcher-v0.
You implement an inert overnight research worker.

Do not modify core.py.
Do not modify Programme L.
Do not touch admission, activation, human approval, or rent.
Do not move tags.
Do not write to accepted knowledge.
Do not integrate INV-0 certificates into live search.
Do not revive prime(seven) route.
Do not run theorem packs.
Do not run Experiment 4.
Do not explain FLT.
```

All produced material is inert:

```text
researcher_v0/
  tasks/
  journals/
  certificates/
  candidates/
  reports/
  discovery_graph.json
```

No output may feed search unless explicitly passed inside the same inert v0 run.

---

## 1. Base and branch

Use the current session branch unless explicitly told otherwise.

Record:

```text
branch
HEAD
base SHA
Python version
gmpy2 version
PYTHONPATH
wall-clock budget
max_workers
random seed / deterministic seed
```

If any dependency is missing, halt and report. Do not silently switch environments.

---

# GATES

## G0 — Inspection / reuse gate

Before implementation, record the exact reusable pieces:

| Needed component | Expected source |
|---|---|
| cold worker execution | `BoundedWorkerPool` or local equivalent |
| certificate replay | `cert_replay` where usable |
| typed outcomes | existing atoms or experiment-local labels |
| journal format | Programme C journal if portable; otherwise v0-local JSON |
| INV-0 miner/checker | `invariant_experiment.py` or equivalent |
| Peano/token-world rules | INV-0 substrate |

If Programme C journal classes are not cleanly importable on this branch, use a **v0-local inert journal**. Do not widen scope to repair Programme C.

Deliver:

```text
researcher_v0/inspection.md
```

---

## G1 — Domain gate

Implement or reuse a tiny Engel-style reachability domain.

Required world:

```text
State:
  finite token count or two-color token count

Ruleset R_even:
  Add2
  Remove2
  Swap / identity

Ruleset R_plus:
  Add1 added as perturbation / scope breaker
```

Optional extensions if time remains:

```text
two token colors
move one token between colors
add/remove two of one color
```

State must be structural Peano or existing INV-0 terms, not Python integers as the semantic state. Python integers may be used only for reporting counts.

Deliver tests:

```text
construct Zero, One, Two, Three
apply Add2
apply Remove2 where legal
illegal Remove2 recorded as miss, not crash
```

---

## G2 — Task generation gate

Generate a task set from seeds.

Task kinds:

```text
reachability(start, goal, ruleset_version)
perturbed_reachability(start, goal, changed_rule)
scope_break_test(old_certificate, new_ruleset)
```

Perturbations:

```text
change goal by +1
change goal by +2
remove a rule
add Add1
rename display labels
```

Canonicalization:

- alpha-renamed/display-renamed tasks collapse to the same canonical id;
- exact duplicates are dropped;
- each task records parent task and perturbation reason.

Required minimum:

```text
at least 30 generated tasks
at least 10 non-isomorphic canonical tasks
```

Deliver:

```text
researcher_v0/tasks/tasks.jsonl
researcher_v0/tasks/canonicalization_report.md
```

---

## G3 — Laboratory execution gate

Run two conditions with the same generated task set and budget:

```text
BASELINE: mining OFF
MINING:   mining ON
```

Each task execution records:

```text
task_id
ruleset_version
start
goal
worker_id / attempt_id
outcome:
  CHECKED_REACHABLE
  CHECKED_UNREACHABLE
  OPEN_RESIDUAL
  UNSUPPORTED
  BUDGET_EXHAUSTED
  EXECUTION_FAILURE
expansions
elapsed_ms
certificate_id if any
counterexample_id if any
```

Required:

- every certificate is replayed or checked by the experiment checker;
- timeout is not a counterexample;
- crash is not refutation;
- unsupported is distinct from budget exhaustion.

Deliver:

```text
researcher_v0/journals/baseline.jsonl
researcher_v0/journals/mining.jsonl
```

---

## G4 — Mining gate

Every K completed tasks in the MINING condition, run the INV-0-style miner over the run’s journal.

Observer grammar is supplied and must be declared:

```text
Length
Parity(Length)
optional:
  CountColor(A)
  CountColor(B)
  Parity(CountColor(A))
  Difference(CountColor(A), CountColor(B))
```

For each observer:

```text
if broken:
  retain BrokenOn transition/counterexample
if survives traces:
  emit CandidateInvariant(observer, ruleset_version)
```

Then run the independent checker:

```text
∀ rule in ruleset_version:
  prove observer is preserved
or return UNSUPPORTED / REFUTED with reason
```

Only **proved** invariants may be used for pruning inside the same MINING run.

Deliver:

```text
researcher_v0/candidates/candidates.jsonl
researcher_v0/candidates/proved_invariants.jsonl
researcher_v0/candidates/refuted_candidates.jsonl
```

---

## G5 — In-run use gate

If an invariant is proved, it may prune later tasks **inside v0 only**.

Record every use:

```text
prune_event_id
task_id
certificate_id
observer
start_value
goal_value
result = CHECKED_UNREACHABLE
expansions_saved_estimate
```

Requirements:

- certificate ruleset version must equal task ruleset version;
- if ruleset changes (`R_plus`), old certificate returns `ScopeMismatch`;
- no pruning on mismatched scope;
- no pruning from candidate-only or trace-only invariants.

Deliver:

```text
researcher_v0/certificates/prune_events.jsonl
```

---

## G6 — Discovery graph gate

Build an inert discovery graph tying together:

```text
task generated from parent
task produced journal outcome
transition broke candidate
candidate proved by checker
certificate pruned later task
ruleset change invalidated certificate
```

Format can be JSON for v0, but every edge must cite source artifact ids.

Minimum node kinds:

```text
Task
Attempt
Transition
Outcome
CandidateInvariant
BrokenOn
Certificate
PruneEvent
ScopeMismatch
```

Minimum edge kinds:

```text
generated_from
attempted
produced
broke
proposed_from
proved_by
used_by
invalidated_by
```

Deliver:

```text
researcher_v0/discovery_graph.json
researcher_v0/discovery_graph_summary.md
```

---

## G7 — Evaluation gate

Compare BASELINE vs MINING.

Metrics:

```text
tasks_completed_checked
tasks_refuted_checked
tasks_unresolved
total_expansions
median_expansions
elapsed_ms_total
invariants_proposed
invariants_proved
invariants_used
prune_events
estimated_expansions_saved
false_prune_count  # must be zero
scope_mismatch_count
```

Success criterion:

```text
MINING proves at least one invariant
MINING uses at least one proved invariant
MINING completes or refutes at least one task with fewer expansions than BASELINE
all report claims trace to certificates/counterexamples/journals
no output is activated or admitted
```

If MINING does not beat BASELINE, the run is still valid; report it as a negative result.

Deliver:

```text
researcher_v0/reports/morning_report.md
researcher_v0/reports/metrics.json
```

---

# Acceptance tests

At minimum:

1. Baseline and mining use the same canonical task set.
2. Display renaming does not create new canonical task id.
3. Timeout does not create `BrokenOn`.
4. Length is broken by Add2/Remove2 traces.
5. Parity is proposed and proved for R_even.
6. Parity prunes at least one odd/even mismatch task.
7. Adding Add1 invalidates parity certificate.
8. Scope mismatch prevents pruning under R_plus.
9. Discovery graph has source ids for every reported claim.
10. No live admission/activation/rent/human hook called.
11. No files outside `researcher_v0/` and test harness touched, unless explicitly listed.

---

# Morning report required structure

```text
# Researcher-v0 Morning Report

## Run identity
branch, HEAD, budget, workers, seed

## Executive result
Did mining improve checked work? yes/no

## Task set
generated, canonical, dropped as duplicates

## Outcomes
baseline table
mining table

## Mined candidates
proposed
refuted with counterexamples
proved with certificates
unsupported

## Invariant use
where pruning happened
expansions saved
scope checks

## Discovery graph highlights
what unlocked what

## Negative findings
timeouts
unsupported observers
failed candidates
scope mismatches

## Integrity
no activation
no admitted knowledge
no rent/human
all claims trace to artifacts

## Next bounded item
one sentence only
```

---

# What not to do

Do not:

- attempt theorem packs;
- attempt FLT;
- route `prime(seven)`;
- install a discovered invariant into live search;
- use Programme C admission;
- use rent;
- use human approval;
- write a new general graph substrate;
- build a prose/story track;
- declare self-improvement achieved if mining only proposes but never uses an invariant.

---

# First-pass success definition

The run is a success if, by morning, this sentence is true:

```text
On the same generated task set and budget, mining-on produced at least one
proved scoped invariant and used it to reduce checked search work, with every
claim traceable to inert artifacts and no live activation.
```

That is the smallest honest version of “the Machine worked while I slept.”

---

## Suggested filename

```text
programme_c/tests/artifacts/2026-09-23/researcher_v0_brief.md
```

Commit only the brief if you want a planning artifact. If an agent implements it, use a new branch and report:

```text
agent: Researcher-v0
branch:
base:
budget:
tests:
artifacts:
baseline vs mining:
proved invariants:
prune events:
live activation: none
ready for next: yes/no
```
