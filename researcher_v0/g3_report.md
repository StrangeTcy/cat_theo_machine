# Researcher-v0 — G3 (Laboratory execution gate) report: BASELINE

Status: **BASELINE run complete; MINING not run.** Per the staged G3
authorization (G2 report §11, an explicit override of the brief's G3 wording),
G3 runs the delivered canonical task set under BASELINE only. MINING stays for
G4/G5, on the same canonical ids and the same budgets. No invariant was
proved, nothing was mined or pruned, and no unreachability certificate exists.

## 1. Run identity

```text
agent:        Researcher-v0
branch:       arena/01a0d40c-cat-theo-machine (this session's pinned branch)
base:         ece90a8237cf39ed181a57c5044db689afb96294
              ("Researcher-v0 G2 follow-up: precondition canonical-id test;
               typed PENDING-REF"), the tip of
               origin/arena/01a0d325-cat-theo-machine, verified by object id.
               The session branch was created on this exact commit;
               `git merge --ff-only ece90a8` reported "Already up to date."
HEAD at run:  ece90a8 plus the uncommitted G3 files (the G3 commit follows)
Python:       3.11.2 (/usr/bin/python3)
gmpy2:        2.3.1 (absent in this sandbox; reinstalled at exactly 2.3.1,
              binary wheel, into the system interpreter; no repository file
              changed for it)
PYTHONPATH:   empty; every command runs from the repository's parent
              (/home/user)
condition:    BASELINE (mining off)
budget:       32 expansions per task; wall-clock ceiling 60000 ms per task
              (never reached: slowest attempt 2307 ms)
workers:      max_workers 1: one in-process worker (worker-0), no pool
seed:         none; the run is deterministic (breadth-first in declared rule
              order, representatives in delivered order); a rerun reproduces
              the journal apart from elapsed milliseconds (tested)
task set:     researcher_v0/tasks/tasks.jsonl, git blob a8ba3f91..., blake2b-256
              b89ac1f5742ea7bbb03bffa59fc10efab7a4ab27b522edbc014d3448882ec90c
artifacts:    researcher_v0/ only
live activation: none
```

## 2. Preflight (G3 base hand-off, steps 1–8)

The hand-off named `arena/01a0d3c7-cat-theo-machine` as the G3 session
branch. This session is pinned to `arena/01a0d40c-cat-theo-machine`, which the
platform created directly on `ece90a8`; all G3 work is committed to and pushed
from that branch only.

| # | Step | Result |
|---|---|---|
| 1 | `git fetch origin arena/01a0d325-cat-theo-machine` | exit 0; `git ls-remote` shows `ece90a8237cf39ed181a57c5044db689afb96294` for that ref |
| 2 | `git cat-file -t ece90a82...` | `commit` |
| 3 | ancestry `8094c46`, `83e6003c`, `97a746f`, `76bdc11` → `ece90a8` | first pass: exit 128 on all four ("Not a valid object name"): the sandbox clone was shallow at depth 1 and held `ece90a8` alone. `git fetch --unshallow origin arena/01a0d325-cat-theo-machine` adds objects only and moves no branch. Second pass: all four exit 0. `8094c46 → 2100d54 → 83e6003c` also confirmed (exit 0, exit 0), so `2100d54` sits between them as the hand-off corrected |
| 4 | `git merge-base --is-ancestor HEAD ece90a8` | exit 0 |
| 5 | `git merge --ff-only ece90a8` | `Already up to date.` |
| 6 | `git rev-parse HEAD` | `ece90a8237cf39ed181a57c5044db689afb96294`, matches |
| 7 | environment | Python 3.11.2; gmpy2 missing, reinstalled at 2.3.1; PYTHONPATH empty; seed, budget and workers as §1 |
| 8 | `run_g1_tests`, `run_g2_tests` | `passed: 23  failed: 0`, `passed: 16  failed: 0`; `tasks.jsonl` blob unchanged by the G2 regeneration (`a8ba3f91...` before and after) |

Chain verified, first-parent: `8094c46 → 2100d54 → 83e6003 → 97a746f →
76bdc11 → ece90a8`.

## 3. What G3 built

| File | Contents |
|---|---|
| `researcher_v0/checker.py` | the experiment checker: certificate layout and content-addressed id; reachable-path replay by recomputation; the A2.1 reading guard (`ObserverReadings`, `ReadingsVerdict`); typed PENDING-REF (`PendingSlot`, `SlotMismatch`, `ResolvePendingRef`) |
| `researcher_v0/laboratory.py` | the BASELINE executor: canonical representatives, budgeted breadth-first search, the five-label BASELINE vocabulary, attempt records, journal and archive rendering |
| `researcher_v0/run_g3_baseline.py` | the run: binding check, selection, BASELINE, artifacts, printed summary |
| `researcher_v0/journals/baseline.jsonl` | the journal: header binding, 34 attempt lines, footer counts |
| `researcher_v0/certificates/baseline_path_certificates.jsonl` | 21 reachable-path certificates with their replay logs |
| `researcher_v0/tests/test_g3_baseline.py` | 17 tests as `Edge` classes |
| `researcher_v0/tests/run_g3_tests.py` | read-only test runner (exit 0 / 1) |
| `researcher_v0/g3_report.md` | this report |

No prior-gate file was modified: G1's and G2's code, `tasks.jsonl`, the
reports, `CONSTRAINTS.md` and `inspection.md` are unchanged, and G1/G2 are
reused by import.

The test runner writes nothing. The journal carries elapsed milliseconds, so a
runner that regenerated it would change a deliverable on every test run; the
tests read the artifacts and recompute in memory, including one full BASELINE
rerun compared with timing masked.

House idiom as G1/G2: each operation is an `Edge` class called as
`Class(args)()`; no module-level function (`grep -c "^def "` is zero in every
file), no Python container, no `isinstance` / `hasattr` / `type` / `__class__`
/ `lambda` / `global` / `__new__`, no bool literal, no module-level mutable
state; `core.py` untouched; nothing monkeypatched. Non-substrate imports:
`hashlib` (certificate ids, task-set digest), `time` (elapsed milliseconds,
wall-clock ceiling), `os` / `sys` at the runners' file boundary.

## 4. The run

**Binding.** The runner regenerates the G2 rows and requires
`RowsToJsonl(kept)` to equal `tasks.jsonl` byte for byte before any task runs;
otherwise it halts and writes nothing. The header records the blake2b-256 of
the delivered text.

**Selection.** One representative per canonical id: the first delivered row of
that id, in delivered order. 34 attempts; the other 8 delivered rows (the
display-rename twins `T0012 T0017 T0022 T0027 T0032 T0037 T0042` and `T0044`)
are recorded as `members` of their representative and never re-run.

**Search.** Breadth-first from the task start, rules applied in declared order
through the G1 applier (`token_domain.ApplyRule`, the transition relation
derived from rule content), states deduplicated with `machine.Compare`, goal
tested when a state is generated. The search stops when the frontier is empty
(OPEN_RESIDUAL), when 32 expansions are spent, or when 60000 ms are spent
(both BUDGET_EXHAUSTED).

**Vocabulary.** Five labels: `CHECKED_REACHABLE`, `BUDGET_EXHAUSTED`,
`OPEN_RESIDUAL`, `UNSUPPORTED`, `EXECUTION_FAILURE`. A reached goal is not yet
an outcome: the path is bound into a certificate and replayed by the checker,
and only a REPLAYED verdict yields `CHECKED_REACHABLE` (a failed replay would
be OPEN_RESIDUAL: malformed evidence is never a result). The BASELINE executor
has no route to `CHECKED_UNREACHABLE`: that label is not defined in the G3
modules, and the inertness test guards it.

## 5. Outcomes

```text
attempts            34   (34 canonical ids, each exactly once; members cover all 42 rows)
CHECKED_REACHABLE   21   (21 reachable-path certificates, all REPLAYED)
BUDGET_EXHAUSTED    10   (32 of 32 expansions each)
UNSUPPORTED          3   (T0043 = T0044, T0045, T0046: typed PENDING-REF, unresolved)
OPEN_RESIDUAL        0
EXECUTION_FAILURE    0
CHECKED_UNREACHABLE  0   (expected; see the A2.3 reading below)
counterexamples      0   (a mining artifact; none exists at BASELINE)
total expansions   361
```

| seq | task | members | ruleset | start → goal | outcome | exp. | certificate |
|---|---|---|---|---|---|---|---|
| 1 | T0001 | T0001,T0012 | R_even | 0 → 2 | CHECKED_REACHABLE | 1 | `cert-adaa742f3d4e0d8c…` |
| 2 | T0002 | T0002,T0017 | R_even | 0 → 4 | CHECKED_REACHABLE | 2 | `cert-66d714d4a6113374…` |
| 3 | T0003 | T0003,T0022 | R_even | 0 → 3 | BUDGET_EXHAUSTED | 32 | — |
| 4 | T0004 | T0004,T0027 | R_even | 1 → 3 | CHECKED_REACHABLE | 1 | `cert-83253e7fbcde6bdd…` |
| 5 | T0005 | T0005,T0032 | R_even | 2 → 5 | BUDGET_EXHAUSTED | 32 | — |
| 6 | T0006 | T0006,T0037 | R_even | 4 → 2 | CHECKED_REACHABLE | 1 | `cert-27a483877425c4be…` |
| 7 | T0007 | T0007,T0042 | R_even | 6 → 0 | CHECKED_REACHABLE | 5 | `cert-b66048fbd3c02bed…` |
| 8 | T0010 | T0010 | R_even-minus-Remove2 | 0 → 2 | CHECKED_REACHABLE | 1 | `cert-d72febb0b600d885…` |
| 9 | T0011 | T0011 | R_plus | 0 → 2 | CHECKED_REACHABLE | 1 | `cert-882559625de331f7…` |
| 10 | T0013 | T0013 | R_even | 0 → 5 | BUDGET_EXHAUSTED | 32 | — |
| 11 | T0014 | T0014 | R_even | 0 → 6 | CHECKED_REACHABLE | 3 | `cert-a8880dfc9aef4fed…` |
| 12 | T0015 | T0015 | R_even-minus-Swap | 0 → 4 | CHECKED_REACHABLE | 2 | `cert-4674645a36a34801…` |
| 13 | T0016 | T0016 | R_plus | 0 → 4 | CHECKED_REACHABLE | 2 | `cert-15d9ead59ec84688…` |
| 14 | T0020 | T0020 | R_even-minus-Remove2 | 0 → 3 | BUDGET_EXHAUSTED | 32 | — |
| 15 | T0021 | T0021 | R_plus | 0 → 3 | CHECKED_REACHABLE | 2 | `cert-bfc57f5e741ef18c…` |
| 16 | T0023 | T0023 | R_even | 1 → 4 | BUDGET_EXHAUSTED | 32 | — |
| 17 | T0024 | T0024 | R_even | 1 → 5 | CHECKED_REACHABLE | 2 | `cert-369a40c0da0ad746…` |
| 18 | T0025 | T0025 | R_even-minus-Swap | 1 → 3 | CHECKED_REACHABLE | 1 | `cert-1a9940f208a1cf0f…` |
| 19 | T0026 | T0026 | R_plus | 1 → 3 | CHECKED_REACHABLE | 1 | `cert-a6c400c1be05df70…` |
| 20 | T0028 | T0028 | R_even | 2 → 6 | CHECKED_REACHABLE | 2 | `cert-ce33a5fa97394425…` |
| 21 | T0029 | T0029 | R_even | 2 → 7 | BUDGET_EXHAUSTED | 32 | — |
| 22 | T0030 | T0030 | R_even-minus-Remove2 | 2 → 5 | BUDGET_EXHAUSTED | 32 | — |
| 23 | T0031 | T0031 | R_plus | 2 → 5 | CHECKED_REACHABLE | 2 | `cert-24eff15cf311c030…` |
| 24 | T0033 | T0033 | R_even | 4 → 3 | BUDGET_EXHAUSTED | 32 | — |
| 25 | T0034 | T0034 | R_even | 4 → 4 | CHECKED_REACHABLE | 0 | `cert-4b650f762033f08f…` |
| 26 | T0035 | T0035 | R_even-minus-Swap | 4 → 2 | CHECKED_REACHABLE | 1 | `cert-09c7cd12227330bb…` |
| 27 | T0036 | T0036 | R_plus | 4 → 2 | CHECKED_REACHABLE | 1 | `cert-3d2a738a31f54ac1…` |
| 28 | T0038 | T0038 | R_even | 6 → 1 | BUDGET_EXHAUSTED | 32 | — |
| 29 | T0039 | T0039 | R_even | 6 → 2 | CHECKED_REACHABLE | 3 | `cert-2ee7dc10fc4c1c9a…` |
| 30 | T0040 | T0040 | R_even-minus-Remove2 | 6 → 0 | BUDGET_EXHAUSTED | 32 | — |
| 31 | T0041 | T0041 | R_plus | 6 → 0 | CHECKED_REACHABLE | 7 | `cert-517adf6955b5723c…` |
| 32 | T0043 | T0043,T0044 | R_plus | 0 → 2 | UNSUPPORTED | 0 | — |
| 33 | T0045 | T0045 | R_even-minus-Swap | 1 → 3 | UNSUPPORTED | 0 | — |
| 34 | T0046 | T0046 | R_even-minus-Remove2 | 2 → 5 | UNSUPPORTED | 0 | — |

(`start → goal` are token counts, host reporting values; each journal line
also carries the canonical fact text of both states, which is what binds.)

**The A2.3 reading.** Zero `CHECKED_UNREACHABLE` results with mining off is the
expected outcome, not a defect and not an unfair comparison: BASELINE mints no
invariant certificate, so no unreachability claim can be certified (A1.1: a
bounded search exhausting its budget in an unbounded token world is
`BUDGET_EXHAUSTED`, never unreachability). Every ruleset in the set contains
`Add2`, so no frontier ever closes, and the ten unanswered queries spend the
full budget.

## 6. Certificates and replay

Layout `researcher-v0-certificate/1`, shared by every v0 certificate kind:
`(kind, observer, start, goal, ruleset digest, checker version, evidence)`. A
reachable-path certificate has no observer and, as evidence, its steps
`(per-rule content digest, state after)` in path order, so a step names rule
content, never a display label or a position. The id is
`cert-<blake2b-256>` over the canonical content text (G1 encoders; states by
their fact chains), so re-minting the same content in another process yields
the same id; the tests re-mint all 21 and compare ids.

Replay (`checker.ReplayPathCertificate`) recomputes, in the order of
`g1_replay_procedure.md` adapted to a path: (1) the task ruleset's content
digest against the certificate's, where a mismatch is SCOPE_MISMATCH and
nothing else is compared; (2) kind, observer slot and checker version; (3) the
certificate's start and goal against the task's; (4) every step re-applied
from the task's exact rule content with the G1 applier, each recomputed
successor `Compare`d with the recorded one; (5) the final state against the
goal. All 21 archived certificates carry `"replay": "REPLAYED"`; the test
suite shows the checker refusing a changed ruleset (SCOPE_MISMATCH for T0010
and T0011 against T0001's certificate), accepting a display rename (T0012, same
digest: REPLAYED, per A1.2), and failing a wrong goal, a tampered
intermediate state, a rule outside the ruleset, an older checker version and a
foreign kind.

## 7. Typed PENDING-REF

Each scope-break row's slot is typed `(kind proved-invariant, observer
Parity(observed), old ruleset digest recomputed from the row's old specs,
checker version)`. Resolution searches the run's archive for a certificate
matching all four; the parent's archived certificates that fail are recorded
with the first differing field.

| task | members | pending | resolution | refused by type |
|---|---|---|---|---|
| T0043 | T0043,T0044 | `pending:T0001` | unresolved | `cert-adaa742f…` (T0001's path certificate): kind reachable-path is not proved-invariant |
| T0045 | T0045 | `pending:T0004` | unresolved | `cert-83253e7f…` (T0004's path certificate): kind reachable-path is not proved-invariant |
| T0046 | T0046 | `pending:T0005` | unresolved | none: T0005 is BUDGET_EXHAUSTED and minted no certificate |

All three canonical scope-break tasks are UNSUPPORTED at zero expansions,
even where the parent holds a path certificate (PENDING-REF point 3). An
unresolved reference is recorded as `"pending_resolution": "unresolved"`: it is
not an error, not a refutation and not a checked result (point 2). The
resolver is shown able to say yes: an in-memory fixture shaped like the slot
resolves, and altering any single one of its four fields makes it fail. The
fixture is never archived, written or replayed.

## 8. A2.1-R — `MissingPhiReadingIsNotChecked`

The standing acceptance item from G2 report §7 is test 13, by that name. The
guard (`checker.ObserverReadings`) requires `invariance.PhiHolds` truth and a
non-empty `invariance.PhiReading` on BOTH sides, else it returns NOT_CHECKED;
`ReadingsVerdict` compares only two present readings (SEPARATES /
SAME_READING) and passes NOT_CHECKED through. The test builds a goal state with
no Parity fact: `PhiReading` there is `EmptyList`, and a naive `Compare` of the
two readings says "different" (asserted, as evidence of the hole). The guard
reports NOT_CHECKED on either side, never `false_value`, never equal to a
present reading, and its verdict never SEPARATES. Present readings still
compare: 0 → 3 separates, 0 → 2 reads the same.

This is the one A2.1 replay step G3 carries. BASELINE holds no invariant
certificate, so the run never enters it; the preservation steps belong to G4,
where a candidate first exists.

## 9. Tests and results

```text
run:      cd /home/user && python3 -m cat_theo_machine.researcher_v0.run_g3_baseline
          binding holds; 34 attempts; artifacts written (exit 0)
tests:    cd /home/user && python3 -m cat_theo_machine.researcher_v0.tests.run_g3_tests
          passed: 17  failed: 0   (exit 0)
regression:
          run_g1_tests  passed: 23  failed: 0   (exit 0)
          run_g2_tests  passed: 16  failed: 0   (exit 0; tasks.jsonl blob unchanged)
```

| # | Test | What it establishes |
|---|---|---|
| 1 | journal: header binds BASELINE, budget, workers, seed, task set | condition, mining off, 32 / 60000, one worker, seed none, checker version, 42 / 34, and the blake2b of the delivered text |
| 2 | journal: 34 canonical ids, each attempted exactly once | 34 attempt lines; every delivered row's canonical id occurs exactly once |
| 3 | journal: members cover the 42 delivered rows | members recorded per attempt, summing to 42, with 8 collapse groups |
| 4 | journal: every attempt records the G3 fields | task_id, ruleset_version, start, goal, worker_id, attempt_id, outcome, expansions, elapsed_ms, certificate_id, counterexample_id on every line; version, start and goal texts equal recomputed values |
| 5 | outcomes: BASELINE vocabulary, zero unreachability (A2.3) | 34 outcomes, all from the five labels; no `CHECKED_UNREACHABLE` anywhere in the journal |
| 6 | certificates: each CHECKED_REACHABLE cites a replaying certificate | re-minted id equals the cited id, replay REPLAYED, archive line REPLAYED; no other line cites a certificate |
| 7 | certificates: reachable-path only | 21 lines, all kind reachable-path, observer empty, no other kind |
| 8 | budget: a timeout is not a counterexample | exhausted lines cite nothing and spent 32; an attempt at budget 1 and one at a 0 ms ceiling both exhaust with no certificate and no counterexample |
| 9 | failure: a crash is not a refutation | a malformed rule spec yields EXECUTION_FAILURE, recorded text, no certificate, no checked label |
| 10 | outcomes: UNSUPPORTED is distinct from BUDGET_EXHAUSTED | the labels differ; UNSUPPORTED lines are exactly the three scope-break rows at 0 expansions |
| 11 | PENDING-REF: T0043=T0044, T0045, T0046 unresolved | as §7, read from the journal, with refusals naming the parents' real certificate ids |
| 12 | PENDING-REF: typed resolution, four fields checked | a path certificate never fills the slot; a slot-shaped fixture does; each field alone breaks it |
| 13 | A2.1-R: MissingPhiReadingIsNotChecked | as §8 |
| 14 | replay: scope first, rename keeps scope, tampering fails | as §6 |
| 15 | rerun: journal (timing masked) and archive reproduce | full in-memory rerun equals the journal apart from elapsed ms, and the archive byte for byte |
| 16 | inertness: no unreachability route in G3 modules | `laboratory.py`, `checker.py`, `run_g3_baseline.py` hold no `CHECKED_UNREACHABLE`, no unreachability or invariant constructors, no preservation call, no `programme_c`, no live `graph` / `search` import |
| 17 | corpus: tasks.jsonl bound and untouched | the journal binds the delivered digest; regeneration still reproduces the file; it still carries no outcome field |

Bite check (evidence that the suite can fail): three tamperings of the written
artifacts, each restored byte for byte afterwards. Relabelling T0003 as an
unreachability result failed tests 5 and 15; flipping one archived replay to
REPLAY_FAILED failed tests 6 and 15; erasing T0045's refusal record failed
tests 11 and 15.

## 10. Negative findings and notes

```text
unanswered queries   10 BUDGET_EXHAUSTED; none is a counterexample, none is
                     evidence of unreachability
parity reading       9 of the 10 have endpoints of different parity (T0003,
                     T0005, T0013, T0023, T0029, T0033, T0038 under R_even;
                     T0020, T0030 under R_even-minus-Remove2). T0040 (6 -> 0
                     under Add2 and Swap only) has endpoints of equal parity:
                     a parity reading cannot separate it, and it stays open
                     under the declared observer grammar. This describes the
                     questions, not a proved invariant or a result.
OPEN_RESIDUAL        0: every ruleset contains Add2, so no frontier closes
EXECUTION_FAILURE    0 in the run; the crash path is exercised by test 9 only
wall-clock ceiling   never reached (slowest attempt 2307 ms of 60000 ms)
```

## 11. Integrity

```text
core.py                      untouched
Programme C                  untouched, not imported
Programme L                  untouched
admission / activation / rent / human hooks   not called, not imported
tags                         not moved
live knowledge               not written
prior-gate files             unmodified (G1/G2 code, tasks.jsonl, reports,
                             CONSTRAINTS.md, inspection.md)
mined / proved / pruned      nothing
unreachability certificates  none; CHECKED_UNREACHABLE issued: none
invariance                   imported by checker.py for PhiHolds / PhiReading
                             (the reading guard) only
monkeypatching               none
module-level functions       none (grep "^def " over the package: zero)
```

Verification greps (CONSTRAINTS.md § Verification commands): the deny-list
strings appear only in `CONSTRAINTS.md`; the identity-pattern grep hits
documentation prose only (`CONSTRAINTS.md`, the `chains.py` docstring,
`g1_report.md`), never code; `^def ` is zero across `researcher_v0/*.py` and
`researcher_v0/tests/*.py`. Runtime `__pycache__` caches are not committed.

Environment notes, stated because they are real changes to the sandbox and
not to the repository: the checkout was a depth-1 clone, deepened with
`git fetch --unshallow` so the ancestry preflight could be answered; `gmpy2`
was absent and was reinstalled at 2.3.1, as G1 and G2 recorded.

## 12. Next bounded item

G4: the MINING condition on the same 34 canonical ids and the same budget
(32 expansions, 60000 ms, one worker), with the INV-0-style miner and the
independent checker's preservation steps added behind the A2.1 replay, and
nothing pruned before G5.
