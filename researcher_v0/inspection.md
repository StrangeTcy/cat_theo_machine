# Researcher-v0 G0 — Inspection report

Status: inspection only. No code, no jobs, no tags. This file is the only change.

## 1. Run identity

```text
branch:      arena/01a0352a-cat-theo-machine
HEAD (v0 base): df8b1bcfe8d99d72da0248c05c5a305269568c16
remote:      git ls-remote origin arena/01a0352a-cat-theo-machine
             -> df8b1bcfe8d99d72da0248c05c5a305269568c16 (verified 2026-09-24;
                brief + Amendment A1 retrievable)
Python:      3.11.2
gmpy2:       2.3.1
PYTHONPATH:  <empty> (repo parent must be on sys.path; probes used sys.path.insert)
```

Import-order constraint (pre-existing, same on every branch checked):
`machine` must be imported before `graph` (`machine.py` line ~1007 imports
from `.graph`; graph-first import raises ImportError on the partial cycle).
All probes below used machine-first order.

## 2. Component inventory

| # | Needed | Found | file:line | imports cleanly? | verdict |
|---|---|---|---|---|---|
| 1 | cold worker pool | `BoundedWorkerPool` | `programme_c/worker.py:93` (`spawn_worker` :112, budget/timeout/ticket taxonomy) | NO — `No module named 'hyge_int_pkg'` (via `programme_c/__init__.py:9`) | v0-local equivalent; reuse the pattern only (budget_millis, tickets, F_TIMEOUT / F_CRASH / F_LAUNCH_ERROR split, launch-error is never refutation). Note: `spawn_worker` requires snapshot preflight (`snapshot_path` + identity), wrong weight for a token world. |
| 2 | certificate replay | `run_certificate_replay_subprocess` | `programme_c/cert_replay.py:67` (child: `run_cert_replay_child` :304; entailment: `ConclusionEntailsGoal` :264) | NO — same `hyge_int_pkg` failure (package `__init__` runs first); child would also fail (`-m hyge_int_pkg.main` at :105) | NOT reusable even if importable: it replays `BuildDerivation` search certificates bound to snapshots. v0 certificates are invariant certificates. Reuse the discipline only: isolated replay, fatal start-mismatch, two-disjunct entailment shape. v0 replays via `invariance.py` predicates (§3a). |
| 3 | typed outcomes | `ProvedLabel` / `RefutedLabel` / `FailedLabel` / `InvariantRefutedLabel` / `AttemptResultLabel` | `labels.py:1442` / `:1166` / `:1450` / `:1470` / `:1434` (classes); singletons `:1788` / `:1719` / `:1790` / `:1795` / `:1786` | YES (`labels` imports clean) | Reuse where they fit (proved / refuted / failed). v0's six journal outcomes (`CHECKED_REACHABLE`, …) have no atoms, and no `BrokenOn` label exists anywhere in `labels.py` → v0-local labels on the same `ConstructorLabel` pattern; v0-local `BrokenOn` records mapped from `InvariantRefuted` terms (§3a). |
| 4 | journal format | `WorkerJournal` / `open_journal` / `load_journal` | `programme_c/journal.py:55` / `:167` / `:191`; JSONL header(binding) + `kind`/`record` lines + footer seq; kinds `trace`/`attempt`/`residual`/`counterfactual` + `candidate_law`/`candidate_policy` (:26–27) | NO (`hyge_int_pkg` import at :14–15) | v0-local JSON journal mirroring the shape: header binding (task id, ruleset_version, seed, attempt), append-only records, footer seq check. Binding must include ruleset_version (their binder uses snapshot/task/attempt/assumption instead). |
| 5 | INV-0 miner | NONE. No `invariant_experiment.py` on this branch; `InvariantCandidate` (`invariance.py:1559`) is a term constructor, not a loop. `INV-0` appears only in prose (`protocol/C-INT-8A.md`, the brief). | — | n/a | v0-local miner loop (G4). |
| 6 | INV-0 checker | `Preserves` (per-rule proof; refutation carries `(pre_reading, post_reading)` reason) / `IsPreserves` / `IsInvariantRefuted` / `Invariant` (whole-ruleset walk) / `IsInvariant` / `Unreachable` (certificate term) / `IsUnreachable` / `ReachabilityPrune` (pruning rule) | `invariance.py:98` / `:124` / `:137` / `:1199` / `:1235` / `:1248` / `:1263` / `:1276` | YES (`invariance` imports clean; pulls `labels`, `machine`, `proof`, `search`) | REUSE. Testsuite coverage: `Preserves` exercised at `testsuite.py:15594`, `:16156`; `ReachabilityPrune`/`IsUnreachable` at `:15590`–`:15626`; 64 mention lines total. |
| 7 | Peano / token rules | structural nats `NatRepOf` / `Succ` / `Count` / `NatEq` / `NatLess`; `ZeroLabel` / `SuccLabel`; rule API `Rule` / `RulePremises` / `RulePattern` / `RuleIsUnary` / `RuleReplacement` | `math/peano.py:28` / `:177` / `:206` / `:320` / `:342`; `labels.py:14`, `:18`; `proof.py:156` / `:316` / `:326` / `:339` / `:354` | YES (`math`, `math.peano` import clean; `M.NatEq` used in testsuite at `:201`, `:250`, `:357`) | Reuse nats (structural `Zero`/`Succ` via registry + GMP rep cache). Token-world RULES (`Add2`/`Remove2`/`Add1` as `proof.Rule` terms) do not exist → G1 builds them; legality preconditions live in rule premises (`MultiRule(premises, replacement)`, `proof.py:166`). |

Out of scope, noted for avoidance: `JoinAdmission` / `ResultCertificate`
(`programme_c/join.py:115` / `:86`) is admission machinery — forbidden for v0
by brief §0 (and unimportable here regardless). `EvidenceArchive`
(`programme_c/evidence.py:32`) likewise unimportable → v0-local archive.

## 3a. How CHECKED_UNREACHABLE will be certified

Checker: `invariance.ReachabilityPrune(start, goal, invariant, phi, registry)`
(`invariance.py:1276`), fed by `invariance.Invariant` (`:1199`).

1. Prove: `Invariant(phi, ruleset, registry, start, rewrite_rules)` walks the
   ruleset term (`_walk`, :1218–1232) and applies `Preserves(rule, phi,
   registry)` (`:98`) to EVERY rule. Any failure returns
   `InvariantRefuted(phi, rule, (pre_reading, post_reading))` — the
   counterexample (v0 `BrokenOn` source). Success returns
   `Pair(InvariantLabel, (phi, ruleset[, transform]))`.
   - With no `Sequence` facts (v0 token world), `ExamineTransforms` (`:1039`)
     returns `EmptyList` and `Invariant` reduces to the per-rule `Preserves`
     walk (verified by reading `:1199`–`:1233`). v0 passes a real registry +
     start; `rewrite_rules` may be `EmptyList`.
2. Certificate contents: `Unreachable` term
   `Pair(UnreachableLabel, (start, goal, invariant, witness))` (`:1248`–`:1258`)
   with `witness = (PhiReading(start, phi), PhiReading(goal, phi))`. The
   embedded invariant term itself carries `(phi, ruleset)`.
3. Replay (both A1.1 parts, re-executed by the experiment checker over the
   task's exact ruleset term): `IsInvariant(invariant)` (`:1235`) must be
   truth; `PhiHolds(start, phi)` (`:74`) truth;
   `Compare(PhiReading(start), PhiReading(goal))` (`constructors.py:247`)
   must be false. Timeout/crash during replay → `OPEN_RESIDUAL` /
   `EXECUTION_FAILURE`, never a certificate.

G1 design constraint: `Preserves` uses exact `Compare`-equality of pre/post
readings (`:106`–`:115`). Observers are match patterns over state facts
(`PhiReading`, `:58`–`:73`; `StateFacts`, `:27`). The parity observer must be
shaped so `Add2`/`Remove2` yield `Compare`-equal readings while odd/even
states differ.

## 3b. How the ruleset version fingerprint is computed

Per rule, fingerprint inputs from `proof.py`: `RulePremises` (`:316`) +
`RuleReplacement` (`:354`) + `RuleIsUnary` (`:339`). Premises carry legality
preconditions (e.g. "`Remove2` requires ≥2 tokens"), so two same-named rules
with different legality digest differently.

1. Canonical encoding: structural walk of the `Pair` skeleton with constructor
   labels; alpha-normalize free-atom identities by traversal-order index.
   Display atom values are excluded (A1.2).
2. TRAP (must be validated in G1): `prettyprinting.PrettyTerm` (`:332`)
   renders via the registry and may leak display text — G1 must NOT hash its
   output raw. The G2 rename test (brief acceptance #2) is the check: display
   rename preserves the digest.
3. Combine: sort per-rule digests (order-independent), hash the sorted list
   with domain tag `researcher-v0-ruleset/1`. Output hex string =
   `ruleset_version`. (Observers versioned separately in candidate records;
   the ruleset version covers rules only.)
4. Adding `Add1` / removing / changing any rule changes the digest by
   construction.

## 3c. How scope mismatch is detected

1. `Invariant` terms embed the ruleset TERM (`_walk`, `:1218`–`:1232`). v0
   certificate records store `ruleset_version` = fingerprint (§3b) of that
   embedded term. (No existing cert format carries a ruleset field:
   `ResultCertificate`, `join.py:86`–`:101`, has snapshot/obligation/
   assumption only — scope lives in v0-local records + the embedded term.)
2. Prune path (G5): recompute the fingerprint of the TASK's ruleset, compare
   to the certificate's. Unequal → `ScopeMismatch` record, no prune, count it
   (`scope_mismatch_count`). Equal → proceed to §3a replay.
3. `R_even` → `R_plus` (add `Add1`): digest differs → the old parity
   certificate scope-mismatches every `R_plus` task. No pruning across the
   boundary, ever.

## 4. Disposition of the three A1 additions (review)

1. Fingerprint order-independence + preconditions → specified in §3b; NOT in
   brief text → recommend an A2 amendment or folding into the G1 task text
   (operator call; G0 changes no existing file).
2. Pruning needs invariant-proof + differing values, replayed evidence holds
   both → ALREADY covered by A1.1; §3a implements it (witness pair + triple
   re-check).
3. Baseline zero `CHECKED_UNREACHABLE` is expected (no mining → no invariant
   proofs) → new; recommend adding to the G7 / morning-report instructions so
   it reads as correct, not as a bug or unfair comparison.

## 5. G1 handoff (facts only)

Reuse: `invariance.py` checker (8 entry points, §2 row 6), `labels.py` atoms
(`Proved` / `Refuted` / `Failed` / `InvariantRefuted`), `math.peano` nats,
`proof.py` Rule API.
Build local: worker pool, journal, archive, miner loop, `BrokenOn` records,
six outcome labels, fingerprint normalizer, scope check, discovery-graph
writer.
Do not touch: `core.py`, Programme L, `programme_c`, admission / activation /
rent / human hooks, tags, live knowledge.

## 6. Integrity

Methods: `grep` / `sed` / file reads + clean import probes
(`PYTHONDONTWRITEBYTECODE=1`, machine-first order, 100 s timeouts each).
Probes: `labels`, `invariance`, `math`, `math.peano` → OK;
`programme_c`, `programme_c.journal`, `programme_c.cert_replay` → fail
(`No module named 'hyge_int_pkg'`).
Files changed: none. Files added: `researcher_v0/inspection.md` only. Jobs
run: none. Tags moved: none.
