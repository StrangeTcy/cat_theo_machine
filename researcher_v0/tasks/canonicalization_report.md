# Researcher-v0 — G2 (Task generation gate) report

Status: **task set generated, no task run**. G2 delivers the generated task
set (`researcher_v0/tasks/tasks.jsonl`) and this canonicalization report.
Zero rows carry an outcome field: *tasks generated* is not *tasks run*, and a
populated outcome at G2 would be a scope breach, not progress.

## 1. Run identity

```text
agent:        Researcher-v0
branch:       arena/01a0d325-cat-theo-machine
base:         83e6003c250de8499284725906be5b6d6be615c2
              ("Researcher-v0 G1 fix: no Python identity on terms; indices
               never in term slots"). Fetched from
               origin/arena/01a0d2fb-cat-theo-machine and verified by object
               id; this session branch was fast-forwarded onto that exact
               commit before any G2 work, so G2 sits on the G1 base the
               hand-off pinned. The hand-off asked for a fresh branch from
               that commit; this session is bound to its own branch, which
               serves as the implementation branch.
Python:       3.11.2
gmpy2:        2.3.1 (absent in this sandbox; restored to the version G1
              recorded, wheel install into the system interpreter; no
              repository file was changed for it)
PYTHONPATH:   empty; run from the repository's parent (/home/user)
budget:       single session, single process, no background jobs
seed:         none needed; generation is deterministic (a rerun reproduces
              tasks.jsonl byte for byte — tested)
artifacts:    researcher_v0/ only
live activation: none
```

## 2. What G2 built

| File | Contents |
|---|---|
| `researcher_v0/task_generation.py` | task records and rows, the generation lattice, canonicalization, exact-duplicate dropping, the JSONL writer |
| `researcher_v0/tasks/tasks.jsonl` | the generated task set: 42 rows, zero outcomes |
| `researcher_v0/tasks/canonicalization_report.md` | this report |
| `researcher_v0/tests/test_g2_tasks.py` | 15 tests as `Edge` classes |
| `researcher_v0/tests/run_g2_tests.py` | runner: generation, then tests, exit 0 / 1 |
| `researcher_v0/CONSTRAINTS.md` | the operator's standing constraints, recorded verbatim (carried from the G1 branch's `c0b3ebd` so the registry lives inside this package) |

Two pre-existing files were touched beyond the additions: `g1_replay_procedure.md`
received a one-word wording fix (a stray adverb removed so the standing
constraints' verification grep passes; no semantic change), and nothing else
of G1's changed.

House idiom throughout, as G1: each operation is an `Edge` class called as
`Class(args)()`; no module-level function, no Python container, no
`isinstance` / `hasattr` / `type` / `__class__` / `lambda` / `global` /
`__new__`; `core.py` untouched; nothing monkeypatched. Non-substrate imports:
`hashlib` (canonical digests) and `os` (path joining and directory creation at
the runner's file boundary).

## 3. Task kinds and perturbations

```text
kind reachability           7 rows   (the seed queries over R_even)
kind perturbed_reachability 35 rows  (five perturbations of each seed)
kind scope_break_test       4 rows   (old certificate slot + new ruleset)
```

Perturbations, as recorded in each row's `perturbation_reason`:

```text
seed                       the seven declared (start, goal) queries
goal +1  /  goal +2        goal moved; ruleset untouched
remove rule Remove2        ruleset = R_even minus one rule (alternating
remove rule Swap           per seed: Remove2 on seeds 1,3,5,7; Swap on 2,4,6)
add Add1                   ruleset = R_plus (G1's Add1 perturbation rules)
display rename             same rule contents, display-only labels replaced
scope break: add Add1      scope-break rows over R_plus and over R_plus with
scope break: remove rule …  renamed labels / a removed rule as the new ruleset
```

Every row records its parent task id (seeds record `none`) and its
perturbation reason. Every row binds `ruleset_version` to the G1 content
digest of its exact ruleset, recomputed from the rule terms the row carries
(`token_domain.RulesetVersionOfSpecs`) — never to a display name. A scope-break
row also records the old ruleset's digest (`old_ruleset_version`) and its
certificate slot as `pending:<parent task id>`: no certificate exists at G2.

Generation order and serials: `T0001`–`T0007` seeds (0→2, 0→4, 0→3, 1→3,
2→5, 4→2, 6→0); `T0008`–`T0042` five-row perturbation families of each seed
in order; `T0043`–`T0046` the scope-break rows.

## 4. Canonicalization

Canonical content, encoded with G1's own encoders (`ruleset_digest.TermText`
for state fact chains and the observer pattern;
`ruleset_digest.RulesetVersionText` for rule content):

```text
query rows       (query reachability  start S  goal G  ruleset V)
scope-break rows (query scope-break   start S  goal G  observer P
                                  old-ruleset A  new-ruleset B)
```

The semantic/display partition declared in G1 (report §4) is used exactly as
declared and is **not widened**: display slots and variable names stay
invisible; rule order stays invisible through sorted per-rule digests;
variable sharing, premise and replacement shapes, legality preconditions and
every semantic constant stay visible. `reachability` and
`perturbed_reachability` rows share the one query shape — provenance is not
task identity.

```text
display rename      collapses to the same canonical id as the unrenamed twin
                    (8 collapse groups; brief acceptance test 2 holds)
exact duplicate     a later row whose canonical id AND display signature both
                    match a survivor: dropped, and the drop recorded with the
                    dropped row's parent and perturbation reason (4 drops)
goal perturbation   different canonical id, same ruleset digest (the goal is
                    not rule content)
rule-content
perturbation        different canonical id AND different ruleset digest
                    (remove a rule / add Add1 / either as a scope break)
```

Comparison discipline, inherited from G1 unchanged: terms with
`machine.Compare`; emptiness of `EmptyList` with `machine.IdentityCompare`;
predicate results by identity to `truth_value` / `false_value`; no Python
identity on a term. Task ids and counts are host reporting values: they never
occupy a semantic term slot and never enter canonical content; each reported
value rides inside a term as `Pair(value, EmptyList)` and is read at payload
level only (the `FirstPremiseWithoutMatch` pattern). No record slot holds an
int-or-atom union: each shell head carries one payload kind throughout.

## 5. Counts and records

```text
generated rows : 46
dropped        : 4
delivered rows : 42   (tasks.jsonl, zero outcomes)
canonical      : 34   (non-isomorphic canonical tasks)
collapse groups: 8
```

Drop records — each dropped row keeps its parent and reason:

| dropped | parent | perturbation reason | exact duplicate of |
|---|---|---|---|
| T0008 | T0001 | goal +1 | T0003 |
| T0009 | T0001 | goal +2 | T0002 |
| T0018 | T0003 | goal +1 | T0002 |
| T0019 | T0003 | goal +2 | T0013 |

The overlap is planned: the seed lattice contains 0→3 and 0→4, so goal +1 and
goal +2 of T0001 (and goal +1 / +2 of T0003) land on already-generated
queries. First occurrence survives; the drop path is exercised by
construction.

Collapse groups — same canonical id across a display rename:

| canonical id (first 16 hex) | rows |
|---|---|
| 02993ae55d9fce2f | T0001 + T0012 |
| 82478be487701e35 | T0002 + T0017 |
| 1ebd42297f4d5012 | T0003 + T0022 |
| 117aff88d575c01a | T0004 + T0027 |
| 15aca02a7f3ada3b | T0005 + T0032 |
| 5744458ed680101e | T0006 + T0037 |
| 81d66ef91a394b19 | T0007 + T0042 |
| 1da9972cfe660386 | T0043 + T0044 |

Ruleset digests observed (blake2b-256; the values rows bind):

```text
R_even                 15f5467c985c4dd9710e87b59b69788f3e2b23fb25f5320015589da844d2d68f
R_plus                 533cb46bd134cd0c1bcaf87d03ba6b4a1a5395c331f1ba0f391921ed500d2b8d
R_even-minus-Remove2   0b2a31f486b5fe4bd192aa4f3a00170e28af695abddc07fe11fee5e279e99bb3
R_even-minus-Swap      8fb3494f9388b1984c58a06a3acecda2d5c5d4151a365399320fb3a192675a9e
R_plus-display-renamed 533cb46bd134cd0c1bcaf87d03ba6b4a1a5395c331f1ba0f391921ed500d2b8d
R_even-display-renamed 15f5467c985c4dd9710e87b59b69788f3e2b23fb25f5320015589da844d2d68f
```

The first two match G1 report §4 exactly (the G2 test
`binding: G1 ruleset digests bound` pins them). The display-renamed variants
keep their unrenamed digests — renaming changes no binding.

## 6. Tests and results

```text
command:  cd /home/user && python3 -m cat_theo_machine.researcher_v0.tests.run_g2_tests
result:   passed: 15  failed: 0   (exit 0)

regression:  cd /home/user && python3 -m cat_theo_machine.researcher_v0.tests.run_g1_tests
             passed: 23  failed: 0   (exit 0)
```

| # | Test | What it establishes |
|---|---|---|
| 1 | minimums: generated >= 30, canonical >= 10 | 46 generated, 34 non-isomorphic canonical |
| 2 | tasks.jsonl: delivered rows >= 30 | 42 rows delivered |
| 3 | tasks.jsonl: zero outcome fields | no outcome/status/result vocabulary exists in the deliverable |
| 4 | rows: parent task id and perturbation reason recorded | every row carries both fields (seeds: `none` / `seed`) |
| 5 | canonical: display rename collapses (acceptance #2) | every renamed row shares an unrenamed twin's canonical id and digest |
| 6 | canonical: exact duplicates dropped and recorded | each drop duplicates a survivor in content and display; delivered rows pairwise non-exact |
| 7 | canonical: goal perturbation changes id, keeps digest | goal is not rule content |
| 8 | canonical: rule-content perturbation changes id and digest | remove-a-rule and add-Add1 rows diverge both ways |
| 9 | canonical: scope break changes ruleset digest | old and new digests differ on every scope row |
| 10 | binding: G1 ruleset digests bound | R_even / R_plus rows carry G1 report §4 values |
| 11 | binding: version is content, never display name | bindings are 64 hex of content; display text is never a binding or an id |
| 12 | discipline: ids and counts outside semantic terms | shells ride as `Pair(value, EmptyList)`; fact/rule/observer atoms are declared or text; no task id in canonical content |
| 13 | scope break: pending certificate references only | `old_certificate` is `pending:…`; nothing is minted |
| 14 | inertness: no checker or outcome vocabulary | the generation module holds none of the guarded tokens |
| 15 | generation: rerun reproduces tasks.jsonl | deterministic byte-for-byte |

## 7. Deferred to checker

Recorded here per the G2 hand-off; **no checker code is written at G2**. The
checker gates (G3/G4) must include a named acceptance test:

```text
MissingPhiReadingIsNotChecked
    a missing PhiReading is reported as "not checked" and never compares
    equal to false_value or to a differing reading.
```

This is the A2.1 carry-forward (`PhiReading` returns `EmptyList` on a miss,
which a naive comparison would treat as a differing value). G2 calls no
reading function; the scope-break observer rides as inert pattern data for
that later test to consume.

## 8. Integrity

```text
core.py                      untouched
Programme C                  untouched, not imported
Programme L                  untouched
admission / activation / rent / human hooks   not called, not imported
tags                         not moved
live knowledge               not written
tasks run / mined / proved / pruned           none
outcomes issued              none (vocabulary absent — tested)
certificates produced        none (pending: references only — tested)
monkeypatching               none
module-level functions       none (grep "^def " over the package: zero)
```

Verification greps (CONSTRAINTS.md § Verification commands): the deny-list
strings appear only in `CONSTRAINTS.md` (after the one-word wording fix of
§2); the identity-pattern grep hits documentation prose only, never code;
`^def ` is zero across `researcher_v0/*.py` and `researcher_v0/tests/*.py`.

Files changed: `researcher_v0/task_generation.py`,
`researcher_v0/tests/test_g2_tasks.py`, `researcher_v0/tests/run_g2_tests.py`,
`researcher_v0/tasks/tasks.jsonl`, `researcher_v0/tasks/canonicalization_report.md`,
`researcher_v0/CONSTRAINTS.md`, one wording fix in
`researcher_v0/g1_replay_procedure.md`. G1's module code
(`token_domain.py`, `ruleset_digest.py`, `chains.py`) is unchanged and reused
by import. Runtime `__pycache__` caches are not committed.

## 9. The distinction this report keeps

```text
tasks generated   46   (42 delivered rows, 34 non-isomorphic canonical)
tasks run          0   (zero outcomes is the correct G2 end state)
```

A generated task is a question. Nothing here is an answer.

## 10. Next bounded item

G3 runs the delivered canonical set under BASELINE and MINING with the
operational replay of `g1_replay_procedure.md` — including
`MissingPhiReadingIsNotChecked` — gating every unreachability claim.
