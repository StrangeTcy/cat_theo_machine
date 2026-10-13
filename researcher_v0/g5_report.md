# Researcher-v0 — G5 In-run use gate report

Status: **G5 complete.** Proved invariants are now eligible for use on later tasks inside the Researcher-v0 run. Every use is exact-scope, endpoint-bound, independently replayed, and recorded. Candidate-only and trace-only material has no route to pruning.

## 1. Run identity

```text
agent:          Researcher-v0
branch:         arena/01a0eca3-cat-theo-machine
base:           9b42cc17560e0d6bec27b67030e4301cbe1715c2
condition:      MINING with in-run proved-invariant use
mining cadence: structural K = 5; sweeps 5,10,15,20,25,30,34
budget:         32 expansions and 60000 ms per task
workers:        1
canonical tasks: 34 from 42 delivered rows
task binding:   b89ac1f5742ea7bbb03bffa59fc10efab7a4ab27b522edbc014d3448882ec90c
pruning scope:  Researcher-v0 run only
live activation: none
```

The runner regenerated the G2 corpus and required exact machine comparison with `researcher_v0/tasks/tasks.jsonl` before running. All G0–G4 files remain unchanged.

## 2. Files added

| File | Purpose |
|---|---|
| `researcher_v0/use_checker.py` | exact-scope invariant replay for use; two-sided endpoint reading guard; endpoint certificate minting and replay; proved-certificate-only use interface |
| `researcher_v0/in_run_use.py` | G5 attempt loop, structural mining cadence, later-task pruning, scope audit chain, prune event rendering |
| `researcher_v0/run_g5_use.py` | bound G5 runner and required artifact writer |
| `researcher_v0/certificates/prune_events.jsonl` | eight required prune event records with endpoint certificates and replay evidence |
| `researcher_v0/tests/test_g5_use.py` | 17 executable G5 acceptance tests |
| `researcher_v0/tests/run_g5_tests.py` | recursive structural test runner |
| `researcher_v0/g5_report.md` | this report |

## 3. In-run use procedure

For each canonical task in delivered order:

1. inspect only the proved-invariant archive accumulated by earlier mining sweeps;
2. recompute the task’s exact ruleset digest before any endpoint comparison;
3. return `SCOPE_MISMATCH` for a certificate from any other digest;
4. independently recompute preservation for every exact rule;
5. verify the preservation verdict names the requested observer and exact digest;
6. require `PhiHolds` and non-missing `PhiReading` on both start and goal;
7. require the two present readings to separate;
8. mint an endpoint certificate bound to observer, start, goal, digest, checker version, parent invariant certificate, preservation evidence, and both readings;
9. replay that endpoint certificate from the task’s exact rules and endpoints;
10. issue `CHECKED_UNREACHABLE` at zero expansions only after `REPLAYED`;
11. otherwise execute the unchanged G3 attempt path.

After every five completed tasks, INV-0 runs over the completed prefix exactly as at G4. Newly proved certificates become eligible only for subsequent tasks. T0003 and T0005 therefore remain `BUDGET_EXHAUSTED`; proofs discovered after task 5 are not applied retroactively.

The use checker accepts a chain of proved-invariant archive records. Candidate and `BrokenOn` archives are absent from its interface. An empty proved archive cannot prune even when candidate records exist.

## 4. Semantic replay across equivalent rule instances

The exact scope key remains the G1 ruleset content digest. G5 does not compare display labels or runtime variable identities as semantic evidence. For each rule digest, replay compares:

- the exact per-rule content digest;
- preservation status;
- canonical premise-side observer reading;
- canonical replacement-side observer reading.

It checks both recorded-to-recomputed and recomputed-to-recorded coverage. This preserves A1.2/A2.2: display-only renaming and newly allocated rule variables do not invalidate the same content version, while any body change changes the digest and fails at scope first.

## 5. Outcomes

```text
attempts              34
CHECKED_REACHABLE     21
CHECKED_UNREACHABLE    8
BUDGET_EXHAUSTED       3
UNSUPPORTED            2
OPEN_RESIDUAL          0
EXECUTION_FAILURE      0
total expansions     137
```

G4 used 361 expansions. G5 uses 137, a reduction of 224 expansions. Seven formerly exhausted search tasks are stopped before search, each with a saved estimate of 32. T0046 previously ended `UNSUPPORTED` at zero expansions, so its saved estimate is correctly 0 even though G5 now proves it unreachable.

## 6. Prune events

| Task | Exact ruleset | Start reading | Goal reading | Saved estimate |
|---|---|---|---|---:|
| T0013 | R_even | Even | Odd | 32 |
| T0020 | R_even-minus-Remove2 | Even | Odd | 32 |
| T0023 | R_even | Odd | Even | 32 |
| T0029 | R_even | Even | Odd | 32 |
| T0030 | R_even-minus-Remove2 | Even | Odd | 32 |
| T0033 | R_even | Even | Odd | 32 |
| T0038 | R_even | Even | Odd | 32 |
| T0046 | R_even-minus-Remove2 | Even | Odd | 0 |

Every event records all required fields:

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

The artifact additionally records canonical task id, parent invariant certificate id, ruleset version, checker version, exact per-rule preservation evidence, and endpoint replay result/reason. All eight endpoint certificates replay successfully.

## 7. Scope behavior

The run records 62 certificate/task scope checks internally. In particular, the R_even certificate tested against R_plus at T0011 returns `SCOPE_MISMATCH` before endpoint comparison. No R_plus task is pruned because Add1Even and Add1Odd refute parity preservation and G4 produced no proved R_plus parity certificate.

The scope-break tail demonstrates both sides of the rule:

- T0043, current scope R_plus: old R_even proof mismatches; no exact proved separating certificate; remains `UNSUPPORTED`.
- T0045, current scope R_even-minus-Swap: an exact proved certificate exists, but endpoint parity is the same; remains `UNSUPPORTED`.
- T0046, current scope R_even-minus-Remove2: the old R_even certificate mismatches, but the independently proved certificate for the exact new digest exists and its endpoint readings separate; result `CHECKED_UNREACHABLE`.

Thus a changed ruleset never inherits authority from the old certificate, while a separately proved certificate for the exact new content may be used.

## 8. A2.1 replay evidence

An endpoint certificate is accepted only after replay verifies, in order:

1. exact task/certificate ruleset digest;
2. endpoint-certificate kind, observer, start, goal, and checker version;
3. cited invariant certificate under exact semantic preservation replay;
4. fresh `CheckObserverPreservation` across every rule;
5. requested observer and digest in that verdict;
6. equivalence of complete semantic preservation evidence;
7. both endpoint readings present;
8. readings separate;
9. recorded readings equal recomputed readings.

A missing goal reading returns `NOT_CHECKED`. A same reading returns `NOT_CHECKED`. A changed endpoint binding returns `REPLAY_FAILED`. None can become `CHECKED_UNREACHABLE`.

## 9. Artifact

```text
researcher_v0/certificates/prune_events.jsonl
lines: 8
JSON Lines parse: success
all results: CHECKED_UNREACHABLE
all endpoint replays: REPLAYED
```

The renderer is deterministic; the G5 test run reproduces the written file byte for byte. G4’s candidate, proved, and refuted archives also reproduce byte for byte from the G5 mining state, showing that in-run use did not rewrite prior-gate evidence.

## 10. Tests

```text
run_g5_use
  completed=34
  expansions=137
  checked_reachable=21
  checked_unreachable=8
  budget=3
  unsupported=2
  candidates=3
  proved=3
  prune_events=8

run_g5_tests  passed: 17  failed: 0
run_g4_tests  passed: 16  failed: 0
run_g3_tests  passed: 17  failed: 0
run_g2_tests  passed: 16  failed: 0
run_g1_tests  passed: 23  failed: 0
```

The G5 suite checks representative order and budget, cadence, exact event order, outcome and expansion totals, replay of every parent and endpoint certificate, expansion estimates, R_plus scope mismatch, zero R_plus pruning, candidate-only refusal, trace-only refusal, no retroactive use, same-reading refusal, missing-reading refusal, endpoint tamper failure, exact new scope at the scope-break tail, G4 artifact preservation, and prune artifact reproduction.

## 11. Constraint verification

The G5-only scans have no hits for module-level functions, reflection, direct `core`, Programme C/L imports, monkeypatching, direct hashing, line comments, Python container construction, host boolean literals, `while`, direct comparison operators, or host text search/transformation.

The required package-wide greps were rerun. Hits are confined to standing documentation and prior-gate prose; no G5 code imports or modifies protected systems.

```text
core.py                         untouched
Programme C                     untouched and not imported
Programme L                     untouched and not imported
live graph / search             not imported
admission / activation / rent   not called
live knowledge                  not written
prior-gate files                unmodified
tags                            unmodified
monkeypatching                  none
activation outside v0           none
```

## 12. G6 handoff

G6 may now build the inert discovery graph. It has concrete ids for tasks, attempts, transition counterexamples, candidates, proved invariant certificates, eight endpoint certificates/prune events, and recorded scope mismatches. G6 must cite these artifacts rather than recomputing or activating them.
