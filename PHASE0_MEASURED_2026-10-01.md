# Phase 0 — measured on the carrier

**Date:** 2026-10-01
**Carrier:** `arena/01a0eca3-cat-theo-machine` @ `3ec069a` ("Researcher-v0 G6 inert discovery graph", 2026-09-29)
**My branch after Phase 0:** `arena/01a0f845-cat-theo-machine`
**Commits:** `7933e9d` (re-base onto carrier), `ff8b137` (apply INV-0)
**Purpose:** re-run the ODR-6 probe set against the real tree before changing dispatch. Measurements here, not the stale-tree measurements, determine the next spec.

---

## §0 Carrier choice — now verified by ancestry, not by date

`CTM-ODR-7.md` recommended `01a0eca3` because it was newest and G6-complete. That was the right answer for a weak reason. The strong reason:

```
eng-base-0            (2026-09-05, cb84540)  ⊆ cint-integrated-8a (2026-09-19, 2c97a7b)
cint-integrated-8a    (2026-09-19)           ⊆ cint-integrated-8b (2026-09-23, bb58d6e)
cint-integrated-8b    (2026-09-23)           ⊆ 01a0eca3          (2026-09-29, 3ec069a)
```

`git merge-base --is-ancestor` returns true for all three, and `git merge-base cint-integrated-8b 01a0eca3` **is** `cint-integrated-8b` — so the researcher branch descends linearly from the newest integration tag. Choosing `01a0eca3` therefore keeps the full C-INT lineage: admission correctness (`8a`), candidate-bearing rent correctness (`8b`), plus the researcher and the programme docs.

**INV-0 is not in that lineage.** `arena/01a0bb91` branches from a different base; its 29 files are purely additive (`git diff 428ecdc 01a0bb91` = +1,872 lines, zero shared-file edits), which is why the cherry-pick was clean. Verified collision-free against the carrier before applying.

**Note on the deleted-ref scare.** `arena/01a0bb91` appeared to vanish mid-session: its remote tip had moved from INV-0's commit to `b123a979` and my local remote-tracking ref was pruned. The commit was recovered via the GitHub API and the branch re-fetched. Nothing was lost, but it is a live demonstration of the repo's own rule — *an unpushed commit is not protected* — and it means **remote-tracking refs do not survive between turns in this sandbox**; any ref needed for work must be re-fetched in the same call that uses it.

---

## §1 Probe 1 — teaching ingress

**Result: `wire.py` is not a teaching ingress.** It is *"Step 42: deterministic canonical byte encoding for machine terms"* — format `WIRE1`, one UTF-8 line per section, with `serialize_term`/`deserialize_term`, `serialize_version`, `serialize_proposal_store`, `serialize_ledger`, `worker_task`, `run_workers`, `distributed_cycle`, and `save_checkpoint`/`load_checkpoint`. Its own docstring states the constraint: *"This module is substrate-only: it must never import from search/."*

**The teaching vocabulary is still absent — on the carrier too.** `grep` for `TeachingCandidate`, `ResidualRecord`, `DependencyRequest`, `AdmissionDecision`, `ProofReceipt` over all `*.py` returns **nothing**. My ODR-6 §0 finding stands, now measured on the correct tree.

**But the admission/activation machinery exists, and ODR-6 assumed it did not.** `graph.py` carries a full proposal layer: `ProposalStoreSubmit`, `ProposalStoreEntries`, `MeasurePendingProposals`, `CheckSafety`, `activate_proposal`, plus handles, interfaces, contracts and reports (`graph.py:2319–5976`). Tags confirm it is integrated work, not scaffolding:

- `cint-integrated-8a` — *"admission correctness boundary (H1–H5) via isolated replay"*
- `cint-integrated-8b` — *"candidate-bearing rent correctness (H6/H7, C-G1/G2/G3, C-C1, Q-B)"*

**`session.py` is the operational shell, and it already solves the autonomy problem properly.** Its docstring: *"A session is a pure function from checkpoint to checkpoint plus reports. No web UI, no async, no daemon, no network. `run_session` loads a checkpoint, loops `distributed_cycle`, and after each cycle writes a new checkpoint and a rendered curator report to disk."* It stops on exactly three conditions — cycle budget exhausted, quiescence, or any safety refusal. And critically:

> *"Human decisions never enter mid-session. They enter between sessions through two CLI verbs, `approve` and `countersign` … Neither verb activates anything: activation remains `activate_proposal`'s alone, on the coordinator, inside a cycle."*

That is a **better** design than the one ODR-6 specified for CL6: human input is not fenced off by a prompt, it is structurally confined to a between-session verb that cannot activate.

**The operational surface is much larger than the base.** `main.py` modes: `talk` (default — natural-language interaction through correspondence laws), `cold`, `warm`, `test`, `inspect`, `search-worker`, `ingest` (training records), `daemon` (cycle the shared talk state), `live` (one process supervising a conversation and a cycling daemon). "Taught graph data" is submitted to the daemon inbox and reaches the shared version through `G.MergeGraphVersion`.

---

## §2 Probe 2 — the `input()` seam

**It persists, it moved, and it grew.**

| Site | Base `428ecdc` | Carrier `01a0eca3` |
|---|---|---|
| derivation replay approval | `search/compare_subprocess.py:248` | **`search/compare_subprocess.py:256`** |
| comparison resume prompt | `main.py:226` | `main.py:320` |
| mode resume prompt | `main.py:273` | `main.py:367` |
| interactive REPL | — | **`main.py:11717` — `input("you> ")`** |
| console listener | — | `search/compare_console.py:10, 21, 57` |

So the seam is real and slightly larger, but its **blast radius is narrower than ODR-6 assumed**: `session.py` is explicitly designed so that a session never needs it, and the `you>` loop at `:11717` belongs to the interactive talk/live mode, not to the autonomous cycle path.

CL1's justification survives — the comparison path that `Prove` seeds still reaches a blocking prompt — but CL1 is now *"close the seam on the proof/compare path"*, not *"make the loop autonomous"*, because the loop already is.

---

## §3 Probe 3 — persistence

**Measured on the carrier: 5 of 5 checkpoint tests PASS.**

```
PASS WireRoundTripTest
PASS CheckpointMeasurementRoundTripTest
PASS InventedLemmaReplayCheckpointTest
PASS EuclideanReplayCheckpointTest
PASS ThreeVariableSOSCheckpointTest
```

The wire path is sound by construction: `save_checkpoint` writes a temporary file and `os.replace`s it (atomic), four text sections (version / proposal store / ledger), no pickle, no object activation, and the codec is explicitly designed for identity preservation — pairs hash-consed per blob, chars and GMP reps interned, anonymous atoms numbered by first appearance so *"re-serializing a deserialized blob reproduces the bytes exactly (canonical fixed point)."*

**F1 is downgraded, not confirmed.** The cold-load failure the dispatched baseline measured (`BASELINE_2026-10-01.md`: two restored derivation entries lack constructors, readers return `EmptyList`) was measured on `SnapshotCodec`, against base `428ecdc`. But the **session loop uses `wire.py` checkpoints, not `SnapshotCodec`.** The failure may therefore be confined to a path the day does not walk. F1's remaining scope is a targeted re-measurement: does `SnapshotCodec` still fail on the carrier, and does anything in the ODR-6 experiment actually traverse it? Until that is answered, F1 is **not** on the critical path — I put it there on stale evidence.

---

## §4 The finding that rewrites ODR-6: invention already exists

The checkpoint tests print `DEBUG [lemma inventor]` traces:

```
DEBUG [lemma inventor]: testing cubic linear-factor structure
DEBUG [lemma inventor]: running bounded structural exact division
DEBUG [lemma inventor]: constructing bounded candidate evidence
DEBUG [lemma inventor]: exact-division reconstruction is the independent identity validation
DEBUG [lemma inventor]: testing additive SOS structure
DEBUG [lemma inventor]: independently normalizing the candidate identity
```

And `graph.py:502` onward carries a complete invented-lemma ontology: `InventedLemma`, `IsInventedLemma`, `InventedLemmaProposition`, `InventedLemmaGoal`, `InventedLemmaProof`, `InventedLemmaStatus`, `InventedLemmaUtility`, `InventedLemmaCertificate`, `LookupInventedLemmaNodes`, `LookupInventedLemma`, `ReplaceInventedLemmaNode`, `DerivationUsesInventedLemma`.

The machine already: **invents lemmas** from bounded structural search (cubic linear factorisation, additive sum-of-squares), **validates them by an independent reconstruction identity** (exact division), tracks their **utility** — which is what "rent" means — carries a **certificate**, records **which derivations use them**, and **replays them across a cold checkpoint**.

That is the substance of ODR-6's Track II and much of CL3/CL4/CL6. It is not derivation-schema induction in the `schemata.py` sense; it is a parallel, already-integrated mechanism with a lifecycle, a utility gate and certificates. My ODR-6 §0 row calling induction *"the only genuinely research-risky task"* was wrong — **the risk is inverted again**: the mechanism exists and is tested; what does not exist is the **sealed adversarial acceptance** around it.

Two of Luna Max's demands turn out to have been satisfied by the repository already: the macro-not-axiom trust boundary (invented lemmas are propositions with proofs and certificates, checked by an independent identity) and the candidate-bearing rent gate (`cint-integrated-8b`).

---

## §5 Blocker: the carrier does not cold-boot

`main.PACK_PATHS` lists fourteen packs. `packs/` contains thirteen. **`mystery-micro.pack.yaml` is referenced but does not exist**:

```
FileNotFoundError: [Errno 2] No such file or directory:
'/home/user/cat_theo_machine/packs/mystery-micro.pack.yaml'
```

Reproduced by calling `boot_from_packs(MAIN.PACK_PATHS, MAIN._runtime_namespace())` directly. `cold` mode therefore cannot boot on the chosen carrier as it stands. (`number-theory.pack.yaml`, also absent from the base, **is** present — so this is one missing file, not a systematic gap.)

This must be resolved before dispatch: either the pack is supplied, or the reference is removed, and in either case the change is an INT-applied edit to `main.py` with a recorded reason.

---

## §6 Environment

Measured this session: Linux, CPython **3.11.2**, `gmpy2` **2.3.1**, `PyYAML` **6.0.3** (both reinstalled — **the sandbox resets between turns**, so the dependency install is part of every measurement run, not a one-off). Repository target remains Windows/Conda/Python 3.12.13 per `environment.yml`. Two known deltas to carry forward: interpreter 3.11 vs 3.12, and `gmpy2` 2.3.1 vs pinned 2.3.0.

---

## §7 What this does to the ODR-6 dispatch

| ODR-6 item | Stale verdict | Measured verdict on carrier |
|---|---|---|
| **CL1** approval seam | keystone, blocks everything | **keep, narrowed** — the session loop is already autonomous; the seam now covers the proof/compare path plus a new REPL site |
| **CL2** dual step checkers | needed | **keep, unchanged** — no `CheckDerivation`/`VerifyDerivation` exists; the only validation is `_derivation_reaches_goal` (endpoint equality) |
| **CL3** residual characterisation | needed | **keep, unchanged** — vocabulary confirmed absent on the carrier |
| **CL4** cold replay | on critical path | **downgrade** — the wire path passes 5/5; scope shrinks to the `SnapshotCodec` question |
| **CL5** teaching artifact | revised, pack format | **keep** — no ingress vocabulary; `talk`/`ingest` is the nearest existing path and must be inspected before CL5 is specified |
| **CL6** admission gate | build it | **mostly pre-built** — `activate_proposal` + safety floor + `approve`/`countersign`; becomes *verify the boundary*, not *construct it* |
| **CL8** sealed induction | the research-risky task | **rewrite** — invention exists; the day builds the **seal, the dual checkers, the mutation matrix and the ablation conjunct** around it, and grades `AUTO_SCHEMA_INDUCTION` against the invented-lemma mechanism rather than a schema mechanism |
| **F1** persistence repair | on critical path | **downgrade to a targeted probe** |
| — | — | **NEW:** the missing `mystery-micro.pack.yaml` blocks cold boot |

**The reframed one-day objective.** Not *"build a closed loop"* and not *"build induction"*, but:

> **Seal and adversarially verify the autonomous invention the machine already performs.** Freeze a build, show the lemma inventor producing a candidate under a sealed budget on a sealed corpus, with the candidate hashed before holdout exposure, both independent checkers validating every step of the resulting derivations, mutation controls rejecting, ablation restoring the original failure, and cold replay reproducing the verdicts — with the four legs reported as pre-tag acceptance and the claim graded separately from the integration claim.

That is a smaller, more honest, and more useful day than the one I specified — and it is aimed at the machine that exists rather than the one I was handed.
