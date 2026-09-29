# Researcher-v0 — G4 Mining gate report

Status: **G4 complete.** MINING ran over the same delivered 34 canonical ids and the G3 budgets. INV-0 mined two supplied observer forms at a fixed five-task cadence, retained concrete `BrokenOn` witnesses, emitted trace survivors as candidates, and passed each proposal through a separate exact-ruleset preservation checker. No G4 candidate or proof was supplied to search and nothing was pruned.

## 1. Run identity

```text
agent:          Researcher-v0
branch:         arena/01a0eca3-cat-theo-machine
base:           2229fac15944161483a1ababd116c0b0e1b3f026
condition:      MINING
mining cadence: K = 5 completed tasks; final remainder also swept
sweeps:         5, 10, 15, 20, 25, 30, 34
pruning:        off
budget:         32 expansions and 60000 ms per task
workers:        1 (worker-0)
tasks:          42 delivered rows, 34 canonical representatives
binding:        b89ac1f5742ea7bbb03bffa59fc10efab7a4ab27b522edbc014d3448882ec90c
Python:         3.11.2
runtime:        /home/user/.venv (gmpy2 2.3.1)
live activation: none
```

The runner regenerated G2 and required exact machine comparison with the delivered `researcher_v0/tasks/tasks.jsonl` before execution. The recorded task-set binding is the binding already established by G3. Prior-gate files were not edited.

## 2. Files added

| File | Purpose |
|---|---|
| `researcher_v0/mining.py` | supplied observer grammar; journal-derived legal transition corpus; `BrokenOn`; `CandidateInvariant`; structural five-task cadence; no-pruning run record; JSONL renderers |
| `researcher_v0/mining_checker.py` | independent exact-ruleset preservation checker; two-sided rule readings; proved/refuted/unsupported classification; invariant certificate and replay |
| `researcher_v0/run_g4_mining.py` | bound G4 runner and four required outputs |
| `researcher_v0/journals/mining.jsonl` | MINING header, 34 attempts, footer |
| `researcher_v0/candidates/candidates.jsonl` | three trace-surviving `CandidateInvariant` records |
| `researcher_v0/candidates/proved_invariants.jsonl` | three replayed proved-invariant certificates with per-rule evidence |
| `researcher_v0/candidates/refuted_candidates.jsonl` | five refuted observer/ruleset proposals with concrete transitions and independent rule checks |
| `researcher_v0/tests/test_g4_mining.py` | 16 executable G4 acceptance tests |
| `researcher_v0/tests/run_g4_tests.py` | recursive structural test runner |
| `researcher_v0/g4_report.md` | this bounded report |

No direct `hashlib` import was introduced. Candidate, counterexample, and invariant-certificate names are built from already-bound observer/ruleset/rule/task identities. The G4 implementation introduces no module-level function, Python container, reflection, monkeypatching, host boolean literal, `while`, line comment, or direct host comparison/search in machine semantics. Cadence and semantic trace counts are structural chains or structural Peano numerals.

## 3. Operational MINING procedure

1. Attempt the 34 canonical representatives in delivered order with the unchanged G3 attempt executor, 32 expansions, 60000 ms, and one worker.
2. Keep only the G3 path archive available to subsequent attempts. Candidate and invariant archives do not enter task execution.
3. Advance a structural five-tick cadence after each completed attempt.
4. At each cadence boundary, and at the final 34-task remainder, reconstruct legal outgoing transitions from each completed task's delivered start and goal by calling the exact G1 rule applier.
5. Evaluate the supplied grammar on both transition endpoints.
6. Retain the first concrete `BrokenOn` transition if present readings differ.
7. Emit `CandidateInvariant(observer, ruleset_version)` only when every observed transition for that exact digest has present, equal readings.
8. Independently run the preservation checker over every exact rule, without trusting trace survival.
9. Archive proved, refuted, or unsupported classification with reasons and per-rule evidence.
10. Retain proved certificates for G5; do not activate them in G4.

Each sweep runs when its fifth task has completed. Because the proof archives are held apart from the path archive passed to search, mining cannot change later G4 task outcomes or expansions.

## 4. Supplied observer grammar

| Observer | Machine reading |
|---|---|
| `Length` | `Tokens(k)`, the structural pair-count fact |
| `Parity(Length)` | `Parity(p)`, the carried parity fact |

The corpus contains four exact ruleset versions:

| Recipe | Digest | Rules |
|---|---|---|
| `R_even` | `15f5467c985c4dd9710e87b59b69788f3e2b23fb25f5320015589da844d2d68f` | Add2, Remove2, Swap |
| `R_even-minus-Remove2` | `0b2a31f486b5fe4bd192aa4f3a00170e28af695abddc07fe11fee5e279e99bb3` | Add2, Swap |
| `R_even-minus-Swap` | `8fb3494f9388b1984c58a06a3acecda2d5c5d4151a365399320fb3a192675a9e` | Add2, Remove2 |
| `R_plus` | `533cb46bd134cd0c1bcaf87d03ba6b4a1a5395c331f1ba0f391921ed500d2b8d` | Add2, Remove2, Swap, Add1Even, Add1Odd |

## 5. Search results

The G4 search outcome multiset and expansion total exactly match G3 BASELINE:

```text
attempts              34
CHECKED_REACHABLE     21
BUDGET_EXHAUSTED      10
UNSUPPORTED            3
OPEN_RESIDUAL          0
EXECUTION_FAILURE      0
path certificates     21
total expansions     361
```

The three scope-break rows remain `UNSUPPORTED`. Their mining proofs are not inserted into the G4 search archive. The MINING journal records that the proved archives are retained for G5 and were not supplied to the attempts.

## 6. Mining and checking results

Eight observer/ruleset proposals were assessed: two observer forms against four exact ruleset versions.

```text
CandidateInvariant emitted     3
proved                          3
refuted                         5
unsupported                     0 in the delivered run
```

Unsupported is still a real checker classification, not a synonym for refutation: the tests use an observer absent from exact rule bodies and require `UNSUPPORTED` because its two readings are missing.

### Proved

`Parity(Length)` survived traces and was independently proved for:

| Ruleset | First sweep | Observed transitions | Rules independently checked |
|---|---:|---:|---:|
| `R_even` | 5 | 26 | 3 |
| `R_even-minus-Remove2` | 10 | 4 | 2 |
| `R_even-minus-Swap` | 15 | 3 | 2 |

For every exact rule, the checker records rule digest, display, pre-reading, post-reading, `PRESERVED`, and reason. Every certificate was immediately replayed by recomputing fingerprint, observer, and all per-rule preservation steps; all three archive records say `REPLAYED`.

### Refuted

`Length` was refuted for all four ruleset versions. Each retained witness is an applied Add2 transition whose `Tokens` readings differ; the archive also independently records which exact rules preserve or refute that observer.

`Parity(Length)` was refuted for `R_plus`. Its retained witness is the T0011 Add1Even transition from `Parity(Even)` to `Parity(Odd)`. Independent checking evaluates all five rules: Add2, Remove2, and Swap preserve; Add1Even and Add1Odd refute.

Thus trace survival is never presented as proof, and trace breakage is never discarded.

## 7. Independent checker and A2.1 order

`mining_checker.CheckObserverPreservation` is not called by the trace miner to decide survival. It receives only the observer pattern and exact spec chain, then:

1. recomputes the ruleset digest;
2. constructs a preservation step for every exact rule body;
3. obtains premise-side and replacement-side `PhiReading` values;
4. classifies a missing side as `UNSUPPORTED`;
5. calls `invariance.Preserves` on that exact rule;
6. classifies present differing readings as `REFUTED`;
7. requires every step to be `PRESERVED` before minting a certificate.

Invariant replay checks the exact ruleset digest first. A mismatch returns `SCOPE_MISMATCH` before observer or evidence comparison. It then checks kind, observer, empty task-independent endpoint slots, checker version, recomputes every preservation step, and compares the recorded evidence. Tampered evidence fails replay in the acceptance suite.

The proved certificate binds kind `proved-invariant`, the observer pattern, exact ruleset digest, checker version, and complete per-rule evidence. Task endpoint reading/separation and checked unreachability remain G5 work.

## 8. Artifacts

| Artifact | Lines | Binding/result |
|---|---:|---|
| `journals/mining.jsonl` | 36 | header + 34 attempts + footer; MINING on, pruning off, K=5 |
| `candidates/candidates.jsonl` | 3 | all `Parity(Length)`, all finally proved |
| `candidates/proved_invariants.jsonl` | 3 | exact per-rule preservation evidence; all replayed |
| `candidates/refuted_candidates.jsonl` | 5 | four Length refutations and one R_plus parity refutation; every record retains a `BrokenOn` witness |

All four files parse as JSON Lines. The attempt journal gives the first retained counterexample id to its source task while the full transition, readings, checker classification, and per-rule reasons live in the refutation archive.

## 9. Tests

Commands and final results:

```text
cd /home/user
PYTHONPATH=/home/user /home/user/.venv/bin/python \
  -m cat_theo_machine.researcher_v0.run_g4_mining
  completed=34; expansions=361; candidates=3; proved=3; refuted_or_unsupported=5

PYTHONPATH=/home/user /home/user/.venv/bin/python \
  -m cat_theo_machine.researcher_v0.tests.run_g4_tests
  passed: 16  failed: 0

PYTHONPATH=/home/user /home/user/.venv/bin/python \
  -m cat_theo_machine.researcher_v0.tests.run_g1_tests
  passed: 23  failed: 0

PYTHONPATH=/home/user /home/user/.venv/bin/python \
  -m cat_theo_machine.researcher_v0.tests.run_g2_tests
  passed: 16  failed: 0

PYTHONPATH=/home/user /home/user/.venv/bin/python \
  -m cat_theo_machine.researcher_v0.tests.run_g3_tests
  passed: 17  failed: 0
```

The G4 suite establishes delivered-set binding, representative order, unchanged search totals, structural cadence, declared grammar, replayable `BrokenOn`, three parity candidates/proofs, full R_even and R_plus rule checking, missing-reading unsupported behavior, scope-first replay, tamper failure, replay of every proved archive entry, no pruning, bounded artifact counts, and deterministic candidate artifacts.

## 10. Constraint verification

The required package-wide greps were rerun. Their hits are prior documentation prose such as `inspection.md`, `CONSTRAINTS.md`, and old reports; there are no G4 code hits for reflection, direct `core`, Programme C/L imports, monkeypatching, or module-level functions.

A stricter G4-only scan also returned no hits for:

```text
module-level def / async def
reflection or dynamic import
core / programme_c / programme_l
monkeypatch / setattr / delattr
hashlib
line comments
Python bool literals
while
Python list / dict / set / tuple construction
direct comparison operators
host text find / count / replace / lower
```

Generated Python 3.11 cache files were removed and are not part of the gate. Pre-existing tracked cache files from the base checkout were restored unchanged.

## 11. Integrity and boundary

```text
core.py                         untouched
Programme C                     untouched and not imported
Programme L                     untouched and not imported
live graph / search             not imported by G4
admission / activation / rent   not called
live knowledge                  not written
prior-gate files                unmodified
tags                            unmodified
monkeypatching                  none
G4 pruning                      none
checked unreachability          none
```

G4 proves preservation only. It does not bind a proved invariant to task endpoints, compare two present endpoint readings for separation, mint an unreachability certificate, or change an attempt outcome.

## 12. G5 handoff

The next bounded item may load the three replayed proved-invariant certificates, resolve only correctly typed pending slots, recompute both endpoint readings under A2.1, require separation, and only then consider invariant-backed pruning or checked unreachability. The R_plus parity refutation and all Length refutations must remain active scope guards. No G5 use is implemented here.
