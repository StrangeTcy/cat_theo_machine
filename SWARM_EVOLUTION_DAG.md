# Hyge Multi-Agent Swarm Evolutionary Trajectory & DAG Specification

This document specifies the evolutionary architecture, dependency DAG, worker allocation, and synchronization protocols for coordinating Arena agents evolving the Hyge Theorem Prover.

---

## 1. Architectural Scope: The 5 Dimensions & Infrastructure Substrate

The machine's capabilities and subsystems are partitioned into five core dimensions supported by a verified foundation:

1. **Substrate & Infrastructure**: Non-blocking hypergraph persistence, cold snapshot resume, cyclic graph serialization, and distributed RPC/mTLS mesh.
2. **Dimension 1 — FLT (Fermat's Last Theorem & Diophantine Proving)**: Higher Diophantine polynomial derivations, congruence projections, Cartesian domain sweeps, modular obstructions, primitive Pythagorean triplet parametrizations, and infinite descent on well-founded Peano naturals ($n=4$ quartic, $n=3$ Eisenstein UFD).
3. **Dimension 2 — IMO Problems (Olympiad Geometry, Algebra, Combinatorics, Number Theory)**: Multi-pass backward planning, auxiliary construction generation (circumcircles, angle chasing, projective collineations), Cauchy functional equations, and discrete combinatorial configurations.
4. **Dimension 3 — Engel's Heuristic Strategies**: Arthur Engel problem-solving principles (Invariance Principle, Monovariant/Semi-invariant termination measures, Extremal Principle, Box Principle, Checkerboard Coloring).
5. **Dimension 5 — Natural Language, Stories & Socratic Explanations**: Declarative surface-to-graph translation, bidirectional paraphrase equivalence, step-by-step mathematical proof story generation, and conversational concept explanations.
6. **Dimension 4 — Autonomous Self-Improvement & Closed-Loop Promotion**: Trace state extraction, invariant mining, candidate macro formation, Independent Checker B verification receipts, performance ablation trials, withheld negative holdouts, and atomic dual-ledger promotion.

---

## 2. Complete Swarm Evolutionary Trajectory DAG

```
═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
                               5-DIMENSION SWARM EVOLUTIONARY TRAJECTORY DAG
═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════

[PHASE 0: Substrate & Kernels] (FULLY PARALLEL — 5 WORKERS)
 ├── W1: [Infra: Persistence, Snapshot Codec & Crash Recovery] (persistence.py)
 ├── W2: [Infra: Distributed RPC, Work-Stealing & mTLS Mesh] (networking/)
 ├── W3: [Infra: Cartesian Playground & Domain Sweeper] (playground.py)
 ├── W4: [Dim 4: Independent Checker B & Receipt Kernel] (checker_b.py)
 └── W5: [Dim 5: Surface Grammar, Tokenizer & Lexicon Bridge] (surface_bridge.py)
      │
      ▼ (Sequential Gate: Substrate Verified & Green)
[PHASE 1: Domain Strategies & Proving Engines] (FULLY PARALLEL — 6 WORKERS)
 ├── W6:  [Dim 1: FLT Modular Projections & n=4 Descent Engine] ◄──────── W3
 ├── W7:  [Dim 1: FLT Cyclotomic / Eisenstein UFD Factorization] ◄─────── W3
 ├── W8:  [Dim 2: IMO Geometry & Auxiliary Construction Engine] ◄──────── W4
 ├── W9:  [Dim 2: IMO Combinatorics, Functional Equations & NT] ◄──────── W4
 ├── W10: [Dim 3: Engel Strategies (Monovariants & Invariants)] ◄──────── W3, W4
 └── W11: [Dim 4: Invariant Trace Miner & Candidate Evaluator] ◄───────── W4
      │
      ▼ (Sequential Gate: Domain Handlers & Receipt Generation Standardized)
[PHASE 2: Cross-Dimension Integration & Closed Loops] (PARALLEL INTEGRATION — 4 WORKERS)
 ├── W12: [Dim 4: Dual-Ledger Autonomous Promotion Loop] ◄─────────────── W11, W1
 │         (Closed loop: Trace ➔ Invariant ➔ Checker B ➔ Ablation ➔ Active Rules)
 ├── W13: [Dims 1+2+3: Multi-Pass Backward Planning Engine] ◄───────────── W6, W8, W9, W10
 │         (Stitches Engel heuristics, auxiliary points, and descent steps)
 ├── W14: [Dim 5: Proof Storyteller & Derivation Narrative Generator] ◄── W5, W4
 │         (Translates formal receipt hypergraphs into natural mathematical stories)
 └── W15: [Dim 5: Conversational Socratic Tutor & Concept Explorer] ◄──── W5, W12
      │
      ▼ (Sequential Gate: Closed-Loop Self-Improvement & Dialogue Operational)
[PHASE 3: Swarm Distributed Proving Mesh] (SYSTEM DEPLOYMENT — 2 WORKERS)
 ├── W16: [Distributed Heuristic Search & Partitioned Prover Swarm] ◄───── W2, W13
 └── W17: [Byzantine Ledger Consensus & Monotonic Snapshot Broadcast] ◄── W2, W12, W1
```

---

## 3. Worker Node Specifications & File Ownership

| Node ID | Worker Role | Dimension | Core Files / Modules | Inputs / Prereqs | Deliverable Artifacts |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **W1** | Persistence & Snapshot Codec | Infra | `persistence.py`, `snapshots/` | Core graph model | Monotonic snapshot codec, cold resume |
| **W2** | Distributed RPC & mTLS Mesh | Infra | `networking/`, `mesh.py` | Python stdlib sockets/TLS | Zero-copy hyperedge RPC, worker auth |
| **W3** | Cartesian Playground & Sweep | Infra / Dim 1 | `playground.py` | `math/peano.py`, `labels.py` | Irreducible $k$-ary domain products, projections |
| **W4** | Independent Proof Checker B | Dim 4 | `checker_b.py` | `core.py`, `proof.py` | Zero-trust receipt verifier, step auditor |
| **W5** | Surface Grammar & Lexicon | Dim 5 | `surface_bridge.py` | `graph_task.py`, `labels.py` | Declarative parser, render engine, concept defs |
| **W6** | FLT $n=4$ Residue Discovery | Dim 1 | `validation/test18_flt_residue_discovery.py` | W3 | Modulo 4 obstruction discovered live; parametrization descent open |
| **W7** | FLT $n=3$ Eisenstein Factorization | Dim 1 | `packs/flt_eisenstein.pack.yaml`| W3 | Eisenstein norm ring $\mathbb{Z}[\omega]$, cubic descent |
| **W8** | IMO Geometry & Aux Construction | Dim 2 | `packs/imo_geometry.pack.yaml` | W4 | Auxiliary point synthesizers, cyclic quads |
| **W9** | IMO Combinatorics & Func-Eq | Dim 2 | `packs/imo_algebra.pack.yaml` | W4 | Cauchy/d'Alembert equations, extremal sets |
| **W10**| Engel Monovariants & Invariants | Dim 3 | `packs/engel_strategies.pack.yaml`| W3, W4 | Semi-invariants, coloring partitions, box principle |
| **W11**| Invariant Trace Miner & Evaluator| Dim 4 | `invariant_miner.py`, `evaluator.py`| W4 | Trace state extractor, holdout regression gate |
| **W12**| Dual-Ledger Promotion Loop | Dim 4 | `promotion_ledger.py` | W11, W1 | End-to-end autonomous discovery & rollback ledger |
| **W13**| Multi-Pass Backward Planner | Dims 1,2,3 | `planner.py`, `graph_task.py` | W6, W8, W9, W10 | Decomposed goal scheduler, auxiliary search |
| **W14**| Proof Storyteller & Narratives | Dim 5 | `story_renderer.py` | W5, W4 | Formal receipt $\to$ LaTeX/Markdown mathematical story |
| **W15**| Socratic Dialogue & Tutor | Dim 5 | `dialogue.py`, `main.py` | W5, W12 | Interactive concept inspection, counterexample REPL |
| **W16**| Distributed Prover Swarm | Swarm | `search/distributed_engine.py` | W2, W13 | Partitioned frontier worker mesh, work-stealing |
| **W17**| Byzantine Ledger Consensus | Swarm | `consensus/ledger_sync.py` | W2, W12, W1 | Raft/BFT rule sync, monotonic version broadcast |

### 3.1 Substrate extensions added after this DAG was first published

These arrived during Phase 0/1 execution and are prerequisites or enablers rather than new worker slots:

| Extension | Owner | Files | Verified by |
| :--- | :--- | :--- | :--- |
| Hypergraph matching over graph language (see `HYPERGRAPH_MATCHING_SPECIFICATION.md`) | W1 / substrate | `matching.py`, `graph.py` | `validation/test17_hypergraph_matching.py` |
| Cartesian playground tensor evaluation & algebraic template discovery (see `PLAYGROUND_SPECIFICATION.md`) | W3 / W11 | `playground.py`, `invariant_miner.py` | `validation/test16_tensor_evaluation_mining.py` |
| Checker B over knowledge-rewriting (fact-list) steps and `FactsCover`-style goals | W4 | `checker_b.py` | `validation/test19_checker_b_knowledge_rewrite.py` |
| Hypergraph content persistence (`nodes` / `edges` roots in the snapshot codec) | W1 | `persistence.py` | `probes/hypergraph_roundtrip_probe.py`, `validation/test12_persistence_cold_resume.py` |
| Curriculum ladder (see `MATHEMATICAL_APPRENTICESHIP_LADDER.md`) | W11 / Dim 3 | `curriculum.py`, `curriculum/` | `validation/test10_graph_curriculum.py` |

---

## 4. Current Status Matrix

- [x] **W1 (Persistence & Snapshot Codec)**: Completed & verified in `test12_persistence_cold_resume.py` (now **10/10** probes). Re-opened and extended on this branch, with three defects found and fixed:
  - *Hypergraph content was never persisted.* The codec had no root for `graph.nodes` / `graph.edges`, so imported content silently came back empty after a cold resume while the kernel roots round-tripped fine. Both roots are now captured and restored; legacy snapshots without them fall back to `EmptyList`. Probes 9–10 and `probes/hypergraph_roundtrip_probe.py`.
  - *The tree-currency check was dead code.* `_is_current_tree` looked `IsTree` up in the runtime namespace, which never carries it (`trees.IsTree` is not re-exported into `machine`), so every non-empty root was judged legacy. Because `_restore_tree_root` uses the same check to decide whether to rebuild, **every boot paid a full rebuild of `all_rules`, `derivations` and `derivation_schemata`, and then rewrote the snapshot it had just loaded** — silently, shrinking the committed `hyge_snapshot_v8.json` from 18,164,108 to 3,413,614 bytes, and taking two passes to reach a fixed point. Asking the module directly fixes it: v8 now boots in **15.8 s instead of 31.2 s** and is **not rewritten at all**. Content was verified equivalent across the rewrite (`rule_order` 106 either way), so the shrink was format compaction rather than data loss — but a read must not mutate its source. Probe 8 pins the discriminator both ways: a modern `Tree` and `EmptyList` are current, a legacy `TreeNode` is not, so genuine migration still fires.
  - *Resave on upgrade is now announced and optional.* It prints what it is rewriting, and `HYGE_SNAPSHOT_UPGRADE_RESAVE=0` loads without touching the source file, so inspection and test runs can be non-mutating.
  - Capture is also O(1) per object rather than O(n²) — ~620 to ~16,000 objects/s — which matters for ingesting large foreign graphs.
  - Known limit: no snapshot in this repository exercises the legacy `TreeNode` migration end to end any more. `backup_hyge_snapshot_v4.json` is format version 1 and is rejected by the version check before any tree logic, and `hyge_snapshot_v9.json.bad` is version 3 with no `class` keys. The migration path is therefore covered by the discriminator probe, not by a full legacy boot.
- [x] **W3 (Cartesian Playground & Sweeper)**: Completed & verified in `test13_cartesian_playground.py` and `test16_tensor_evaluation_mining.py`; its mod 4 sweep is the FLT obstruction the machine discovers on its own in `validation/test18_flt_residue_discovery.py`.
- [x] **W4 (Independent Checker B)**: Completed & verified in `test5_checker_b_derivation_verification.py`; step verification also covers knowledge-rewriting (fact-list) steps and `FactsCover`-style knowledge goals, covered by `validation/test19_checker_b_knowledge_rewrite.py`.
- [x] **W5 (Surface Grammar & Lexicon)**: Completed & verified in `test11_surface_language_bridge.py`.
- [x] **W11 (Invariant Trace Miner & Evaluator)**: Completed & verified in `test7_candidate_evaluator_ablation.py` and `test8_invariant_trace_miner.py`.
- [x] **W12 (Dual-Ledger Promotion Loop)**: Completed & verified in `test9_autonomous_promotion_loop.py`.
- [x] **W14 (Proof Storyteller & Derivation Narrative Generator)**: Completed & verified in `test14_proof_story_narrative.py` (`story_renderer.py`).
- [x] **W13 (Multi-Pass Backward Planning Engine)**: Completed & verified in `test15_multi_pass_planner.py`.
- [~] **W6 (FLT $n=4$)**: The hand-authored `flt-quartic` pack was withdrawn as a hardcoding violation. What remains is machine-derived and verified in `validation/test18_flt_residue_discovery.py`: the Cartesian sweep discovers modulus 4, the machine's own arithmetic runs the complete residue case analysis (fourth powers are $\{0,1\}$ mod 4, two odd fourth powers give 2), the discovered obstruction names its own candidate lemma, and the promotion ledger refuses to ledger it without a Checker B receipt. The Pythagorean parametrization descent needed for the full theorem is not derivable by the current machinery and stays open.
- [ ] **W7 (FLT $n=3$ Eisenstein UFD Factorization)**: Ready for execution.
- [ ] **W8 (IMO Geometry & Auxiliary Construction Engine)**: Ready for execution.
- [ ] **W9 (IMO Combinatorics, Functional Equations & NT)**: Ready for execution.
- [ ] **W10 (Engel Strategies & Monovariants Pack)**: Ready for execution.
- [ ] **W15 (Conversational Socratic Tutor & Concept Explorer)**: Ready for execution.
- [ ] **W2 (Distributed RPC & mTLS Mesh)**: Ready for execution.
- [ ] **W16 / W17 (Distributed Prover & Byzantine Consensus)**: Dependent on Phase 2.

---

## 5. Agent Coordination Protocol & Invariant Rules

Every Arena agent working on this repository must strictly adhere to the following invariants:
1. **Repository & Branch**: Work exclusively on the branch your own session is pinned to, and never on another session's branch. (This rule was first published naming one specific branch, `arena/01a108cd-cat-theo-machine`, but every copy of this document — including the two on other branches — carried that same hardcoded name, so it was never a usable instruction. The invariant is one-branch-per-session, not one-branch-for-everyone.)
2. **Machine Representation Purity**:
   - Do not edit `core.py`.
   - Never use Python built-in lists, dicts, or Python bools in machine runtime code. All constructs must use `Pair`, `EmptyList`, `truth_value`, `false_value`, `Atom`, `Char`, and native labels.
   - Never use `isinstance`, `hasattr`, `type`, `__class__`, or `__new__`.
   - Counting and arithmetic must operate via Peano `Zero`, `SuccLabel`, and `GMPRep`.
3. **No Domain-Specific Hardcoding**: Do not hardcode problem targets or fixed heuristics in search or mining modules.
4. **Verification Requirement**: Every new worker module or pack must include an automated verification suite in `validation/` with $100\%$ green test results before promotion. There are currently **19** suites, `test1`–`test19`, each a standalone script. Run one with `PYTHONPATH=<repo-parent> python -u validation/testN_*.py` (the suites insert the package parent onto `sys.path` themselves and import as `cat_theo_machine.*`).
5. **Snapshot Root Invariant**: any new machine state that must survive a cold resume has to be registered as a root in `SnapshotCodec.capture()` and restored in `activate()`. Content added through the graph's `nodes`/`edges` context is now covered; state kept only in Python attributes is not, and silently evaporates on reload.
6. **Suite Slot Discipline**: `validation/` numbering is append-only. Two lineages independently claimed slots 15 and 16 for unrelated suites; the reconciliation below is what happened, and new work must take the next free number rather than reusing a taken one.

---

## 6. Lineage Reconciliation (2026-10-12)

This document existed in three divergent copies across branches. It was first published in `c0cc38d`, then the swarm's work forked at `4a5378b` into two lineages that never merged:

| Lineage | Branch tip | What it contributed |
| :--- | :--- | :--- |
| **A** | `arena/861455d0-cat-theo-machine` | The honest W6 record: the hand-authored `flt-quartic` pack was authored, then withdrawn as a hardcoding violation in `524de6f`, replaced by `test15_flt_residue_discovery.py`. Also Checker B knowledge-rewrite verification (`checker_b.py`, +58 lines) and `test16_checker_b_knowledge_rewrite.py`. |
| **B** | `arena/d09a2974-cat-theo-machine` | Chronologically newest. W13 and W14 completed, multi-premise forward derivation in `graph_task.py`, tensor evaluation in `playground.py`, algebraic template discovery in `invariant_miner.py`, hypergraph matching (`matching.py`, `graph.py`), and the three specification documents. Never saw A's withdrawal, so it still listed W6 as unstarted. |

**How they were reconciled on this branch:**

- **Base** is lineage B (newest, and a strict superset for `graph_task.py`, `invariant_miner.py`, `labels.py`, `playground.py`, `main.py`, `story_renderer.py`, `surface_bridge.py` — in every case B's changes replaced or extended A's).
- **`checker_b.py` is taken from A**, not B. B's version is A's minus knowledge verification: its only two "new" lines are the replacements for A's `_reaches` call sites. Taking "newest wins" here would have silently dropped the `FactsCover` goal matching and fact-list rewrite checking that `test5`/`test19` depend on.
- **`persistence.py` was identical on both lineages** (82 insertions, 21 deletions — the gmpy2 fallback, the four new optional roots `planner_state`/`graph_tasks`/`promotion_ledger`/`invariant_catalog`, and `_child_refs` constructor handling), so no merge was needed there. It is combined with this branch's `nodes`/`edges` fix and O(1) capture, which apply to disjoint regions.
- **Suite slot collision**: A's `test15`/`test16` were renumbered to **`test18_flt_residue_discovery.py`** and **`test19_checker_b_knowledge_rewrite.py`**, keeping B's `test15_multi_pass_planner`, `test16_tensor_evaluation_mining`, `test17_hypergraph_matching` in place. Internal banner strings were renumbered to match, and §3/§4 citations updated. The union is 19 suites.
- **W6 status** is A's `[~]` with B's completed W13/W14 retained, so the matrix now reflects both truths at once.
- **Excluded as generated junk**: `.pyc`/`__pycache__` files and the `snapshots/search_compare/run-*` comparison artifacts (80 files) that both lineages had committed. `snapshots/hyge_snapshot_current.json` was **kept** — it is a committed fixture that `test12` probe 2 requires, not an artifact; without it that probe fails.
- **Result**: all 19 suites pass on this branch, and `probes/hypergraph_roundtrip_probe.py` round-trips hypergraph content through a cold resume.

The two lineages are otherwise disjoint in code, so nothing was lost by this merge. Lineage A's FLT pack withdrawal is recorded rather than re-litigated: no quartic rule, solution constant, or named lemma exists in this tree.
