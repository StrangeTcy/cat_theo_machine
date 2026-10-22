# Hyge Multi-Agent Swarm Evolutionary Trajectory & DAG Specification

This document specifies the evolutionary architecture, dependency DAG, worker allocation, and synchronization protocols for coordinating Arena agents evolving the Hyge Theorem Prover.

Phases 0–3 (W1–W20) landed by 2026-10-15; their record is §2–§6. **Remaining work is §7 (five-dimension status) and §8 (Phase 4+ DAG).** W21–W27 and W30 have landed; W29 has reported a precise negative (test41); W33 landed 2026-10-21 (test45, §4); W27 and W30 landed 2026-10-22 (test39, test42, §4). The next unoccupied allocated suite slot is `test40` (W28). The two post-W22 heads — `arena/c58acfec-cat-theo-machine` (`0b80aed`: W23, W29) and `arena/f0572ef6-cat-theo-machine` (`8fac788`: W24–W26), both fast-forwarded from `arena/717c9822-cat-theo-machine` (`a548d7d`) on 2026-10-19 — were integrated on 2026-10-21 (§6.10); this branch descends from the first of them, via `arena/b94f5f2e-cat-theo-machine`, where W33 landed before the merge. A further parallel head, `arena/f42b3f12-cat-theo-machine` (`966e26f`, forked at W33), was integrated on 2026-10-22 after W27 landed (§6.11).

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

Phases 0–3 below are the original trajectory. They are **completed** (2026-10-15) except W6 closed as partial and W7 partial. Do not re-dispatch W1–W20. The continuation DAG is §8.

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

[UNPHASED, KERNEL — coordinator sign-off] W18: [NatValueIndex lookup cost, trees.py] ◄── none (opened by W6, §6.5)
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
| **W6** | FLT $n=4$ Residue Discovery & Descent | Dim 1 | `validation/test18_flt_residue_discovery.py`, `playground.py` (`PolynomialIdentityByGrid`, `ResidueTable`, `CongruenceClasses`), `packs/infinite-descent.pack.yaml`, `validation/test26_flt_descent.py` | W3 | Modulo 4 obstruction discovered live; descent reduced to one named hypothesis with each step labelled derived / evidenced / authored / missing (partial, closed) |
| **W7** | FLT $n=3$ Eisenstein Factorization | Dim 1 | `playground.py` (`RunPlaygroundFilteredPowerSweep`, `DiscoverSeparatingModulus`), `math/arithmetic.py` (`Ring*`), `validation/test20_flt_eisenstein_discovery.py` | W3 | Mod-9 obstruction discovered live, $N(1-\omega)=3$ derived; UFD and cubic descent open |
| **W8** | IMO Geometry & Aux Construction | Dim 2 | `constructions.py`, `packs/geometry-constructions.pack.yaml`, `planner.py` (`Construction`) | W4 | Goal-directed auxiliary-point schemas, slot `test21` |
| **W9** | IMO Combinatorics & Func-Eq | Dim 2 | `math/funceq.py`, `graph_task.py` (`ForwardDeriveFacts`), `packs/funceq-nt.pack.yaml` | W4 | Families 1–3 over the forward engine / miner / ledger (slot `test22`); pack-based functional-equation and parity slice (slot `test29`) |
| **W10**| Engel Monovariants & Invariants | Dim 3 | `packs/engel-strategies.pack.yaml`, `planner.py` (`Monovariant`, `SemiInvariant`, `Invariance`) | W3, W4 | Semi-invariants, colouring as invariance, box principle obligationed; suite slot `test23` |
| **W11**| Invariant Trace Miner & Evaluator| Dim 4 | `invariant_miner.py`, `evaluator.py`| W4 | Trace state extractor, holdout regression gate |
| **W12**| Dual-Ledger Promotion Loop | Dim 4 | `promotion_ledger.py` | W11, W1 | End-to-end autonomous discovery & rollback ledger |
| **W13**| Multi-Pass Backward Planner | Dims 1,2,3 | `planner.py`, `graph_task.py` | W6, W8, W9, W10 | Decomposed goal scheduler, auxiliary search |
| **W14**| Proof Storyteller & Narratives | Dim 5 | `story_renderer.py` | W5, W4 | Formal receipt $\to$ LaTeX/Markdown mathematical story |
| **W15**| Socratic Dialogue & Tutor | Dim 5 | `dialogue.py`, `main.py` (`live` fall-through, `load pack`), `labels.py` (+11) | W5, W12 | Concept inspection from loaded rules/definitions/ledger, claim REPL (Checker B / counterexample / undecided), structure-generated Socratic questions, ledger transparency; `validation/test24_socratic_dialogue.py` (85/85, ~45 s) |
| **W16**| Distributed Prover Swarm | Swarm | `search/distributed_engine.py`, `networking/jobs.py`, `main.py` (`swarm`, `mesh --swarm`) | W2, W13 | Partitioned frontier worker mesh, work-stealing; `validation/test27_distributed_prover_swarm.py` (51/51, ~340 s) |
| **W17**| Byzantine Ledger Consensus | Swarm | `consensus/ledger_sync.py` | W2, W12, W1 | Raft/BFT rule sync, monotonic version broadcast |
| **W18**| Kernel: `NatValueIndex` lookup cost | Infra | `trees.py` (`TreeLookup`, `TreePatriciaLookup`, `TreeInsert`), `math/peano.py` (`NatFromRep`) | none (kernel; coordinator sign-off) | `TreeLookup` miss in `O(key)`, not `O(entries)`; `validation/test30_nat_index_lookup_cost.py`; `test22`/`test26` wall clocks before/after. Brief: `delegation/W18-nat-index-lookup-cost.md` |
| **W19**| Neo4j dump → machine shards, decoded on Colab | Infra / ingest | `importers/split_apoc_export.py`, `colab/neo4j_dump_to_shards.ipynb`, `colab/README.md` §B | ingest (§3.1, §6.8) | Combined and bulk APOC exports → `nodes.csv`/`edges.csv` + shard plan; the Neo4j decode in a notebook; `validation/test32_neo4j_export_to_shards.py` (35/35, ~38 s, one shard booted and machine-counted). Brief: `delegation/W19-neo4j-dump-to-shards.md` |
| **W20**| Mesh beyond one filesystem (laptop behind a tunnel + Colab worker) | Swarm / Infra | `networking/artifacts.py`, `networking/framing.py` (`Duplex`), `networking/peer.py`, `networking/protocol.py`, `mesh.py` (`issue_bundle`), `main.py` (`mesh` switches), `colab/mesh_worker.ipynb`, `colab/README.md` §A | W2, W16 | `--artifacts wire` (inputs fetched / results pushed inside the connection, digest-named, authority-checked), `--no-inbound`, `--verify identity --expect`, `--advertise`, `--role issue` bundles; `validation/test31_wan_mesh_artifacts.py` (50/50, ~60 s). Brief: `delegation/W20-wan-mesh.md` |
| **W21**| Existential witness introduction | Substrate / Dim 1 | `graph_task.py`, `checker_b.py` | none (kernel off-limits) | Unbound replacement variables mint recorded witnesses; Checker B audits the introduction. Brief: `delegation/W21-witness-introduction.md`. Slot `test33` |
| **W22**| Algebraic rewriting (recorded grid proofs ✅) | Substrate / Dim 1 | `invariance.py`, `playground.py`, `checker_b.py` (new grid clause) | none | Grid-decided identities become Checker-B-verified derivations; symbolic normalisation remains open. Brief: `delegation/W22-algebraic-rewriting.md`. Slot `test34` |
| **W23**| Factorisation substrate & derived `NatLess` ✅ | Substrate / Dim 1 | `math/arithmetic.py`, `packs/nat-order.pack.yaml` | none | Partial natural / signed subtraction, exact quotient, gcd cofactors; successor and transitivity schemas conclude `NatLess`. Brief: `delegation/W23-factorisation-natless.md`. Slot `test35` |
| **W24**| Residue / divisibility schema wiring ✅ | Dim 2 | `packs/funceq-nt.pack.yaml` | W9 ✅ (edges already exist) | ✅ 2026-10-19: eight constant-free schemas (transitivity, gcd's two universal properties, commutativity, Euclid's lemma, residue addition and multiplication); facts are records of the machine's `Divides`/`Gcd`/`Modulo`/`IsCoprime` edges; Checker B verifies the transitivity step and the ledger promotes it; `test36` 41/41. Brief: `delegation/W24-residue-divisibility-wiring.md`. Slot `test36` |
| **W25**| Curriculum card loader ✅ | Dim 2/3/4 | `curriculum.py`, `labels.py`, `curriculum/` | none | ✅ 2026-10-19: markdown cards parse to machine records; two compile to graph tasks (held-out solved, decoy refused); 22 refused with reasons, 48 Ground 1 gaps reported; `test37` 62/62. Brief: `delegation/W25-curriculum-loader.md`. Slot `test37` |
| **W26**| Geometry remainder ✅ | Dim 2 | `constructions.py`, `packs/geometry-constructions.pack.yaml` | W8 ✅ W4 ✅ | ✅ 2026-10-19: three constant-free chord/angle schemas plus the `antipode-completion` construction; Checker B verifies the Thales step, the ledger promotes it (evaluator/ablation/holdout), four ablations; `test38` 49/49. Brief: `delegation/W26-geometry-remainder.md`. Slot `test38` |
| **W27**| Engel remainder ✅ | Dim 3 | `invariant_miner.py`, `planner.py`, `labels.py` (pack untouched) | W10 ✅ | ✅ 2026-10-22: two unnamed instances close — Euclid-by-subtraction `Terminates`, chameleons `Unreachable`×3 — on transition-verified measure/observable facts; the chameleon observable is *mined* (10 certified / 42 refuted, ablation separates nothing); the planner proposes strategy methods from declarations and supplied obligations discharge in `PlannerRun`; root closure inside search is pinned as not-landed (two isolated `search/` blockers); `test39` 53/53. Brief: `delegation/W27-engel-remainder.md`. Slot `test39` |
| **W28**| FLT $n=3$ UFD + cubic descent | Dim 1 | `playground.py`, `math/arithmetic.py` | W21, W22, W23, W7 `[~]` | Unique factorisation scaffolding used, cubic descent attempted. Brief: `delegation/W28-flt-n3-ufd-descent.md`. Slot `test40` |
| **W29**| FLT $n=4$ `EveryStateMoves` retry — precise negative | Dim 1 | `validation/test41_flt_n4_everystate.py`; test26 unchanged | W21–W23 ✅, W6 `[~]` | 61/61; adapter repaired and finite numeric fixture solved, but no universal movement producer in all 206 registered rules. The descent remains open. Brief: `delegation/W29-flt-n4-everystate.md`. Slot `test41` |
| **W30**| Domain packs through the closed loop ✅ | Dim 4 | `promotion_ledger.py`, `evaluator.py`, `invariant_miner.py`, `labels.py` (`checker_b.py` unchanged) | W12 ✅, W24–W27 ✅ | ✅ 2026-10-22: one shared ledger promotes funceq transitivity, geometry Thales and both Engel closers (versions 1–4); the two W27 Engel chains earn multi-step Checker-B receipts; gate-4 provenance re-verifies ground-observable certificates (forged refused); withheld-rule ablation on two domains; multi-rule macros and premise-consumption pinned as the loop's current shape; `test42` 42/42. Brief: `delegation/W30-domain-promotion-loop.md`. Slot `test42` |
| **W31**| Tutor/story beyond arithmetic | Dim 5 | `dialogue.py`, `story_renderer.py` | W15 ✅ W14 ✅ | Claims and stories over geometry/Engel/FLT vocabulary. Brief: `delegation/W31-dialogue-beyond-arithmetic.md`. Slot `test43` |
| **W32**| Swarm unit-boot cost | Infra | `persistence.py`, `search/distributed_engine.py` | W16 ✅ | Cut the 12–30 s per-unit boot that makes swarm speedup negative. Brief: `delegation/W32-swarm-boot-cost.md`. Slot `test44` |
| **W33**| Mesh reconnect attempt accounting ✅ | Infra | `networking/peer.py` | W2 ✅ W16 ✅ | ✅ 2026-10-21: a severed link makes a member suspect for `reconnect_grace` (default 5 s) — no attempt charged, no terminal record — and only an unresolved suspect becomes `member-lost`; goodbye/heartbeat-timeout stay immediate; the offer watchdog does not charge a suspect owner either. `test45` 20/20. Brief: `delegation/W33-mesh-reconnect-accounting.md`. Slot `test45` |

### 3.1 Substrate extensions added after this DAG was first published

These arrived during Phase 0/1 execution and are prerequisites or enablers rather than new worker slots:

| Extension | Owner | Files | Verified by |
| :--- | :--- | :--- | :--- |
| Hypergraph matching over graph language (see `HYPERGRAPH_MATCHING_SPECIFICATION.md`) | W1 / substrate | `matching.py`, `graph.py` | `validation/test17_hypergraph_matching.py` |
| Cartesian playground tensor evaluation & algebraic template discovery (see `PLAYGROUND_SPECIFICATION.md`) | W3 / W11 | `playground.py`, `invariant_miner.py` | `validation/test16_tensor_evaluation_mining.py` |
| Checker B over knowledge-rewriting (fact-list) steps and `FactsCover`-style goals | W4 | `checker_b.py` | `validation/test19_checker_b_knowledge_rewrite.py` |
| Hypergraph content persistence (`nodes` / `edges` roots in the snapshot codec) | W1 | `persistence.py` | `probes/hypergraph_roundtrip_probe.py`, `validation/test12_persistence_cold_resume.py` |
| Curriculum ladder (see `MATHEMATICAL_APPRENTICESHIP_LADDER.md`) | W11 / Dim 3 | `curriculum.py`, `curriculum/` | `validation/test10_graph_curriculum.py` |
| CSV-to-hypergraph importer for decoded Neo4j exports (nodes/edges roots, machine-counted) | W1 / substrate | `importers/csv_to_hypergraph.py` | `probes/importer_roundtrip_probe.py` (24k edges out and back), `probes/imported_reasoning_probe.py` (20,000 facts derived from imported content through `matching.Rewrite`) — probes, not a `validation/` slot |

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
  **Remainder (2026-10-14, slot `test26`, `validation/test26_flt_descent.py`, 43/43, ~115 s before W18, 38 s after):
  done-definition rung 2, partial, closed with a demonstrated negative account.** No pack
  carries a quartic rule, a parametrisation, a constant or a lemma about squares; the only
  authored schema is a strategy axiom, `packs/infinite-descent.pack.yaml` (one rule,
  `Terminates(p) ∧ EveryStateMoves(p) → NoStates(p)`, declared as authored on the same footing
  as `monovariant_terminates`). Two generic decision procedures were added to `playground.py`
  and are the reusable yield: `PolynomialIdentityByGrid` decides an identity between two
  polynomial expression terms (`ExprAdd`/`ExprMul`/`ExprPow` over Chars and nats) by
  evaluating both sides with the machine's `Add`/`Multiply` on the grid `{0..d_i}` per
  variable, `d_i` a structural degree bound — sound by the finite-grid identity lemma, so a
  truth verdict is a proof over Z, not evidence (the suite shows the grid size is load-bearing:
  `a²+a` and `2a` agree on `{0,1}` and the bound forces the third point that separates them);
  `ResidueTable` / `CongruenceClasses` run the exhaustive residue case analysis `test18` did
  inline, as records. Each step of Fermat's descent is then labelled. *Derived*: the
  Pythagorean square identity in additive form `p² + 4(p+n²)n² = (p+2n²)²` (15 grid points),
  `x⁴ = (x²)²`, odd squares ≡ 1 (mod 4), and `1 + n² ≡ m² (mod 4)` holding exactly on
  `m` odd / `n` even — the modulus being the one the sweep re-discovers, not a constant; and a
  2-step derivation `monovariant_terminates`, `infinite_descent` from `Monovariant`,
  `AllMovesDecrease`, `BoundedBelow`, `EveryStateMoves` to `NoStates(descent)`, Checker-B
  verified, rejected against the wrong goal, and not findable without `EveryStateMoves`.
  *Evidenced only* (machine arithmetic on bounded sweeps, refused by the ledger, version 0):
  every primitive triple with an even leg in range is `(m²−n², 2mn, m²+n²)` for a coprime
  opposite-parity pair (5 instances, 2 beyond the bound the first 3 came from — and the suite
  says the parametrisation is a human-stated candidate the machine neither discovered nor
  derived), coprime factors of a square are squares (6 instances; the non-coprime
  counterexample `(2, 8)` shows the hypothesis is load-bearing), the measure drops along the
  would-be descent (6 family pairs). *Missing, demonstrated*: no loaded schema has a
  replacement variable unbound by its premises, so no rule can introduce the witnesses a
  descent step constructs (the `m, n`, the `u, v, w`) — existential witness introduction is
  absent from the knowledge-rewrite format; `invariance.RewriteEquals` with the default
  distributivity/associativity rules is stuck on the identity the grid decided — ring
  normalisation is absent; `math/arithmetic` has no subtraction, root or factorisation edge,
  so the coprime-square-factors lemma (unique factorisation) has no substrate; no loaded
  schema concludes a `NatLess` fact, so the decrease is evidenced, not derived. The theorem is
  therefore reduced to `EveryStateMoves(descent)` — "from every primitive solution a smaller
  one can be built" — whose discharge is exactly the missing list. Nothing is promoted and the
  skeleton derivation is not submitted: its receipt would certify the implication, not the
  theorem. The brief's own ranking applies: this is a precise partial, not a positive hiding an
  authored step.
  **W29 continuation (2026-10-19):** `test41_flt_n4_everystate.py` retries this
  missing list after W21–W23; initially 54/54, then 56/56 after the endpoint
  repair, now 61/61 with a bounded numeric witness probe; precise negative,
  ledger 0. Supplemental test46 validates bounded numeric search (185/185). The grid identities
  now have Checker-B receipts, but anonymous allocation is not arithmetic witness
  solving and gcd extraction is not a square-root/parametrisation theorem. A new
  value/identity mismatch was found in computed predecessor-order facts; the adapter
  follow-up below now interns the computed endpoint. See §4 W29; EveryStateMoves
  and the full descent remain undischarged. test26 is unchanged.
- [~] **W7 (FLT $n=3$ Eisenstein UFD Factorization)**: Partial, machine-derived, verified in
  `validation/test20_flt_eisenstein_discovery.py` (all sections green, ~92–98 s) — slot 20, from
  `arena/87d8295b-cat-theo-machine` (`808f299`). `RunPlaygroundFilteredPowerSweep` /
  `DiscoverSeparatingModulus` in `playground.py` take the exponent and both domain filters as
  parameters: with power 3 over the coprime-to-3 domain the machine's own flags show moduli 2–8 do
  not separate the cube image from the unit pair-sum image and 9 does (unit cubes $\{1,8\}$, unit
  pair-sums $\{0,2,7\}$); with power 2 and an odd-pair filter the same sweep rediscovers `test18`'s
  modulus 4. Generic quadratic-ring scaffolding over the kernel's `Whole` integers
  (`RingAdd` / `RingMultiply` / `RingConjugate` / `RingNorm` in `math/arithmetic.py`, parameterised
  by $\omega^2 = p + q\omega$) computes $\omega^2 = -1-\omega$, derives $N(1-\omega)=3$ by conjugate
  product with no norm formula written anywhere, checks multiplicativity on a witness set, and
  derives the Gaussian norm 13 under a second relation. The machine links its two discoveries
  ($9 = N(1-\omega)\cdot N(1-\omega)$ by its own multiplication). The promotion ledger refuses the
  discovered candidate without a Checker B receipt, as in `test18`. No cube identity, named lemma
  or solution constant in the tree; no pack added. *Not derived, not claimed*: unique
  factorisation in $\mathbb{Z}[\omega]$, the infinite descent, the full $n=3$ theorem.
- [x] **W8 (IMO Geometry & Auxiliary Construction Engine)**: Completed & verified in
  `validation/test21_imo_geometry_constructions.py` (36/36 checks, ~152 s) — slot 21, the one
  `delegation/README.md` pre-allocates to this worker.
  - *The generator is goal-directed but problem-free.* `constructions.py` carries construction
    schemas as machine terms — a goal shape, soundness premises, effect facts — and
    `ConstructionProposals` instantiates them through the machine's own matching (`Match`,
    `JoinPremises` seeded with the goal's bindings, `MergeBindings`), minting one anonymous
    `Thingy` per proposal as the auxiliary object. There is no table of problems and no named
    auxiliary point; the pack's vocabulary is pinned by an explicit allowlist (a rule leaf is a
    pattern variable or one of the ten declared labels, nothing else), and the same pin runs over
    the schemas themselves. Two schemas ship: bisector completion (an `EqualAngle` goal over a
    corner-symmetric angle pair, sound only when both flanks carry the same length quantity) and
    circumcircle completion (an `OnCircle` goal over a triangle vertex).
  - *End to end, without the auxiliary object being named.* Base angles of an isosceles triangle:
    the figure carries `Triangle(P,Q,R)` and two flanks sharing one length quantity; the goal
    `EqualAngle(Angle(P,Q,R), Angle(P,R,Q))` draws exactly one proposal; the minted foot induces
    `PointOn` (both segment orientations), `BisectorFrom` and two sub-triangles; and the generic
    schema pack closes the goal through the bisector definition, SAS self-congruence, the ray
    identity on the constructed foot, and equality symmetry/transitivity. Withhold the proposal
    and the goal does not close; scalene the figure and nothing is proposed; aim the goal
    elsewhere (a length) and no schema fires.
  - *Through the planner, not around it.* Proposals become `Construction` method terms
    (`planner.py`, dispatched beside the other method heads); their effects are the obligations,
    the goal is the conclusion, and `PlannerRun` records one alternative per proposal with one
    child per obligation. With no generator there is no construction alternative.
  - *New labels* (append-only, snapshot-registered): `EqualAngle`, `BisectorFrom`, `PointOn`,
    `CircumcircleOf`, `OnCircle`, `ConstructionSchema`, `ConstructionMethod`.
    `packs/geometry-constructions.pack.yaml` registered in `main.py:PACK_PATHS` (path only, no
    agenda case). `core.py` untouched.
  - *Honest scope note*: this branch carries no `checker_b.py`, no ledger, no `evaluator.py`, no
    `graph_task.py` and no `playground.py`, so the done-definition's Checker-B receipt, ledger
    record, evaluator ablation and figure sweeps are **not met here and are not claimed**. The
    brief's wider construction classes (angle chasing beyond the bisector, projective
    collineations, cyclic quadrilateral conclusions) are open: the two shipped schemas are the
    proof that the pipeline works, not the catalogue.
    *Integration note (2026-10-13)*: those modules are present on the integrated branch now; the suite
    still does not exercise them, so the items above remain unmet until someone extends it.
    *W30 note (2026-10-22)*: Checker-B receipt, ledger record and evaluator ablation for this
    pack's schemas are now met -- first by W26 (`test38`), and again on the shared cross-domain
    ledger in `test42`; figure sweeps remain unmet.
  - *Not done*: no cyclic-quadrilateral conclusion schema yet; the circumcircle schema stops at
    vertex incidence and does not yet feed chord/angle facts back into goals.
- [x] **W9 (IMO Combinatorics, Functional Equations & NT)**: Two independent deliverables
  landed, both kept (see §6.2 for the slot collision).
  - **(a) Families 1–3 over the code line** — `validation/test22_imo_combinatorics_funceq.py`
    (sections [1]–[32], ~160–220 s), from `arena/87d8295b-cat-theo-machine` (`b087253`…`a02555b`,
    audited twice). *Family 1*: a generic multi-premise rule over an opaque fact hypergraph
    (`residue(x,r) & residue(y,r) & distinct(x,y) -> shares_class(x,y)`) is closed by the machine's
    own forward engine; `invariant_miner.py` finds class-assignment persistence as the terminating
    invariant and refutes the rival; `UnreachabilityProverByInvariant` proves the injective decoy
    unreachable; the macro is Checker-B-verified, holds on 3+3 held-out instances and is promoted
    through the ledger with the certificate as provenance. *Family 2*: Cauchy's equation is
    **data** (an `ExprEq` term over `Apply`/`ExprAdd`/`ExprMul`); `math/funceq.py` compiles any
    equation into a unary rewrite schema, the machine closes $f((x+y)+z)$ to the expanded normal
    form with machine-checked termination evidence, the multiplicative decoy is refused, and the
    multiplicative equation goes through the same compiler unchanged. *Family 3*: a generic
    divisibility theory over `GMPRep` nats (gcd/coprime/transitivity rules) closed by the forward
    engine; a sweep over $(a,b,c)\in 2..8$ derives all 45 positive-class triples and refuses all
    110 decoys (37 true-but-underivable triples counted as the theory gap, stated). `graph_task.py`
    `ForwardDeriveFacts` now instantiates fact-list replacements fact by fact in both the unary and
    multi-premise paths (previously a one-premise rule embedded its whole fact list as one bogus
    term). *Measured, not asserted* ([32]): the closure engine is a single-chain saturator — it
    instantiates the first join per depth step and is blind to a second collision in the same
    configuration — so every derivation here is soundness, not completeness. *Checked, not
    asserted* ([31]): all 24 curriculum cards are blueprint-only, no loader exists, and their
    constructors (`IntegerLabel`, `ResidueLabel`, …) are absent, so curriculum held-out evidence is
    impossible on this code line. One host introspection (`type(term).__name__` for a label's
    name) is justified under the conjunctive exception in the suite. No kernel edits, no new labels.
  - **(b) Pack-based functional-equation and parity slice** —
    `validation/test29_imo_funceq_parity_pack.py` (26/26 checks, ~125–170 s), from
    `arena/500df21f-cat-theo-machine` (`5a546ec`), authored as slot 22 and renumbered to **29** on
    integration. Its own record follows.
  - *Family 2 (functional equations) delivered.* The equation is an input fact — `CauchyAdd(f)`
    / `CauchyMul(f)` — and `packs/funceq-nt.pack.yaml` (25 rules, registered in
    `main.py:PACK_PATHS`) derives the consequences: additive Cauchy down to $f(0)=0$ (the free
    $(0,0)$ instance, then the shared-term cancel — the one classical lemma the slice assumes as
    a schema, exactly as a geometric worker assumes SAS), instances at whatever values the
    instance supplies and never at values it does not, multiplicative Cauchy down to $f(1)=1$
    under a **visible** `NonTrivial(f)` input — without it the zero function is a counterexample
    and the schema refuses, which the suite pins as a negative control. The unit chain needs
    argument-position normalisation ($1\cdot 1$ inside $f(\cdot)$), which is its own schema pair.
  - *Family 3 delivered as a parity-algebra slice.* The machine's own `Add` / `Multiply` edges
    compute the naturals (their constructor chains were verified: $2+3$ walks five successors
    onto a nullary Zero), the sum/product is recorded as a `NatSum` / `NatProduct` fact, and the
    schemas derive the parity the computation must carry — and the suite verifies the machine's
    sum against its own `Count`. The wrong parities are pinned unreachable. The machine has no
    modulo, subtraction or division, so residues beyond mod 2 and divisibility chains are open.
  - *Family 1 out of scope, declared.* `graph_task.py`, `invariant_miner.py`, `evaluator.py` and
    `curriculum.py` did not exist on the authoring branch, so the combinatorial-configurations family, the
    held-out/decoy evidence, the ablation and the Checker-B/ledger items of the done-definition
    are **not met by this suite and are not claimed** (the brief's partial-coverage clause).
    On the integrated branch deliverable (a) covers family 1 and those items.
    *W30 note (2026-10-22)*: the funceq/NT derivations also run through the loop as a domain
    pack (W24 `test36`; shared-ledger promotion in `test42`).
  - *New labels* (append-only, snapshot-registered): `CauchyAdd`, `CauchyMul`, `NonTrivial`,
    `Value`, `NatSum`, `NatProduct`. `core.py` untouched.
  - *Machine finding recorded during this worker's session*: no machine predicate answers
    atomness — `IsAtom` accepts any non-pair, non-edge host object and never consults the
    registry it is handed, and `GetConstructor` returns the empty constructor for every
    non-pair object, machine or host alike. Consequences: structural genericity pins must walk
    argument/cons positions with `IsPair`/`IdentityCompare` (as this suite and `test21`/`test23`
    now do), and `packs.py`'s `sym` resolution would admit a host callable named in a pack —
    coordinator's attention drawn; kernel off-limits to workers.
  - *Not done*: d'Alembert-type equations (they need a minus/subtraction term the machine's
    arithmetic does not carry), residues beyond parity, divisibility, extremal sets, and
    everything catalogued under the family-1 scope note above.
- [x] **W10 (Engel Strategies & Monovariants Pack)**: Completed & verified in
  `validation/test23_engel_strategies.py` (80/80 checks, ~70 s) — slot 23, the one
  `delegation/README.md` pre-allocates to this worker; slots 20–22 belong to W7/W8/W9.
  `packs/engel-strategies.pack.yaml` states the strategy principles once, over symbolic problems,
  measures and move sets: invariance (`thread_preserving_moves` / `preserving_moves_empty` / `step`
  + `invariant_obstruction`), monovariants (`thread_decreasing_moves` / `decreasing_moves_empty` /
  `step` + `monovariant_terminates`), semi-invariants (`thread_non_increasing_moves` /
  `non_increasing_moves_empty` / `step` + `semi_invariant_terminates`) and the extremal principle
  (`extremal_choice`, whose direction is a supplied fact, never a min/max constant). The pack
  carries ontology and generic schemas only — no problem instance, no examples block, and no
  agenda cases in `main.py` (the brief names that style a standing §5.3 violation; the two agenda
  hooks this worker first added there are gone).
  - *Universality by fixpoint recursion, not enumeration.* Termination and preservation quantify
    over **every** move, and Horn rules cannot. The universal is reached the way the machine
    reaches every other universal: `MoveSet` is threaded into a `MovesDecreasing` /
    `MovesPreserving` / `MovesNonIncreasing` obligation, one rule peels the head off the list
    while the head discharges its own premise, and the empty list closes the case. No list length
    is ever assumed — a five-move problem and a one-move problem run the same three rules, an
    earlier version that spelled out lengths 1/2/3 was a Python-flavoured enumeration and was
    replaced by this recursion — and a single move that does not discharge stops the recursion
    dead. A symbolic move set cannot be peeled and must supply the universal itself.
  - *The semi-invariant is honestly weaker than a monovariant.* It owes `NonIncreases` per move
    (not a strict drop) plus the fact `EventuallyDecreases(p, m)` — the "eventually" is a premise,
    i.e. an obligation, because how a process is seen to drop eventually is arithmetic about that
    process. An earlier schema consumed `StrictlyDecreases`, which made the term a monovariant
    with a different name; a schema that counted steps to prove the drop would hardcode the very
    argument it is meant to licence.
  - *The box principle is obligationed, not asserted.* From `|D| > |C|` and a total map, "two
    pigeons share a box" is arithmetic the machine should establish by Peano counting, not a
    conclusion it should be handed; an earlier `box_principle_collision` rule did exactly that and
    was withdrawn. The existing `Pigeonhole` planner method already obligationes finiteness,
    totality, both cardinalities and the strict inequality, and the suite pins that no pack rule
    concludes a collision and that the facts alone manufacture none.
  - *Checkerboard colouring is not a sixth principle*: a colouring argument is an invariance
    argument whose phi is a parity, and `invariant_obstruction` discharges it once the 2-colouring
    and its parity observable are supplied.
  - *Planner*: `Monovariant`, `SemiInvariant` and `Invariance` method terms with their obligation
    and conclusion records (before this only `Pigeonhole` and `Extremal` produced children), all
    nine edges now exported. A literal move set is obligationed move by move, a symbolic one as a
    single universal; the obligation records never claim the universal they cannot phrase.
  - *New labels*: `Monovariant`, `SemiInvariant`, `StrictlyDecreases`, `AllMovesDecrease`,
    `AllMovesNonIncrease`, `NonIncreases`, `EventuallyDecreases`, `MoveSet`, `MovesDecreasing`,
    `MovesPreserving`, `MovesNonIncreasing`, `Reading`, `Terminates`, `Measure`, `Direction`, plus
    the `MonovariantMethod` / `SemiInvariantMethod` / `InvarianceMethod` method heads, registered
    in `labels.py` (append-only) and in `SNAPSHOT_SYMBOL_NAMES`; the suite round-trips all of them
    through `SnapshotCodec`. `core.py` untouched.
  - *Honest scope note*: this branch carries none of the modules the W10 brief's "what already
    exists" section assumes (`playground.py`, `invariant_miner.py`, `evaluator.py`,
    `curriculum.py`, `checker_b.py`, `promotion_ledger.py`), so the parts of its done-definition
    that need discovery, held-out/decoy evidence, ablation or a Checker B receipt are **not met
    here and are not claimed**; the suites they live in were not on the authoring branch either, so
    its "existing suites stay green" check covered the four that were.
    *Integration note (2026-10-13)*: those modules are present on the integrated branch now; the suite
    still does not exercise them, so the items above remain unmet until someone extends it.
    *W30 note (2026-10-22)*: discovery landed with W27 (`test39`), held-out/decoy evidence with
    W25 (`test37`), and Checker-B receipts + ledger promotion + withheld-rule ablation for the
    strategy closers with W30 (`test42`); what remains open is root closure inside ordinary
    search (test39 §[5]).
  - *Not done*: no domain pack drives these rules from a real Engel problem yet; nothing
    verifies a `StrictlyDecreases` / `NonIncreases` / `Preserves` claim; the brief's discovery
    layer (mining a measure or an observable rather than being handed one) is open; and the
    strategy rules do not fire during ordinary search — nothing yet proposes them to the search
    the way the planner methods do.
- [x] **W15 (Conversational Socratic Tutor & Concept Explorer)**: Completed & verified in
  `validation/test24_socratic_dialogue.py` (85/85 checks, ~45 s; a scripted deterministic
  conversation). `dialogue.py` is a *reader* of the machine, not a second knowledge base: no
  per-concept prose lives in it (pinned by the suite — the probe vocabulary and the bridge's
  definition sentences appear nowhere in its source). **Concept inspection** builds an index
  from the loaded packs' `rule_map` (rule id → rule, premises/replacement walked structurally;
  label class names split into words, Char symbols), the packs' `phi`, the bridge's
  `SurfaceDefinition` records (via `QueryConceptDefinition`) and `promotion_ledger` entries;
  `SemiInvariant` — defined nowhere in prose — is explained from `engel-strategies`'
  `semi_invariant_terminates`/`thread_non_increasing_moves`, `parity` from its definition record
  with (honestly) no rule, `quaternion` as not represented, and a tutor over fewer packs knows
  less. **Claims** (a small grammar over naturals: `+`, `*`, even/odd/divides/coprime, `if … then`,
  `implies`, `whenever`, `for every n ,`; paraphrases meet in one machine record via
  `proof.SameKnowledge` + `Compare`, and the rendering re-parses to an equivalent record) are
  judged three ways, distinguishably: **verified** only when a derivation found by a bounded
  iterative-deepening search over `proof.KnowledgeRewriteSuccessors` is accepted by
  `checker_b.VerifyDerivation` (the suite re-runs the checker itself and shows it rejecting the
  same derivation against the wrong goal); **refuted** by a counterexample found by sweeping
  `playground.BuildNatRange`/`ProductOfDomains` with `math/arithmetic` edges (re-evaluated in the
  suite); **undecided** with both pieces of evidence attached — a true claim no loaded rule proves
  (`Even(a) ⇒ Odd(a+1)`; divisibility transitivity) stays undecided and bounded evidence is never
  upgraded to a proof. **Socratic questions** come from `BackwardObligations` (rules whose
  replacement matches the goal, premises bound through the goal and the known facts, the
  JoinPremises discipline), ranked by open premises and tagged with the curriculum rungs
  (`Rung2Join` choose a rule → `Rung1Retrieval` one missing premise at a time, no repetition →
  `Rung4Derivation` apply and `check`; `Rung6Negative` when no rule concludes the goal); the same
  machinery runs over an Engel-pack goal (`Terminates(p)` from `Monovariant(p,m)`, with `assume
  Name(args)` in the rules' own vocabulary) and ends in a Checker-B verified
  `monovariant_terminates` step. **Ledger**: each proposal's status (receipt present / refuted
  with witness / lacks a receipt and the premise that would earn one, e.g. `Odd(1)`), and real
  `PromotionLedger` entries with status and receipt presence. REPL: `main.py live` routes its
  fall-through through the tutor before the pre-existing bridge path (explicit fall-through keeps
  “no, I can't prove that”), plus a `load pack <name>` command. Boundary: a label is named by its
  class name and a Char read by calling it, in two helpers (`_label_name`, `_char_text`) — the
  suite counts the `type()` calls. Known limits: the claim grammar is arithmetic-only (other
  goals enter through `Tutor.set_focus_goal` / `assume`); the ledger's ablation/holdout gates are
  reported as not run, not simulated; search depth 4, sweep bound 12 (≤ 2000 assignments).
- [x] **W2 (Distributed RPC & mTLS Mesh)**: Completed & verified in `validation/test25_rpc_mtls_mesh.py` (48/48, ~97 s, phases: mTLS 1.4 s, protocol 15.7 s, guards 0.5 s, real jobs 47 s, file transport 33 s) — framed RPC over mutual TLS with a certificate authority generated in Python, refusal negatives (unknown CA, untrusted server, expired leaf), membership over loopback, scopes and leases with monotonic sequences, peer-to-peer work stealing (proved once with stub jobs over real mTLS sockets and once with real subprocesses, where a queued search job is stolen from under a busy peer), and real `search` jobs over real `main.py mesh` subprocesses, compared against the same job run alone in a fresh process. The manifest/result contract is the one the file transport already used, so a mesh job is a `search-worker` job by construction (`search-worker` stays selectable and is regression-covered in the same suite). Clean shutdown is covered too: a closing connection no longer discards a queued goodbye, and a `deferred` result counts as a result rather than a failure. The crash clause is pinned from both sides — a killed peer's job is re-dispatched, and where nothing is left to re-dispatch to it ends as a terminal `failed` record naming `reason="worker-lost"`, so a job is either recovered or reported and never quietly dropped. Its own transport defects — a heartbeat that answered itself (an unbounded storm), a frame reader that read a TLS want-read as a clean EOF, and a result projection that pretty-printed proofs instead of reading the snapshot graph — were found and fixed on the way; see `networking/README.md`.
- [x] **W16 (Distributed Heuristic Search & Partitioned Prover Swarm)**: Completed & verified in
  `validation/test27_distributed_prover_swarm.py` (51/51 checks, ~340 s on 2 vCPU; phases: plan
  81 s, in-process partition 12 s, baseline 82 s, swarm 98 s, kill 52 s). Engine and CLI came from
  `arena/abf4a212-cat-theo-machine` (`532ef41`…`223a023`); the suite was written on the integrated
  tree. What the suite measures: `main.py swarm --role plan` expands `engel_e2` once and writes one
  unit snapshot per frontier node (4); disjointness and coverage are asserted from the plan's own
  data (distinct digests, indices 0..n-1, shard sizes summing to the frontier, resharding k=1..4 a
  bijection onto the same units) and then *reproduced in a different process* — the baseline
  snapshot is booted in the suite and `partition_frontier` returns the same digests, shards and
  ids. The whole-frontier baseline runs alone; two `mesh --swarm` workers over real mTLS run the
  four units; `merge` crowns unit 0 and its plan digest (`2ad79637693297dd`) and proof-cost digest
  (`cda29f2b48da3570`) equal the baseline's on every semantic key — equality of the proof, not
  merely success; the other three units report `failure-search`, not silence. One unit was
  stolen in the healthy run and its result is identical to the same unit run locally in the kill
  run (stolen work == local work, measured). Kill test: a worker is SIGKILLed 3 s into a unit; the
  coordinator records `member-lost`, `job-redispatched` (“worker lost mid-job, attempt 2”), the
  survivor hands in a real (non-provisional) result, and each unit's result equals the same unit's
  result in the healthy run. *Findings, reported not tuned*: speedup **0.84×** (baseline 82 s vs
  swarm 98 s — on `engel_e2` the proof lives in one branch, so the critical path is one unit's
  boot plus search, and a second worker only adds contention on 2 vCPU); memory high-water
  ~235 MiB per worker, 259 MiB largest child. Machine purity pinned: frontier nodes and states
  stay machine terms, unit records hold only str/int. **Defect found and fixed on the way** (see
  §6.3): on the integrated tree every unit snapshot was unbootable — the spawned restore worker
  in `persistence.py` died with “maximum recursion depth exceeded” while *pickling* `all_rules`
  back to the parent, because the merged packs made the rule list longer than the default
  1000-frame pickler recursion allows. *Open*: k-way scaling beyond one problem and the unit-boot
  cost (~12–30 s per unit, which is what makes the speedup negative); the brief's ~180 s suite
  budget is not attainable at this boot cost and the suite prints per-phase timings instead.
- [x] **W17 (Byzantine Ledger Consensus & Monotonic Snapshot Broadcast)**: Dependent on Phase 2;
  W2 ✅, W12 ✅, W1 ✅ — landed (see §6.6).
- [x] **W18 (Kernel: `NatValueIndex` lookup cost)**: Opened 2026-10-14 from the W6 remainder's
  measurements (§6.5): one arithmetic operation costs ~0.2 s on a fresh runtime and ~0.6 s
  after two hundred more nats are interned, because `trees.TreeLookup._lookup_tree` falls
  back to a linear scan of every entry (`_lookup_entries`, `ExactKey` recomputed per entry)
  whenever the Patricia lookup misses — and for `NatFromRep` a miss is every new value. Every
  arithmetic sweep in the tree is therefore quadratic (`test22` ~215 s, `test26` ~85 s of
  sweeps, the tutor's counterexample bound of 12). Kernel file: the fix needs coordinator
  sign-off and must keep `trees.py` free of forbidden constructs; `core.py`'s per-allocation
  `uuid4()` (57 % of the profile) is the floor under it and is out of scope. Brief:
  `delegation/W18-nat-index-lookup-cost.md`; slot `test30`. Landed 2026-10-15 with the
  coordinator's sign-off (see §6.7).
- [x] **W19 (Neo4j dump → machine shards, decoded on Colab)**: Opened and landed 2026-10-15
  (`8571449`). The ingest work of §6.8 read APOC's CSV natively and sharded it by label; what was
  missing was the step from a Neo4j `.dump` (a private store format only Neo4j decodes) to that
  CSV, without running a JVM database on the laptop that also runs the machine.
  `importers/split_apoc_export.py` turns either APOC layout — the combined `apoc.export.csv.all`
  file or the `bulkImport` per-label files with neo4j-admin headers — into the `nodes.csv` /
  `edges.csv` pair plus `split.json` (counts, property columns, the first-label histogram that
  *is* the shard plan, warnings); `colab/neo4j_dump_to_shards.ipynb` does the decode where a JVM
  is free (load the dump into a matching Neo4j, export with APOC, split, `sharded_import`,
  shards back to Drive). `test32` (35/35, ~38 s) drives the split both ways, `build_terms` on the
  result, the real sharder as a subprocess and one shard booted alone with its nodes, edges and
  cross-shard stubs counted by the machine. *Honest boundary*: the Neo4j cells of the notebook
  are unexecuted (no route to `dist.neo4j.org` from the sandbox); verification starts at the
  export. One importer quirk documented, not changed: a relationship property is an edge
  `src → TYPE:prop → value`, so the sharder makes a stub node for the value. See §6.9.
- [x] **W20 (Mesh beyond one filesystem)**: Opened and landed 2026-10-15 (`aaac6de` … `cedae50`).
  W2/W16 assumed one box or a shared mount, dialable peers and SAN-matching certificates; a
  laptop plus a Colab runtime has none of the three. Four switches remove them one at a time and
  default to the old behaviour (`test25` 51/51 and `test27` unchanged in `shared` mode):
  `--artifacts wire` moves the W16 unit snapshot to the worker and the result snapshot + manifest
  back *inside* the mesh connection, chunked under the frame cap, SHA-256 named, with asymmetric
  path-free authority (the coordinator serves only inputs it named and accepts only `result_ref`s
  it issued) and without touching `TERM_PAYLOAD_KEYS` — the bytes are the codec's own file, loaded
  through the codec, still the one serialisation of a machine term; `--no-inbound` for a peer
  nobody can dial (steals, is never stolen from; undialable advertised addresses back off);
  `--verify identity --expect NAME` matches the common name under the CA pin instead of the SAN
  against a tunnel's address; `--advertise` and `--role issue` bundles (CA cert + leaf only; the
  CA key never moves). The transfers exposed a latent W2 defect: one `SSLSocket` read by one
  thread and written by another is unsound, and a 3 MiB frame in flight broke it intermittently;
  `framing.Duplex` (non-blocking socket, one lock around OpenSSL, `select` with the lock released)
  replaces the pattern for every mesh connection. `test31` 50/50 (~60 s) on loopback through the
  real CLI. *Honest boundary*: no tunnel and no Colab in the sandbox — the first laptop ⇄ notebook
  run is the user's, and `colab/README.md` names the ledger events to read. See §6.9.
- [x] **W21 (Existential witness introduction)**: Landed 2026-10-19. `graph_task.MintUnboundWitnesses` / `ApplyKnowledgeRewriteWithWitnesses` mint a fresh `Thingy` for replacement variables unbound by premises and record the introduction in the action bindings. Checker B accepts that step only with the record (`test33`, 8/8, ~3 s) and refuses a successor that still carries the leftover Var (`UnboundVariableLabel`). Fully-bound rules are a no-op. `test5`/`test15`/`test19`/`test22`/`test26` still green; `test26`'s pack-level negative account is unchanged (no loaded schema uses the new ability; `EveryStateMoves` is not discharged). Brief: `delegation/W21-witness-introduction.md`.
- [x] **W22 (Algebraic rewriting / recorded grid-proof route)**: Completed on
  `arena/c58acfec-cat-theo-machine` (2026-10-19), using the brief's explicit alternative
  of a recorded grid proof with a Checker-B clause, **not** full symbolic ring normalisation.
  Initial ordinary-path API remains: `invariance.RewriteEqualityDerivation` records an
  ordered, fuel-bounded walk as `RewriteAction` paths; `PolynomialRewriteCertificate`
  gates it on a grid truth. The default rules still cannot expand `ExprPow`.
  The continuation, `playground.PolynomialGridDerivation`, records one
  `PolynomialGridActionLabel` inference containing the identity record. Checker B
  accepts it only when `PolynomialGridRuleLabel` is explicitly in the trusted policy,
  validates endpoints and record shape, recomputes syntax/variable coverage, degree
  bounds, the full Cartesian grid and machine arithmetic, and compares the submitted
  bounds/count by natural value. It never trusts the submitted verdict or a smaller grid.
  Both test26 identities (`x^4 = (x^2)^2` and the additive square identity) now have
  Checker-B-verified grid derivations; `test26` itself remains unchanged.
  `test34_algebraic_rewriting.py`: **60/60**, ~53 s, including ordinary root/nested
  paths, forged verdicts/degrees/counts/endpoints, truncated records, variable omissions
  and duplicates, unsupported constructors, constant identities and codec round-trip.
  Two grid soundness fixes: reject malformed/uncovered syntax before degree calculation;
  distinguish a false constant identity's empty-tuple counterexample from no difference.
  New labels are snapshot-registered. `core.py`, `proof.py`, arithmetic and FLT packs
  untouched. **Full gate: 34/34 suites green**, sequential, ~25.6 min on this sandbox;
  snapshots untouched. W22's prerequisite is green; W23 subsequently landed below.
  Limits: no symbolic normaliser, no signed/subtraction fragment, no automatic search
  proposal of grid actions, no FLT theorem or descent discharge claimed. Ordinary
  `BuildDerivation` replays ordinary actions only; grid actions are constructed by the
  dedicated API and verified by Checker B, not replayed through that builder.
- [x] **W23 (Factorisation substrate & derived `NatLess`)**: Completed on
  `arena/c58acfec-cat-theo-machine` (2026-10-19), slot `test35` (**109/109**, ~26 s).
  `math/arithmetic.py` adds `NatSubtract` (partial, underflow refused), `WholeSubtract`
  (existing `WholeAdd` + `WholeNegate`), `ExactNatQuotient` (positive exact divisor only),
  `CoprimeCofactors` (record `a,b,g,u,v` with `a=g*u`, `b=g*v`, coprime `u,v`) and
  `NatPredecessorFact` (guarded computed `NatSuccessor(p,n)`, checks `Succ(p)=n`).
  Zero emits no predecessor fact; `(0,0)` has no cofactor record; single-zero pairs
  reduce to `(0,1)` / `(1,0)`. The `(2,8)` decoy retains gcd 2 and does **not** acquire
  a claim that the original pair is coprime.
  `packs/nat-order.pack.yaml`, registered by path only, carries two authored generic
  Peano schemas: successor implies strict order; strict order is transitive. Search
  and forward closure derive `NatLess` facts from the machine-computed successor
  premises. Checker B verifies the ordinary derivations and refuses swapped goals
  or withheld rules; a multi-step transitive proof and codec round-trip also pass.
  **Trust boundary:** these are proofs conditional on explicit computed premises,
  like `NatSum` in W9, not a new independently audited arithmetic action. The checker
  replays schemas, not the provenance of initial facts. Do not supply unaudited
  `NatSuccessor` facts and call the resulting conditional proof arithmetic verification.
  No changes to kernel files except append-only labels; no changes to `math/peano.py`,
  Checker B, W21/W22 files, persistence or test26. **Full gate 35/35 green**, sequential,
  ~27.9 min; snapshots untouched. `test30` measures 0.0674 s/call before and after
  index growth (ratio **1.00**, within 1.5x). No new index scan or host cache.
  Not derived: prime factorisation/FTA, coprime-square-factors, Eisenstein UFD,
  EveryStateMoves or FLT. test26's old absence prose is now historical: its shallow
  name checks and selected packs do not cover these new sort-specific APIs. test35
  is the new substrate account; test26's descent claim was neither changed nor upgraded.
  The W21–W23 entry gate is now green: W28/W29 may retry, not presume success.
  **W29-driven adapter follow-up (2026-10-19):** NatPredecessorFact now interns
  its computed predecessor through the existing NatFromRep/NatValueIndex before
  checking Succ(p)=n and emitting the fact. The input upper atom n is preserved.
  Thus it joins independently computed NatSubtract(n,1) endpoints without any
  general equality change or new trusted checker rule. Raw NatPred is unchanged.
  test35 covers both interning orders, values through 1,000,003, repeated calls,
  off-index upper inputs, transitive joins across representation boundaries and
  codec replay. Latest full gate 36/36; test30 growth ratio 1.04 (within 1.5x).
  This repairs newly emitted predecessor facts, not arbitrary equal-valued atoms
  or facts already stored with off-index endpoints. It proves no new descent.
- [x] **W24 (Residue / divisibility schema wiring)**: Landed 2026-10-19 on
  `arena/c58acfec-cat-theo-machine`. Eight constant-free schemas appended to
  `packs/funceq-nt.pack.yaml` (25 → 33 rules): `divisibility_transitive`,
  `gcd_divides_both`, `gcd_commutative`, `coprime_commutative`,
  `gcd_greatest_common_divisor`, `coprimality_euclid`, `residue_of_sum`,
  `residue_of_product`. Instance facts are *records* of the machine's own edges
  (`Divides`, `Gcd`, `Modulo`, `IsCoprime`, `NatSum`, `NatProduct`), and every
  schema is fully variable-typed with no constant in an argument position -- the
  genericity walk is re-run over all 33 rules and pins that. The residue head is
  the pre-existing `ModLabel`; `labels.py` is untouched (append-only list unchanged).
  `validation/test36_residue_divisibility_wiring.py`: **41/41**, ~23 s, covering
  transitivity, gcd-common-divisor and gcd-greatest, Euclid's lemma with the decoy
  that would hold if the gcd were ignored (`6 | 9·4` without `6 | 4`), residue
  addition at moduli 3, 5, 7 and residue multiplication at 5, with unreduced-residue
  and missing-premise negatives. Checker B verifies the transitivity derivation and
  refuses it against the converse goal (`GoalMismatch`). The ledger promotes a
  candidate macro through the evaluator, ablation and holdout gates (version 1,
  active entry, `ProofReceipt`), and refuses an untrusted-rule candidate with the
  reason recorded as `UnknownRuleLabel`. Holdouts are genuinely different numbers
  (5|15 ∧ 15|45, 2|8 ∧ 8|24) because the macro patterns reuse the rule's own
  variable objects; the refusal control is a different trusted-rule set.
  *Downstream change, stated honestly*: because the pack is the tutor's rule
  source, `test24` changed with it -- the tutor's rule count is 46, the pack reports
  33 rules in the REPL, the divisibility-transitivity claim it used to hold as the
  UNDECIDED control is now VERIFIED through `divisibility_transitive`, and the
  rung-6 negative control moved to `BoundedBelow(m, b)` (premise-only in both
  packs) because four rules now conclude `Divides`. `test29` pins the new rule
  count. Nothing was weakened: every new expectation is stronger than the one it
  replaced. `test24` 86/86, `test29` 26/26, `test22`, `test19`, `test3`, `test12`,
  `test5` all green.
  *Limits*: no subtraction, so `d'Alembert`-type equations and residue-difference
  laws remain out (W22's grid route is not a signed normaliser); the closure engine
  is still a single-chain saturator, so each scenario is an isolated fact base and
  no completeness claim is made; the moduli exercised are 3, 5 and 7 -- the schemas
  are modulus-agnostic by construction, not by a table, but no exhaustive sweep is
  claimed.
- [x] **W25 (Curriculum card loader)**: Landed 2026-10-19 on this branch.
  `labels.py` gains 30 constructors the corpus already cites (`IntegerLabel`,
  `ResidueLabel`, `CongruentLabel`, the board/colouring/path vocabulary, the
  glass/flip vocabulary) plus 11 record/verdict labels, all append-only and
  registered by `sync_from_namespace`. `curriculum.py` gains the loader:
  `load_card_corpus` turns each markdown card into an eleven-field `CardRecord`
  (id, tier, role, family, target class, status, title, statement, the numbers
  the statement states, the roles those numbers fill, cited and missing
  constructors); `CompileCardTask` dispatches to family builders that emit a
  `GraphTaskRecord`; `RunCardTask` runs it with `ForwardDeriveFacts` +
  `MatchQueryConjunction`; `TrainingRecordLoader` returns records, tasks,
  refusals, verdicts and a machine `Ground1Gap` report.
  What actually loads: 24 records, 2 compiled, 22 refused with a reason. The
  seven-glasses held-out closes as an invariance obstruction -- the builder
  emits `Preserves(flip, phi)` only after the machine's own `Modulo` has
  checked every one of the k+1 splits, and `Apart(0, 1)` only after two
  machine residues differ; the Engel pack then derives `Unreachable` in four
  rounds (`thread_preserving_moves` → `preserving_moves_step` →
  `preserving_moves_empty` → `invariant_obstruction`), open at depth 1-3 and
  solved from depth 4. The domino-board decoy compiles with expectation
  `refuse` and is rejected; the count argument the trap would use is
  machine-verified to hold (62 = 31x2, colours 32 vs 30), so the refusal is
  not a counting artefact. A one-word perturbation of the held-out statement
  (odd flip count, or equal parities) makes the same builder drop the premise
  and the card stay open -- the structural proof that no conclusion is
  authored per card. Still OPEN: 48 constructors the cards cite (Burnside,
  orbit, tournament, necklace, binary-word, staircase ...) and 22 cards with
  no obligation generator (10 count-target refuse on Ground 3; 5 extremal on
  the absent graph theorem; 4 pigeonhole on residue/prefix closure; 3
  invariance whose statement states no numbers). `test37` **62/62**, ~18 s.
  `test10` 8/8 unchanged, `test3`, `test12` 10/10, `test22` green,
  `test36` 41/41.
  *Downstream change, stated honestly*: `test22/[31]` used to assert that no
  loader exists and that ten named constructors are absent. It now measures
  the opposite, true thing: 24 parsed, 2 compiled, 22 refused with reasons;
  those ten names exist, 48 others still do not, and no combinatorics card
  compiles -- so held-out evidence for family 3 in `test22` remains
  machine-swept. `test22` passes end to end.
  *Limits*: two of 24 cards compile; the loader implements two family
  builders (two-state-population invariance, rectangular board tiling
  refusal), not five. The decoy refusal means "the claim is not derivable
  from its own compiled fact base", not "impossibility is proved": a
  colouring-obstruction rule (Ground 3) does not exist yet. Nothing is
  promoted into a pack; the corpus stays `blueprint-only` evaluation data.
- [x] **W26 (Geometry remainder)**: Landed 2026-10-19 on this branch.
  Three generic schemas appended to `packs/geometry-constructions.pack.yaml`
  (6 → 9 rules): `inscribed_angles_same_arc` (two points seeing a chord from
  the same side see it at equal angles, **with** the side condition that makes
  it sound -- opposite sides give supplementary angles, and the rule does not
  fire without it), `cyclic_order_opposite_angles` (a cyclic quadrilateral's
  opposite angles are supplementary; the cyclic order is figure data), and
  `semicircle_angle_is_right` (Thales, stated relationally as perpendicular
  segments so no measure constant is needed). All three are fully
  variable-typed; the genericity walk is re-run over all nine rules.
  One new construction schema, `antipode-completion`: a circle with a centre
  and a point on it mints the antipode, which turns a chord into a diameter.
  It bears on the *existential* perpendicular goal, the generator instantiates
  its effects on the goal's own variable, and the suite then asks the machine
  (`MintUnboundWitnessesInList`) to mint and record the witness -- nothing in
  the tree names a point.
  End to end with a receipt: proposal → witness minting → the Thales step is
  selected by its conclusion (the forward engine instantiates one join per
  rule per round, test22/[32]) → **Checker B verifies** it and refuses the
  same derivation against a goal it does not reach (`GoalMismatch`). The
  promotion ledger promotes the schema through the evaluator, ablation and
  holdout gates (version 1, active entry, `ProofReceipt`; two holdouts, one
  positive and one near-miss), and refuses an untrusted-rule candidate.
  Ablations: withhold the Thales rule → the configuration stops closing;
  withhold all four circle rules → nothing circular derives; withhold the
  antipode schema → no proposal exists; withhold the side condition, the
  fourth point, or the cyclic order → the respective rule stays silent.
  `validation/test38_geometry_remainder.py`: **49/49**, ~28 s. `test21`
  **37/37** (one check added: W8's six rule ids are pinned by name; the pack
  count moved 6 → 9 with a comment), `test15`, `test17`, `test5`, `test19`,
  `test3`, `test12` 10/10, `test22`, `test23` 80/80, `test24` 86/86,
  `test36` 41/41, `test37` 62/62.
  *Limits*: no angle measures or arithmetic on them, so the centre-angle
  (factor two) theorem and any quantitative angle chasing are OUT; deciding a
  cyclic order from incidence is not attempted; projective collineations
  remain OPEN exactly as W8 left them; no figure sweeps and no general
  geometry solver. The construction's witness is existential -- the receipt
  proves "the perpendicular through this configuration exists", not a named
  point.
- [~] **W29 (Quartic descent / `EveryStateMoves` retry)**: Closed as a precise
  negative on `arena/c58acfec-cat-theo-machine` (2026-10-19), slot `test41`:
  Initially **54/54**, ~67 s, consuming W21–W23 unchanged. Following the narrow
  W23 adapter repair below, test41 is **56/56**, ~62 s. No descent rule is added.
  - W21 introductions allocate distinct recorded anonymous handles; neither natural
    arithmetic nor gcd extraction turns them into constrained numerical witnesses.
  - Both W6 grid identities now have Checker-B-verified derivations. Their receipts
    do not certify an existential parametrisation or a universal move assertion.
    The legacy symbolic walker remains stuck on the additive identity.
  - Gcd cofactors of coprime square inputs remain the input values (4,9), not square
    roots. The square-product decoy (2,8) keeps its nonunit gcd. No square lemma is
    authored or promoted.
  - A human-selected family instance computes the candidate measures 5 and 41.
    `NatLess(5,41)` is an arithmetic verdict, not a general decrease derivation.
    The initial retry exposed a transport gap at the immediate predecessor of 41:
    the adapter emitted a 40-valued atom distinct from `NatSubtract`'s result.
    **Follow-up repaired that producer boundary:** NatPredecessorFact now interns
    its computed lower endpoint, so the same proof verifies the independent
    arithmetic endpoint. Raw NatPred's off-index atom still fails that goal;
    general fact matching/coverage and Checker B equality remain unchanged.
  - Full registered-pack audit: **17 packs / 206 raw rules**, no occurrence of
    `EveryStateMovesLabel` or `ExistsLabel` in any replacement. Initial source facts
    contain neither the movement claim nor its symbol. Ordinary substitution and
    fresh-handle allocation cannot manufacture the absent movement label in this
    audited transition system. This is a syntactic obstruction, **not** a theorem
    about arbitrary future code/tactics; one-step smoke retries are labelled bounded.
  - The two-step descent skeleton verifies only with EveryStateMoves as an explicit
    starting premise. Removing it prevents closure; a receipt relabelled to omit it
    is rejected by the policy scope guard. Both the actual missing-universal claim
    and a skeleton replay without that premise are submitted to the real ledger,
    rejected for `GoalMismatch`; ledger remains 0, no active domain promotion.
  Initial gate: 36/36 green, ~28.9 min; only the new suite/docs changed then.
  **Endpoint follow-up gate: 36/36 green**, ~28.7 min sequential; test35 is now
  146/146 (~44 s), test41 56/56 (~62 s). Only math/arithmetic.py, these suites and
  docs changed in the follow-up; kernel, checker, packs, test26 and snapshots
  remain untouched. Do not re-dispatch the descent attempt unchanged. Generic
  constrained arithmetic witnesses, parametrisation/coprime-square-factor proofs
  and a checked construction plus source-state coverage path remain missing. No FLT, smaller solution or
  EveryStateMoves theorem is claimed; these isolated receipts do not clear W30's
  gate as a verified FLT domain macro.
- [x] **Constrained Nat witness follow-up** (2026-10-19; supplemental slot
  `validation/test46_constrained_nat_witnesses.py`): generic **bounded** numeric
  search, not another anonymous-handle allocator. `playground.FindNatWitness`
  streams `[0,bound)^arity` using machine chains/arithmetic, with a native
  candidate-count budget. Accepts equations and strict inequalities in the
  existing natural-polynomial fragment. Separate Found/Exhausted/Budget/Invalid
  statuses prevent bounded absence, resource refusal and malformed input from
  being conflated. `VerifyNatWitness` independently re-evaluates an exact numeric
  assignment against the caller's constraints/bound; it does not authenticate
  the search record's count, completeness claim or status.
  - test46 **185/185**, ~8 s: carries/last tuples, numeric bindings, opaque formal
    variables without sort mutation, bounds/budget, invalid requests, changed
    constraints, empty-dimensional products, codec replay, no movement proof.
  - test41 **61/61**, ~60 s: a human-supplied finite fixture `2mn=4`,
    `m²+n²=5`, `0<n<m` yields `(2,1)` after seven checks. This is NOT a
    discovered parametrisation, universal existence theorem or smaller solution.
  - Latest **37/37 suites green** (~27.5 min); test35 146/146; test30 ratio 1.07.
    Only playground/label vocabulary, test41/test46 and handoff docs changed;
    kernel, checker, ledger, arithmetic adapter, packs, snapshots and test26 are
    untouched. No new proof capability or promotion is enabled. W29 still lacks
    uniform witnesses/parametrisation/square-factor proofs and checked source
    coverage. Budget bounds candidate checks, not exponent cost or wall time.
  Full API/trust-boundary handoff: `delegation/constrained-nat-witnesses.md`.
- [x] **W33 (Mesh reconnect attempt accounting)**: Landed 2026-10-21 on
  `arena/b94f5f2e-cat-theo-machine` (fast-forwarded to `0b80aed` first), slot
  `test45` (**20/20**, ~26 s, three full runs). The §6.5 double-count is closed on the
  accounting side, not just healed on the outcome side. A severed member
  connection now makes the member *suspect* (`member-suspect`,
  `summary()["deferred_losses"]`) for `reconnect_grace` seconds (new
  `MeshPeer` argument, default **5.0**, sized against the worker's 0.3 s
  reconnect poll and 3 s join; `0` restores the old accounting, test45
  phase 4). Membership and the connection end at once, so a suspect is
  offered nothing new, but job owners/states, leases, offer bookkeeping and
  attempt numbers are frozen and **no terminal record is written** — a
  coordinator waiting for every submitted job to have a result can no longer
  mistake a blink for completion and shut down under a queued unit. A
  rejoin with the same peer id inside the grace cancels the loss
  (`member-rejoined`, claimed atomically with re-registration in
  `_handle_join`); the worker's `_announce_work` then re-states an ownership
  that was never taken away. Only an unresolved suspect resolves, from the
  liveness loop, into exactly the old loss once (`member-lost`, leases
  reclaimed, one attempt, re-dispatch or provisional `worker-lost`), with
  the orphan set read at resolution time. `goodbye` and heartbeat-timeout
  losses are never deferred, and the offer watchdog does not charge an
  unanswered offer against a suspect owner (test45 phase 5). *Reproduced
  first*: phase 1 replays the §6.5 sequence with gated stub runners over
  real mTLS (victim killed mid-job → attempt 2 queued on the survivor → the
  survivor's link cut with its rejoin held); against the pre-fix code it
  reads `states={'failed': 1, 'pending': 1}` with the survivor's own job at
  attempt 2 (6 passed, 5 failed), and passes 20/20 whole-suite after.
  *Defect found on the way*: `shutdown()`'s writer-flush wait omitted a
  worker's coordinator connection, so its socket could close on a `GOODBYE`
  the writer had not sent, and a peer that said it was leaving would have
  arrived as a bare link loss; the coordinator connection is in the wait
  now (test45 phase 2 pins goodbye as an immediate, unsuspected loss).
  Files: `networking/peer.py` only (`networking/jobs.py` untouched), plus
  `test45` and docs. `core.py`, kernel, packs, snapshots untouched.
  **Gate** (re-run in full on the final tree): `test25` **51/51** (169.0 s;
  its two crash paths now each pay the 5 s grace before resolving, inside
  their 20–25 s waits), `test31` **50/50** (85.9 s), `test27` **51/51**
  (320 s; kill run 45.8 s, redispatches=1, `member-lost` and mid-job
  attempt 2 exactly as before; healthy-run speedup 0.85×, reported not
  tuned). `test45` also passed in full three times. No other suite imports
  `networking.peer`; the other 34 suites were not re-run this session.
  *Remaining window, stated plainly*: a peer away longer than the grace is
  still charged the one attempt and its presumed record stands until a real
  result supersedes it (the W2 behaviour); the grace lengthens true-crash
  recovery by up to `reconnect_grace` plus one heartbeat interval; and a
  coordinator that shuts down while a holder is suspect does not force
  those jobs terminal — as before, it never did for running jobs.
- [x] **W27 (Engel remainder)**: Landed 2026-10-22 on
  `arena/b94f5f2e-cat-theo-machine` (on top of the §6.10 integration merge
  `ae1297d`), slot `test39` (**53/53**, ~5.4 min). All three brief
  deliverables are addressed; search firing is partial in a pinned way.
  *Two unnamed instances*, built as graph facts in the suite (only 2/24
  curriculum cards compile, so the brief's fallback applies); neither is
  one of the three named packs, and `packs/engel-strategies.pack.yaml` is
  untouched (13 rules, re-pinned). (a) Euclid by subtraction on pairs
  1..12 — 144 states, 132 ground transitions, machine-counted partition
  66 + 66 moves with the 12 equal pairs moveless. The sum measure's
  `StrictlyDecreases` claims are verified by machine arithmetic over every
  transition; the pack threads them to `AllMovesDecrease` and
  `monovariant_terminates` closes `Terminates`; concrete runs halt at
  (4, 4) and (1, 1). The first component alone is refuted as a measure
  with a witnessed counterexample and certified only `NonIncreases`; a
  move with no transitions earns no certificate. (b) nine chameleons,
  three colours — 55 states, 108 transitions, every target machine-summed
  back to the population (closure of the relation is checked, not
  assumed). All three monochrome targets reach `Unreachable` through the
  invariance chain; a same-reading state is correctly not obstructed, and
  withholding one move's `Preserves` fact kills the `Invariant`.
  *Discovery (landed)*: observables are data. One append-only label,
  `LinearObservableLabel` (499th label name; snapshot round-trip pinned),
  heads a descriptor term — coefficient chain, modulus or raw — that
  `LinearObservableValue` reads by machine arithmetic; the syntactic
  `Preserves` of `invariance.py` could never evaluate such a thing. The
  additive `invariant_miner.py` block verifies a descriptor against a
  ground transition list and emits the literal pack facts
  (`Preserves` / `StrictlyDecreases` / `NonIncreases`) as certificates, or
  refutations carrying (before, after, transition) witnesses; empty
  evidence refuses rather than passing vacuously. `MinePreservedObservables`
  swept all 52 nonzero {0,1,2} linear forms, raw and mod 3, over the
  chameleon transitions: **10 certified, 42 refuted**; separation on
  machine readings selects (0,1,2) mod 3 (the suite does not hardcode
  which certified form separates). The trivial total is certified and
  separates nothing, as it should. *Ablation*: add a lone-colour-change
  move and re-mine — 4 observables survive, none separates. Mining cost
  is the ~20 ms/op arithmetic rate; a per-state reading cache keyed by
  state-term identity (transitions reuse the enumerated state objects)
  and first-failure early exit keep the two sweeps inside the suite's
  ~5.4 min.
  *Search firing (partial, pinned)*: `Planner.ProposeStrategyMethods`
  reads declarations already in the facts — `Monovariant` / `SemiInvariant`
  + `MoveSet` + `BoundedBelow` under a `Terminates` goal; `MoveSet` +
  `Reading`×2 + `Apart` under `Unreachable` — and emits method terms
  term-equal to hand-written ones, proposing nothing from incomplete
  declarations or under a wrong-shaped goal. `PlannerProblemWithProposals`
  attaches them (id and root rebuilt at `Zero`, no stale state), and
  `PlannerStep` now discharges at creation any method child whose goal is
  already a fact, so a `PlannerRun` *without a pre-built method term*
  decomposes the proposed `Monovariant` and proves all four obligations.
  Generator withheld → no alternative, root unproved; one
  `StrictlyDecreases` fact withheld → exactly that child stays unproved,
  its sibling still discharges (discharge is per-fact). *Not landed*: the
  root is not `Proved` inside `PlannerRun`. Assembly is a search job, and
  two blockers in `search/` were isolated and left unedited (the brief
  allows planner-side hooks; the search leg is a separate repair):
  (1) a zero-step success is unrepresentable — a goal already true yields
  an empty plan component, which the step reads as no-progress and
  records as failure; this is also why `test1`/`test2` roots are
  `FailedLabel`, and why in-facts obligations could never discharge
  before this branch's creation-time discharge; (2) multi-pass
  fact-saturation on this pack stalls after pass 1, though all three
  applicability filters admit the threading rule in every variant tested
  and per-rule application plus `JoinPremises` derive every step by hand
  (observation-level; suite §[5] records the probes). The instances
  therefore close by forward chaining, as in test23/test37; the two
  root-not-`Proved` checks are the pins that should flip when the search
  leg is repaired.
  *Authoring hazard found on the way*: `M.TermEqual(a, b) is M.truth_value`
  without the terminal `()` compares the *uncalled edge object* and is
  silently `False` — three suite checks failed this way while every
  equivalent probe (with the call) passed; edge results come from calling
  the edge, an edge object is never its own result. Check expressions
  that end `... ) is M.truth_value` with no `()` before `is` are always
  wrong.
  *Limits*: finite enumerations only — certificates quantify over the
  stated transition lists, not over a symbolic move schema; candidates
  are linear forms with coefficients in {0,1,2} at one modulus per sweep;
  Checker B / ledger derivation is not claimed (the suite header says so,
  as test23/test37 do); `main.py`'s hardcoded `"Engel E1"` / `"Engel E2"` /
  `"Engel coin problem"` agenda entries are untouched per the brief.
  **Gate**: full run on the final tree, **42/42 suites exit 0**
  (`test39` 53/53; `test23` 80/80; `test21` 37/37; `test8`, `test7`,
  `test10` green; the two non-asserting demos rc=0 as always).
  Files: `invariant_miner.py` (additive block + one import), `planner.py`
  (proposer hook + creation-time method-child discharge; the stale
  "Only Pigeonhole and Extremal" comment corrected), `labels.py`
  (append-only, three sites), `validation/test39_engel_remainder.py`.
  `core.py`, `search/`, packs, snapshots untouched.
- [x] **Supplemental, unbriefed (machine-native playground, slot `test47`)**:
  Landed 2026-10-22 on `arena/f42b3f12-cat-theo-machine` (forked at W33,
  `b7a94c6`), integrated the same day (§6.11). Three commits, three files:
  `playground.py` grows pure-machine set/coordinate edges (`SetDifference`,
  `SortNatChain`, `TupleElementAt`, `ProjectCoordinate`,
  `ProjectAllCoordinates`, `ProjectTensorModulo`,
  `FindTensorEqualityWitness`, `DiscoverExprObstructions`,
  `EvaluateNatExpr`), a surface-goal parser into Pair spec records,
  dynamic goal-directed Cartesian sweeps over `ResidueTable` /
  `CongruenceClasses`, multi-process sweep dispatch with
  `[debug: cartesian_playground process <pid>]` telemetry, and `main.py live`
  automatically suggests lemmas on unproved goals (playground sweep +
  backward-obligation candidates) without being asked; direct lesson
  naming after "Would you care to give it a name?". `test47` **27/27**
  (~67 s; §[4] drives `main.py live` as a subprocess). Verified on
  integration by diff scan (additions are `M.Edge`s over machine terms;
  host code tokenises/routes) and by the full gate, not by a line audit of
  the ~2800 added lines. *Defect found on integration*: as committed, the
  head was not green — `_pg_debug` used `sys` without importing it, so
  test47 and test13 crashed on contact; one-line repair (`import sys`)
  on this branch. No slot collision: `test47` was the next never-allocated
  number; no brief or W-number was consumed, and no DAG record came with
  the branch — this entry and §6.11 are written by the integrating session.
- [x] **W30 (Domain packs through the closed loop)**: Landed 2026-10-22 on
  `arena/b94f5f2e-cat-theo-machine`, slot `test42` (**42/42**, ~2 min).
  One shared promotion ledger now carries all three Phase 4b domains:
  funceq/NT divisibility transitivity, geometry Thales, and both Engel
  closers (`invariant_obstruction`, `monovariant_terminates`) promote
  onto it in sequence (versions 1–4; fresh instances and holdouts
  throughout — test36/test38 remain those domains' authoring records).
  The two W27 Engel chains earn their first Checker-B receipts as
  multi-step derivations (6-step invariance to `Unreachable`, 5-step
  monovariant to `Terminates`; GoalMismatch against the same-reading
  decoy and UnknownRule with the closer untrusted pinned), and a
  smaller second Euclid instance's `AllMovesDecrease` is receipted the
  same way to back the terminates holdout. One promoted entry's
  `ProofReceipt` is re-verified against policy (and refused against a
  decoy-goal policy).
  *Two loop strengthenings.* (1) The ledger's provenance gate now also
  accepts a `GroundObservableCertificate` (new append-only label, the
  500th; constructor + `VerifyGroundObservableCertificate` in
  `invariant_miner.py`): it re-runs the named ground-transition verifier
  for every listed move at promotion time and demands the certified
  verdict back term for term, so mined premise facts are re-checked
  when promoted, not only when derived. A forged certificate
  (φ=(1,0,0)) is refused with `InvariantRefuted`; an empty move list
  refuses (no vacuous passage). Both Engel promotions carry
  certificates (preservation over the 108 chameleon transitions;
  strict decrease over the 132 Euclid transitions). (2)
  `WithheldRuleAblationTrial` (`evaluator.py`, additive): the candidate
  must stop evaluating once its rule is actually removed from the
  trusted set — `AblationTrial` alone only checks the instance is not
  trivially closed. Pinned `Proved` for the Engel and funceq
  candidates and `Failed` (correctly) when an unused rule is withheld.
  *Substrate findings, recorded not repaired.* (a) Knowledge rewrite
  consumes matched premise facts (`DropMatchedFacts` drops one
  occurrence per use), so replaying a monotone strategy argument as a
  derivation lists a fact used by k inferences k times: the chameleon
  chain lists both `Reading` facts twice (threading + obstruction),
  the Euclid chain lists `Monovariant` twice. (b) Candidate macros are
  single-rule-shaped: `ExpandCandidateMacro` seeds `BuildDerivation`
  with the pattern-match bindings, so patterns must be the rule's own
  templates (the test36/test38 idiom); a six-step strategy plan under
  seeded bindings produces un-instantiated steps, which Checker B
  refuses (`ConclusionMutation` — witnessed while developing this
  suite). Hence chains are receipted via `VerifyDerivation`, and the
  ledger promotes the closers, whose threaded premises are the ends of
  those very chains. (c) `M.Char` is not interned — two `M.Char("P10")`
  are Compare-equal but identity-distinct atoms; holdouts must bind
  atoms once (the first version of this suite's Thales holdouts failed
  exactly there). (d) A no-op step verifies trivially in Checker B
  (identity current→next reproduces), so a derivation whose last rule
  never fired is caught only by the goal check — worth knowing when
  reading `StepVerified`.
  *Limits*: Checker B verifies derivations from stated premises; the
  receipts certify the inference chains, while the miner premise facts
  rest on the transition enumerations (re-run by the certificate gate,
  but a receipt is not a derivation of the enumeration). Engel
  promotion covers the two closer schemas, not a general strategy
  schema; the authoring suites (test21/test23) still do not exercise
  the loop themselves; no figure sweep (W8's remaining item) and no
  corpus-scale evaluation (22 cards unbuilt) are claimed; the
  search-leg assembly gap (test39 §[5]) is untouched. W8/W9/W10's
  "not claimed" notes are amended in their entries above where now met.
  **Gate**: full run on the final tree, **44/44 suites exit 0**
  (`test42` 42/42; `test39` 53/53; `test23` 80/80; the brief's
  `test7`/`test8`/`test9`/`test28` set and the ledger's other users
  `test36`/`test38` green; demos rc=0).
  Files: `promotion_ledger.py` (gate-4 additive branch only),
  `evaluator.py` (one additive edge + `__all__`), `invariant_miner.py`
  (certificate constructor + verifier + `__all__`), `labels.py`
  (append-only, three sites), `validation/test42_domain_promotion_loop.py`.
  `checker_b.py` unchanged — no checker extension was needed.
  `core.py`, packs, snapshots untouched.
- [ ] **W28, W31, W32 (Phase 4+, remainder)**: See §8. Slots through `test39`
  plus `test41`, `test42`, `test45` and supplementals `test46`, `test47` are occupied; other slots remain as allocated.

---

## 5. Agent Coordination Protocol & Invariant Rules

Every Arena agent working on this repository must strictly adhere to the following invariants:
1. **Repository & Branch**: Work exclusively on the branch your own session is pinned to, and never on another session's branch. (This rule was first published naming one specific branch, `arena/01a108cd-cat-theo-machine`, but every copy of this document — including the two on other branches — carried that same hardcoded name, so it was never a usable instruction. The invariant is one-branch-per-session, not one-branch-for-everyone.)
2. **Machine Representation Purity** — binding in the kernel, and in any code that constructs or consumes machine terms:
   - Do not edit `core.py`.
   - Build and inspect machine values with `Pair`, `EmptyList`, `truth_value`, `false_value`, `Atom`, `Char`, and native labels — not Python lists, dicts, or bools.
   - Do not reach into a machine value with `isinstance`, `hasattr`, `type`, `__class__`, or `__new__`; use the machine's own predicates (`IsPair`, `IsTree`, `Compare`, `IdentityCompare`).
   - Counting and arithmetic over machine quantities operate via Peano `Zero`, `SuccLabel`, and `GMPRep`.

   **Host-layer exception.** This rule was first published unqualified, which made it stricter than the codebase it governs: read literally it condemned 46 sites in verified, shipped code. The boundary that is actually observed is a layer boundary, and it is now stated as such.

   - The kernel — `core.py`, `machine.py`, `context.py`, `labels.py`, `proof.py`, `trees.py`, `graph.py`, `matching.py` — contains **zero** forbidden constructs and must stay that way. That is the invariant worth defending.
   - Outside it, in host, harness, codec and CLI layers (`main.py`, `persistence.py`, `packs.py`, `runtime.py`, `prettyprinting.py`, `search/`, `testsuite.py`, `story_renderer.py`, `validation/`, `probes/`), Python natives are permitted where there is no machine analogue. `isinstance` 11, `__class__` 16, `type(` 8, `getattr(` 7, `hasattr(` 4 already live there.

   Two standing cases, so nobody re-litigates them:
   - `persistence.py`'s object-identity index (`_ids_by_pyid`, `_name_by_objid`) is keyed on Python `id()`. Object identity is a Python-level fact and an anonymous `Atom` has no term-derived key, so a pure-machine equivalent is not merely slower, it is not expressible. It buys capture ~620 → ~16,000 objects/s. Sanctioned.
   - Measurement and reporting in harnesses (chain lengths, timings, byte counts) may use Python ints. What must not happen is a Python count standing in for a machine quantity inside a term.

   **The exception is conjunctive: both halves must hold.** The code is host-layer, *and* there is no machine analogue for what it does. Being in a harness or a probe is not by itself a licence — if the machine can already answer the question (`Compare`, `IsAtom`, `IsPair`, `IsTree`), then reaching into a payload with `getattr`, `type`, or `.symbol` is a violation wherever it sits. The identity index passes both halves. A probe that read `.symbol` to find an edge by name and `type(x).__name__` to report what came back passed only the first; it was fixed to use `Compare` and `IsAtom`. An earlier draft of this section stated the test as "whether the value crosses into a machine term", which made layer the only condition and would have excused that probe. Do not spend a session on an unscoped purity refactor of host code, and do not cite this rule to reject working host-layer code — but do not cite the host layer to excuse bypassing a predicate the machine already provides.
3. **No Domain-Specific Hardcoding**: Do not hardcode problem targets or fixed heuristics in search or mining modules.
4. **Verification Requirement**: Every new worker module or pack must include an automated verification suite in `validation/` with $100\%$ green test results before promotion. There are currently **44** suites — `test1`–`test39` plus `test41`, `test42`, `test45`, supplemental `test46` and supplemental `test47` (the rest of the Phase 4+ slots `test40`, `test43`, `test44` remain pre-allocated to their briefs; do not fill numbering gaps with other work, see §8) — each a standalone script. Run one with `PYTHONPATH=<repo-parent> python -u validation/testN_*.py` (the suites insert the package parent onto `sys.path` themselves and import as `cat_theo_machine.*`).
5. **Snapshot Root Invariant**: any new machine state that must survive a cold resume has to be registered as a root in `SnapshotCodec.capture()` and restored in `activate()`. Content added through the graph's `nodes`/`edges` context is now covered; state kept only in Python attributes is not, and silently evaporates on reload.
6. **Suite Slot Discipline**: `validation/` numbering is append-only. Two lineages independently claimed slots 15 and 16 for unrelated suites; the reconciliation below is what happened, and new work must take the next free number rather than reusing a taken one.
7. **One serialisation of a machine term**: the snapshot codec. The mesh carries references (W2) and, under `--artifacts wire` (W20), the *bytes of snapshot files* that the receiver loads through the codec — never a pickled or otherwise serialised term (`framing.TERM_PAYLOAD_KEYS` rejects the frame). A new transport that wants to move machine state moves a snapshot.

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

**Snapshot format fork (open item).** Both reconciled lineages write snapshot format **version 3**, and agreement was mistaken for safety: across all 72 branches, **49 write version 4 and only 22 write version 3**. This branch's codec raises `Unsupported snapshot version` on a v4 file, so real state on those branches — `snapshots/set-b-cumulative.json`, `snapshots/library-only-control.json`, and the `search_compare` runs on the `01a05cb0` / `01a05d5d` / `01a06274` / `01a06542` / `01a06923` / `01a06cca` family — cannot be loaded here. The incompatibility is one-directional: v4's loader gate is `version not in (3, 4)`, so v4 branches *can* read what this branch writes. Neither fork is a superset — v4 routes `constructor_registry` through a `_registry_entries_snapshot_root()` abstraction and has **no** `nodes`/`edges` root and **none** of the four optional roots, so it lacks both this branch's hypergraph fix and the lineages' planner/ledger/task/invariant state. Decision: stay on v3, because ingesting foreign graphs needs exactly the three things v4 lacks. Cost of a later adoption is **unknown and deliberately unbought** — v4's `persistence.py` differs by +701/−225 lines and nobody has read them. Revisit only if state from those 49 branches becomes wanted.

**Ingest path for foreign graphs (built, proven at 20k-relation scale).** `importers/csv_to_hypergraph.py` and `importers/cypher_to_hypergraph.py` take the two shapes a restored `neo4j-admin` dump lands in — `apoc.export.csv.all` tables and `apoc.export.cypher.all` scripts — and both feed the *same* `build_terms`, so there is one representation of a node and one of an edge and the two importers cannot drift. Nodes are named `Char`; relationships are `Pair(rel, Pair(a, Pair(b, EmptyList)))`; labels and properties become hyperedges keyed `(key, node, value)` with a whole string in one `Char`, so every property stays `Compare`-accessible. Three probes cover it: `importer_roundtrip_probe` (out and back, 24,000 edges), `cypher_import_probe` (value integrity and endpoint resolution), `imported_reasoning_probe` (a real `proof.Rule` derives 20,000 inverted facts from imported content through `matching.Rewrite`, then persists and reloads them). Two costs worth knowing before anyone promises scale: derivation runs ~9 ms per edge, because a `Rewrite` miss recurses through the whole term rebuilding it, so reasoning over imported content is the bottleneck and not storage (save 12.5 s vs rewrite 183 s at 24,000 edges); and both importers were written against apoc's documented output shape, never a real export, since this sandbox has no Neo4j and no route to neo4j.com — validate on the first few thousand lines of a genuine dump before a full run.

**Measured ingest ceiling: memory, not time.** `probes/ingest_scale_probe.py` walks a ladder through the real path (build terms, save, reload) on a 3.9 GB / 2-core sandbox, boot baseline 54–71 MB peak RSS:

| relations | edges | build | save | load | snapshot | peak RSS |
|---|---|---|---|---|---|---|
| 20,000 | 24,000 | 1.54 s | 11.47 s | 12.73 s | 24.8 MB | 391 MB |
| 60,000 | 72,000 | 4.08 s | 31.96 s | 23.12 s | 70.3 MB | 951 MB |
| 100,000 | 120,000 | — | — | — | — | **OOM-killed after 546 s of thrashing** |
| 150,000 | 180,000 | — | — | — | — | **OOM-killed after 245 s** |

Time scales gently and was never the problem; resident set is roughly **10 KB per edge at peak**, because the reload phase holds the decoded JSON graph and the restored terms at once. The portable number is that per-edge cost, not the rung where this box died. Extrapolated, a million-edge dump wants ~10 GB, so **one monolithic snapshot is not a viable target for a large foreign graph**: the importer needs a sharding mode that splits by label or domain into independent snapshots, each of which boots and round-trips alone. **Built and proven**: `importers/sharded_import.py` shards by node label, streams the source CSVs and spills per-shard rows to JSON Lines so nothing large is held in memory, boots the packs once and replaces the graph context per shard, and writes `OUTDIR/<shard>.json` plus a manifest. An edge whose endpoints fall in different shards is written into the source shard together with a stub node for the foreign endpoint carrying a `stub_of` property edge that names the shard holding the authoritative copy, so no shard has dangling edges and cross-shard provenance is itself queryable. `probes/sharded_import_probe.py` builds a fixture whose 300 relationships deliberately cross all three labels, then per shard boots it alone, agrees the machine counts against the manifest, and walks every relationship confirming both endpoints occur in that shard's nodes: `shards=3 crossing=180 undeclared=0`, each shard `nodes=32 edges=152 links=100 dangling=0`, 0 failures. Sharding costs save-and-load time per shard, not boot time. Which phase actually kills it is not yet attributed — the probe now prints build, save and load separately, because the fix differs: a death in build means chunked construction, a death in load means streaming or lazy restore.

### 6.1 Three-way reconciliation of this file (2026-10-13)

By 2026-10-13 this document again existed in divergent copies, all descending from the 2026-10-12 reconciled version above (`48bf47d`). The copy on `arena/717c9822-cat-theo-machine` is the three-way merge of:

| Source branch | Last edit to this file | What it contributed |
| :--- | :--- | :--- |
| `arena/abf4a212-cat-theo-machine` | `0b39f49`, 2026-10-12T20:16Z | W2 status at 48/48 with the crash clause pinned from both sides (supersedes the 45/45 line the other copies carried). |
| `arena/500df21f-cat-theo-machine` | `5a546ec`, 2026-10-13T04:13Z | §3 rows and §4 completion entries for W8 (`test21`), W9 (`test22`), W10 (`test23`). |
| `arena/6e28638f-cat-theo-machine` | `7c93667`, 2026-10-12T02:09Z | The snapshot-format-fork open item directly above. |

The three edits touch disjoint regions, so the merge is clean (`git merge-file`, zero conflicts) and nothing was reworded. `delegation/README.md` and `networking/README.md` were linear, not divergent — the `abf4a212` tip is a strict successor of every other copy and was taken as is. Work that is on a branch but **not yet recorded in §4 by its owner**: W7 (`validation/test20_flt_eisenstein_discovery.py`) and a second, independent W9 implementation that also occupies slot `test22` (`math/funceq.py`, no pack) on `arena/87d8295b-cat-theo-machine`; W16 (`search/distributed_engine.py`, `networking/jobs.py`) on `arena/abf4a212-cat-theo-machine`. The duplicate `test22` claim is a slot-discipline collision of the kind §5 rule 6 forbids and is left for the coordinator to rule on.

### 6.2 Integration of all DAG-era worker branches (2026-10-13)

`arena/717c9822-cat-theo-machine` now carries every DAG-era branch on origin, merged with `git merge --no-ff` in this order, each merge a separate commit with its resolutions in the message:

| Order | Branch merged | Tip | What it brought | Conflicts |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `arena/abf4a212-cat-theo-machine` | `223a023` | The reconciled Hyge code line (Phase 0–2 modules, `test1`–`test19`), W2 (`networking/`, `mesh.py`, `test25`), W16 to date | this file only (kept §6.1's copy) |
| 2 | `arena/87d8295b-cat-theo-machine` | `a02555b` | W7 (`test20`), W9 (a) (`math/funceq.py`, `graph_task.py`, `test22`) | none |
| 3 | `arena/6e28638f-cat-theo-machine` | `c362d54` | CSV-to-hypergraph importer and its two probes | this file only |
| 4 | `arena/500df21f-cat-theo-machine` | `5a546ec` | W8 (`constructions.py`, `test21`), W10 (`test23`), W9 (b) (`test29`), three packs, 31 labels, planner method terms | `labels.py` (union, no name shared), `validation/test1`–`4` (kept the `cat_theo_machine.*` convention, dropped the branch's `_hyge_import.py` shim), `test22` (renumbered, below), three docs (kept newer) |

The three older DAG-era branches (`arena/01a108cd`, `arena/d09a2974`, `arena/861455d0`) are strict ancestors in content of the Hyge line per §6 and were not merged separately. The 60-odd pre-DAG branches (`arena/01a0…`, `work/C-*`, August–early October) belong to the earlier programme (`programme_c/`, `researcher_v0/`, `odr_*`); only their markdown was imported (`a5ea84a`), their code was not, and they write snapshot format v4 (open item above).

**Slot collision resolved.** Two sessions executed `W09-imo-combinatorics-funceq.md` independently and both used the pre-allocated slot 22. The code-line deliverable (`87d8295b`, families 1–3 over the forward engine, miner and ledger) keeps `test22`; the pack-based slice (`500df21f`) is renamed `validation/test29_imo_funceq_parity_pack.py` (29 = first free number after the pre-allocated 20–28; only the banner lines changed). Both are recorded under W9 in §4. Root cause: the delegation pack hands out one slot per *brief*, not per *session*, and nothing stops two sessions taking the same brief. The next free slot is `test30`.

**Constraint audit on the integrated tree.**
- `core.py` is byte-identical to `master` (`8ae67734`).
- Kernel purity (§5 rule 2): `machine.py`, `context.py`, `labels.py`, `proof.py`, `trees.py`, `graph.py`, `matching.py` contain zero `isinstance` / `hasattr` / `type(` / `getattr` / `__class__` / `__new__`; `core.py`'s two hits are commented-out debug prints inherited from `master`. Worker-introduced host-layer sites are confined to `networking/` (JSON wire shapes and exception class names in diagnostics — no machine analogue), `mesh.py` (one JSON shape check), and `test22` (two, each justified in the suite). `networking/jobs.py:195` resolves a label name from the wire with `getattr(L, name)`, the same namespace-resolution pattern as `packs.py`'s `sym` branch that the W9(b) session flagged; it is host-layer and has no machine analogue, but it inherits that concern.
- §5 rule 3 (no hardcoding): the three new packs carry ontology and schemas only; their suites pin genericity machine-side (`ground_data_atoms`); W7 writes no cube identity or norm formula; W9 (a) names no equation in `math/funceq.py`.
- §5 rule 5: all 31 new labels are in `SNAPSHOT_SYMBOL_NAMES`; `GraphVersionLabel`, `KObligationLabel`, `HeuristicPerformanceLabel` were already unregistered on `master` and remain so (pre-existing).
- §5 rule 6: see the collision above.
- Pre-existing and untouched: `audit_pack_check.py` does not parse (BOM + a Windows path, from `master`); `__pycache__`/`*.pyc` files committed on `master` are still tracked (a `.gitignore` now prevents new ones; removing the tracked ones is a separate housekeeping commit).

**Gate.** Full `validation/` run on the integrated tree (2 vCPU, `.venv` with `gmpy2` 2.3.2 / `pyyaml` 6.0.3, Python 3.11): **25/25 green**, ~16.7 min wall. Per suite: `test1`–`test19` all pass (`test12` 10/10 probes; `test3` passes — its `master`-era Windows-path failure was fixed on the code line); `test20` all checks in 94.9 sbove.
- Pre-existing and untouched: `audit_pack_check.py` does not parse (BOM + a Windows path, from `master`); `__pycache__`/`*.pyc` files committed on `master` are still tracked (a `.gitignore` now prevents new ones; removing the tracked ones is a separate housekeeping commit).

**Gate.** Full `validation/` run on the integrated tree (2 vCPU, `.venv` with `gmpy2` 2.3.2 / `pyyaml` 6.0.3, Python 3.11): **25/25 green**, ~16.7 min wall. Per suite: `test1`–`test19` all pass (`test12` 10/10 probes; `test3` passes — its `master`-era Windows-path failure was fixed on the code line); `test20` all checks in 94.9 s; `test21` 36/36 in 72 s; `test22` all checks in 211 s; `test23` 80/80 in 68 s; `test25` 48/48 in 171 s; `test29` 26/26 in 165 s. No tracked snapshot was rewritten by the run (`git status snapshots/` clean). Baselines for attribution: `arena/87d8295b` tip 22/22 green before the merge; `arena/500df21f` tip green except its own `test3` (the `master` failure). Note for anyone re-running the gate: do **not** export `HYGE_SNAPSHOT_UPGRADE_RESAVE=0` globally — `test12` probe 10 checks that the *default* policy still resaves and fails under a blanket opt-out; that is the harness, not the codec.

### 6.3 Post-integration: W16 suite and a restore defect (2026-10-14)

`validation/test27_distributed_prover_swarm.py` (slot 27, W16's) landed on the integrated branch;
see §4 W16 for what it measures. Writing it exposed a defect that the 25-suite gate had not:
`persistence._restore_tree_roots_parallel` hands each restored root back from a spawned worker
as a pickle, and `pickle` serialises a cons-list recursively, so `all_rules` pickles at a depth
proportional to the rule count. After the merge the full-pack rule list crossed the interpreter's
default 1000-frame limit *inside the spawned worker* (which starts at the default): the rebuild
succeeded, the handoff died, and every snapshot saved from a full pack boot — i.e. every swarm
unit — failed to boot with “restore worker failed for all_rules: maximum recursion depth
exceeded”. The tracked snapshots (`hyge_snapshot_current.json`, 268 KB of pickled rules against
791 KB for a unit) were still under the limit, which is why the gate stayed green. Fix: the
handoff (`_write_handoff`) runs on a thread with a generous stack and raises the recursion limit
only as far as the payload demands, doubling to a cap that fails loudly rather than hanging;
unpickling in the parent is iterative and unchanged. `core.py` untouched; the change is host-layer
codec plumbing. Also added to `.gitignore`: the `hyge-*-restore-*` scratch directories a worker
killed mid-boot leaves in the package root (the kill phase of `test27` sweeps its own).

Regression run after the change: `test1`, `test4`, `test12`, `test15`, `test25` (the W16 risk
list) and `test27` green; `git status snapshots/` clean. Suite count became **26** (§5 rule 4; 27 with W15's `test24`, §6.4).

Stale note corrected: the W9 (b) entry above says “the machine has no modulo, subtraction or
division” — true on the bare-`master` branch it was written on, not on the integrated tree, which
carries `Divides`, `Gcd`, `Modulo`, `IsCoprime` (`math/arithmetic.py`, from `91dd5f7`) and the
signed `Whole*`/`Ring*` edges (W7). Residues beyond parity and divisibility chains are therefore a
wiring task for the functional-equation schemas, not a missing substrate.

### 6.4 Post-integration: W15 tutor (2026-10-14)

`dialogue.py` + `validation/test24_socratic_dialogue.py` (slot 24, W15's) landed on the
integrated branch; see §4 W15. Two machine facts the work turned up, for the next worker:

- **Bindings are identity-keyed and data atoms join by identity.** `Match` binds the pattern
  variable *object* (`FindBinding` uses `IdentityCompare`), and `MergeBindings` reconciles values
  with `TermEqual`, which treats two constructor-less atoms as unequal unless they are the same
  object — so a fresh `M.Char("p")` never joins a premise bound to another `Char("p")`, and a
  premise copied by `Instantiate` before matching loses its bindings. `dialogue.py` therefore
  interns every Char per session (`Tutor.intern`, the same discipline `packs.py` applies with
  `_char_atom`) and matches the *original* premise patterns (the `JoinPremises` discipline).
- **`RuleIsUnary` means single-premise, not pattern-rule.** Filtering on it drops 16 of the 38
  pack theorem rules (`even_ss`, `eq_symmetric`, the `thread_*` rules); the shape
  `KnowledgeRewriteSuccessors` rewrites is `ReplacementIsFactList`.

Regression run with the new labels and the `main.py` change: `test1`, `test4`, `test11`,
`test12`, `test14`, `test19`, `test22`, `test23` green; `git status snapshots/` clean.

### 6.5 Post-integration: W6 remainder and a measured kernel cost (2026-10-14)

`validation/test26_flt_descent.py` (slot 26) landed with `packs/infinite-descent.pack.yaml`,
three `playground.py` procedures and five labels (`PolynomialIdentityLabel`,
`ResidueTableLabel`, `CongruenceClassesLabel`, `EveryStateMovesLabel`, `NoStatesLabel`);
the pack is registered in `main.py:PACK_PATHS`. See §4 W6 for what is and is not claimed.
Two facts for the next worker:

- **Machine arithmetic is slow and gets slower.** Every `Add`/`Multiply`/`Modulo` result goes
  through `NatFromRep`, whose `TreeLookup` on `NatValueIndex` falls back to a linear scan of
  every entry (`trees.TreeLookup._lookup_entries`, `ExactKey` recomputed per entry) whenever
  the Patricia lookup misses — and for a new value it always misses — then inserts. Measured
  on a fresh runtime: ~0.2 s per operation on new values around 1000, ~0.6 s after two
  hundred more nats are interned, ~75 ms even for a hit. Profiled at 300 entries (20 hits +
  20 misses, 61 s): the miss fallback 27 s, the Patricia bucket scans 15 s, `TreeInsert`
  ~0.7 s per new value; `_is_bucketed_root`, suspected first, is 9 ms per lookup and not
  the cause; `core.py`'s `uuid4()` per allocation is 35 s of the 61 and is the untouchable
  floor. A sweep's cost is therefore quadratic in its size; `test26` keeps its bounds small
  for that reason and says so, and `test22`'s 215 s is mostly this. The fix is in the kernel
  (`trees.py`) and was **not** made here: it is opened as **W18** (§3, §4, slot `test30`;
  brief `delegation/W18-nat-index-lookup-cost.md` with the profile and a fix sketch) and
  needs coordinator sign-off because the file is kernel.
- **The identity procedure is reusable where symbolic algebra is not.** W7's norm
  multiplicativity and the IMO algebra schemas need identities the rewrite walker cannot
  reach; `PolynomialIdentityByGrid` decides any identity in the admitted fragment
  (`ExprAdd`/`ExprMul`/`ExprPow`, natural coefficients) and refuses the rest (`ExprNeg`,
  `ExprFrac`, `ExprDiv` — subtraction must be moved across the equation first, as `test26`
  does).

- **A kill-phase race in the W16 mesh, seen once.** `test27` was run twice after the pack
  registration: 51/51 on the second run, 49/51 on the first. In the failing run the SIGKILL
  of the victim also closed the *survivor's* coordinator connection for 0.2 s
  (`coordinator-lost`, then `rejoined`); the coordinator treated that as a second loss of the
  already re-dispatched unit, hit `max_attempts`, and finalised it `failed / worker-lost`
  while the survivor still held it queued; when the survivor finished its own unit and
  started the victim's, every job was terminal from the coordinator's view, it broadcast
  shutdown, and the survivor abandoned the unit (`abandoned-on-shutdown`; the
  `FileNotFoundError` from its restore shards is that abandonment removing the scratch
  directory under them). Nothing was silent — every outcome carried a reason — but the
  recovery clause (“the survivor hands in a real result”) failed. Not caused by W6; it is
  `networking/peer.py`'s loss handling counting a transient reconnect as an attempt, and it
  belongs to the W16/W17 owner. *Follow-up (2026-10-15, §6.8):* `arena/abf4a212`'s W2 fixes
  (`cbd546a`, `1e98d3e`) close the outcome side of this — a progress report for a job already
  recorded terminal is ignored (`progress-after-terminal-ignored`) and a real success now
  supersedes a *recorded* failure, not only a provisional one — so the survivor's late result
  stands when it arrives. The attempt double-count itself is unchanged; if the coordinator
  shuts down before the survivor starts the unit, the unit is still `abandoned-on-shutdown`.
  *Closed (2026-10-21, W33, §4):* a severed link is now a suspect for
  `reconnect_grace` before it is a loss, so the transient above charges no
  attempt, writes no terminal record (hence no shutdown cue), and is
  cancelled by the rejoin; `test45` reproduces this exact sequence.

Regression run: `test1`, `test3`, `test4`, `test5`, `test9`, `test12`, `test13`, `test18`,
`test19`, `test23`, `test24` green, `test27` green on rerun (above); `git status snapshots/`
clean.

### 6.6 Post-integration: W17 consensus (2026-10-14)

`consensus/ledger_sync.py` + `validation/test28_byzantine_ledger_consensus.py` (slot 28) landed:
in-process agreement under an adversarial schedule (crash, omission, duplicate, reorder, forged
entry, stale snapshot, split view). Design, in one breath: **verification, not voting** — a
delivery is admitted only if the peer re-derives the entry's receipt with Checker B over its own
trusted rules (`EntryReceiptVerdict`); the check policy is built from the receipt's own
session/start/goal, because rule licensing is the security boundary and session pinning is a
deployment concern; commits mirror `PromoteCandidate`'s head-insertion so a peer's ledger is
structurally `Compare`-equal to the origin's; out-of-order deliveries park on a version gap and
drain in version order; tombstones (rollback entries, which reuse the revoked entry's id) are
checked for a known target *before* the duplicate test; snapshots are refused if stale and
delivered entry-by-entry through the same admission path if ahead; a crashed peer is simply
excluded from the agreement set. `main.py` grew a `consensus` mode that replays a compact
schedule end to end. Suite 28: 26/26 checks, ~25 s. Full gate after the change: **29/29**
(test1–test29), which also retires the old W0 note about `test3` failing — it is green on the
integrated tree.

Machine facts the work turned up, for the next worker:

- **Ledger versions are fresh `Succ` atoms — compare them by value, never by identity.**
  `M.IdentityCompare(version, peano.two)()` is `False` even when the version *is* 2, because each
  `M.Succ` mints a new atom; `math.peano.NatEq(v, k, registry)` (GMP-backed) or structural
  `M.Compare` is the only sound test. `IdentityCompare` remains correct for label singletons.
- **`is M.truth_value` binds a Python bool.** `x = X(...) is M.truth_value` followed by
  `x is M.false_value` is always `False` — branch with `if not x:`. This silently dead-coded a
  whole branch of the delivery path until a forge test caught it.
- **Anonymous atoms are equal only to themselves.** `M.Compare` treats two freshly minted
  `M.Atom()`s as unequal (Chars with equal text do compare equal), so cross-run determinism of
  ledger *contents* is unassertable in machine terms — entry bodies are saturated with per-run
  identity atoms. Test 28 therefore asserts cross-run reproducibility on the decision skeleton
  (versions + statuses in commit order) and full structural identity only within a run (peer vs
  origin), which is the strong form anyway.
- **Sandbox bytecode is a live hazard**: restored files carry untrustworthy mtimes, so Python
  silently runs stale `.pyc`s after an edit (symptom: a `DEBUG` print that never fires,
  `inspect.getsource` disagreeing with the file). The tracked legacy `__pycache__` artifacts are
  removed in this commit; the directory stays gitignored.

### 6.7 Post-integration: W18 kernel lookup cost (2026-10-15)

`trees.py` + `validation/test30_nat_index_lookup_cost.py` (slot 30) landed under the
coordinator's kernel sign-off. Root causes, both in `trees.py`:

1. **`IndexAtomKey` collapsed every indexed atom to EmptyList.** All keys of equal cons
   shape — for `NatValueKey`, every value with the same digit count — tokenized to the
   same Patricia path and shared one leaf bucket, so every bucket scan was linear in the
   same-length population. Now the atom rides along as the payload. That is
   completeness-preserving: atoms are `TreeTermEqual` only when they are the same object,
   so equal exact keys still produce equal index keys and collide into one bucket, while
   distinct values diverge at their first differing digit. Buckets shrink to same-value
   duplicates, of which the bucket upsert keeps at most one.
2. **`TreeLookup._lookup_tree` scanned every interned entry on a Patricia miss.** For
   `NatFromRep` a miss is every new value, so interning was `Θ(entries)`. Now a
   current-layout bucketed root trusts the Patricia verdict (miss = absent); the O(entries)
   `_is_bucketed_root` validation walk is replaced by an O(1) root-label check (Patricia
   roots are bucketed by construction — `TreePatriciaInsert` only produces bucketed
   leaves). The linear fallback remains only where it is still needed: legacy-layout roots.

**Snapshot compatibility.** Old-layout trees (every existing snapshot) keep working: a
layout probe reassembles the first leaf's stored path (branch prefixes, choice tokens,
leaf suffix) and looks for an `IndexAtomKeyLabel` block whose payload is not EmptyList —
legacy paths never have one. Legacy roots take the old collapsed index key plus the
linear fallback (correct; taken only until the first insert), and that first insert
rebuilds the whole tree entry-by-entry under the current index keys, exactly like the
pre-existing legacy-BST migration. The key store is untouched by all of this — its paths
were always built from exact keys with real atoms, which is why interning already worked
across restores. `test12` (persistence) is green.

Measured on the same 2-vCPU box as the W6 numbers, fresh `make_fresh_runtime()`:

| situation | before | after |
| :--- | :--- | :--- |
| `NatFromRep`, 50 new values, fresh runtime | 0.22 s/call | 0.064 s/call |
| the same 50 again (index hits) | 0.086 s/call | 0.044 s/call |
| after 200 more nats interned, new values | 0.87 s/call | 0.088 s/call |
| 50 new values at ~300 interned | 1.47 s/call | 0.072 s/call |
| 20 hits at ~300 interned | 0.087 s/call | 0.036 s/call |

Per-call cost is flat in the number of interned entries (0.064 / 0.072 / 0.065 s at
50 / 350 / 900 entries — test30 asserts the ≤1.5× bound and measured 1.10). Wall clocks:
`test26` 121 → 60 s, `test22` 212 → 191 s, `test20` 100 → 78 s, cold boot
`make_fresh_runtime()` 12.8 → 2.5 s (the boot-time registry inserts were quadratic too).
`test27` ran 329 s vs 296 s before and `test29` 164 s vs 135 s — both within the
run-to-run variance those suites have shown (mesh kill-phase timing; pack search), both
green. Full gate after the change: **30/30** (`test1`–`test30`).

Machine facts for the next worker:

- **`Pair(...)` terms and `Edge` results peel differently.** `IndexPairKey(h, t)()` is an
  Edge call returning the term, but `Pair(h, t)` *is* the term and calling it returns
  `Atom.value` — `None`. A helper that returns raw terms from some branches and peeled
  Edge results from others will poison every uniform peel site with `None`s (this bit
  twice while building the layout probe). Pick one contract per helper; `.result` is the
  honest way to get an Edge's term raw.
- **The Patricia leaf suffix is the path *remainder*.** Anything inspecting stored paths
  from a leaf alone must also walk the branch prefixes and choice tokens above it — the
  discriminating tokens are often absorbed into a shared prefix.
- `math.peano`'s import-time `one`/`two`/`three` never pass through `NatFromRep`, so
  `nat(1) is peano.one` is and stays `False`; the index unifies only values that arrive
  through `NatFromRep`. Same value, different atom — do not assert node identity across
  those two worlds.

### 6.8 Second integration: every branch with commits after 2026-10-13 (2026-10-15)

All 76 remote heads were re-fetched and compared against this branch. Three had commits
newer than the first integration (§6.2); everything else is unchanged since then (the
pre-Hyge lineages and the 2026-10-07/08 branches were assessed in §6.1–6.2 and have not
moved). Merged, in this order, as true merges so each branch's history survives:

| Branch | New commits | What landed | Conflicts and how they were resolved |
| :--- | :--- | :--- | :--- |
| `arena/abf4a212` | `cbd546a`, `d6fd805`, `1e98d3e` | **W2 fixes in `networking/peer.py`**: a progress report for a terminal job is ignored instead of resurrecting it; a real success supersedes a recorded failure (provisional or not); `networking/README.md` and `test25` grew the two probes (51/51, 108 s). | `validation/test27_distributed_prover_swarm.py` **add/add**: the branch carried its own 18-check W16 suite (18/18, 239 s on that tree; findings: speedup negative at 140 s vs 56 s; plan equality holds within one transport only). The integrated 51-check suite (§6.3) already asserts the same four claims with the same transport discipline, so it was kept and the branch's suite dropped — its findings are recorded here. DAG §4 / delegation README kept the integrated W16–W18 entries. |
| `arena/6e28638f` | `a066b7b`, `03db9eb`, `1fa7d9b`, `640cc43` (+1) | **Ingest**: apoc CSV headers read natively; `probes/ingest_scale_probe.py` (ceiling is memory, ~10 KB resident per edge: 60k relations at 951 MB, 100k OOM on this box); `importers/sharded_import.py` + `probes/sharded_import_probe.py` (label-sharded snapshots, stub nodes so no shard has a dangling edge). | `.gitignore` (one glob covers both restore-scratch patterns). `SWARM_EVOLUTION_DAG.md`: the branch had **committed its own unresolved conflict markers** around the ingest-ceiling table; resolved by keeping that content in §6's preamble ahead of §6.1. |
| `arena/500df21f` | `3a40b88`, `6fcc568`, `5d07bf8` | **W17** (`consensus/ledger_sync.py`, `main.py consensus` mode, 10 labels, `test28` 26/26, 19 s) and **W18** (`trees.py`, `test30` 18/18, 35 s) — see §6.6 and §6.7; the 88 tracked `__pycache__` artifacts removed. | None (the branch was cut from this one at `675a21c`). |

**Constraint check on the merged tree.** `core.py` is byte-identical to `master`. The
kernel files (`machine.py`, `context.py`, `labels.py`, `proof.py`, `trees.py`, `graph.py`,
`matching.py`) grep clean for `isinstance`/`hasattr`/`type(`/`__class__`/`__new__`. One
follow-up was needed on the W18 change: `_layout_probe` collected machine terms in a Python
list (`segments = []`, twice — a copy in `TreeInsert` and one in `TreeLookup`), and three
accessor methods had been pasted into `TreePatriciaLookup`/`TreePatriciaInsert` on top of
their existing definitions (pyflakes: redefinition). Both fixed in `596d40b`: a single
module-level `_patricia_layout_is_current(walker, root)` collects the segments as a machine
list and both edges delegate to it; the duplicated accessors are gone. `test30` is unchanged
by the cleanup (0.041 → 0.043 s/call across 50 → 350 entries, ratio 1.06). `labels.py`'s W17
additions follow the label convention; `consensus/ledger_sync.py` keeps peers, ledgers,
entries, versions and reports as machine terms with the fault schedule in the suite.

**Full gate on the merged tree, 30/30, sequential on 2 vCPU, `git status` clean after**
(snapshots untouched, no restore scratch left behind):

| Suite | Result | Wall clock now | Before W18 |
| :--- | :--- | ---: | ---: |
| `test1`–`test11`, `test14`–`test17`, `test19` | green | 3–8 s each | — |
| `test12` persistence | 10/10 | 9 s | — |
| `test13` playground | green | 16 s | — |
| `test18` residue discovery | green | 17 s | — |
| `test20` Eisenstein | green | 52 s | ~100 s |
| `test21` geometry | 36/36 | 43 s | — |
| `test22` funceq/combinatorics | green | 122 s | 212–215 s |
| `test23` Engel | 80/80 | 41 s | — |
| `test24` tutor | 85/85 | 29 s | — |
| `test25` mesh (+2 probes) | 51/51 | 108 s | — |
| `test26` descent | 43/43 | 38 s | ~115 s |
| `test27` prover swarm | 51/51 | 213 s (speedup 0.83×) | 339–356 s |
| `test28` consensus | 26/26 | 19 s | new |
| `test29` funceq parity pack | 26/26 | 106 s | 135–164 s |
| `test30` nat index cost | 18/18 | 38 s | new |

The `test27` kill phase passed first time; see the follow-up note in §6.5 for what the W2
fixes change there. Scoreboard after this integration: W1–W5, W8–W18 done; W6 closed as
partial; W7 partial; W9(c) residue/divisibility schema wiring open. Suite slots `test1`–
`test30` were all taken at that point; W20 and W19 then took `test31` and `test32` (§6.9), so
**the next free slot is `test33`**.

### 6.9 Post-integration: W20 WAN mesh and W19 dump → shards (2026-10-15)

Both opened from one request — make the machine run across a laptop and a Colab notebook,
and make a Neo4j dump ingestible — and both landed on `arena/717c9822` the same day
(`aaac6de`, `6301d7c`, `70a5699`, `cedae50`, `8571449` + docs). Briefs:
`delegation/W20-wan-mesh.md`, `delegation/W19-neo4j-dump-to-shards.md`; runbook `colab/README.md`;
transport reference `networking/README.md` ("Beyond one filesystem").

**What was decided before writing code** (user's choices, asked up front). Dump decoding
happens **on Colab**: the notebook loads the dump into a Neo4j of the matching major version,
exports with `apoc.export.csv.all`, splits and shards — a `.dump` is a private, versioned
store format and nothing but Neo4j should decode it, and the laptop that runs the machine
should not also run a JVM database. WAN model: **the laptop is the coordinator behind a
tunnel and artifacts travel over the wire** — the jobs, the PKI and the results stay on the
machine the user owns; Colab dials out, verifies *who* it reached rather than *where*, and
holds nothing that outlives the session. Scope: both halves, loopback-tested in `test31` /
`test32`, the user runs the first real trial.

**A W2 defect found by W20.** The mesh `Connection` reads its socket from one thread and
writes from another. On the small control frames of `test25`/`test27` that never showed; the
first 3 MiB `artifact-chunk` did: an `SSLSocket` is one OpenSSL object, the reader's poll
`settimeout` landed inside the writer's `sendall`, and the link died intermittently with
`SSLEOFError` / a half-written record on one side and a stall on the other. `framing.Duplex`
replaces the pattern (non-blocking socket, one lock around every OpenSSL call, waits on
`select` with the lock released, `pending()` checked before every wait). Micro-benchmark
5/5 and `T31_PHASES=123` 6/6 after, flaky before; `test25` and `test27` green after.

**Purity.** Nothing new touches a machine term over the wire: `artifact-*` frames carry file
bytes the receiver loads through the codec, which is why §5 now says so as rule 7. The W19
splitter is CSV-to-CSV; the sharder and importer it feeds were already machine-counted.
`core.py` unchanged; kernel files unchanged.

**Gate on this tree, sequential on 2 vCPU**: `test31` 50/50 (59 s), `test32` 35/35 (38 s),
`test25` 51/51, `test27` all green (kill phase passed; the §6.5 race note still applies).
`git status` clean after each; no certificate or key under the tree (`test32` phase 5 checks
`git ls-files` for it).

**What is not verified and must be said plainly.** (1) The Neo4j cells of
`colab/neo4j_dump_to_shards.ipynb` — install, `neo4j-admin … load`, APOC export — were written
against the documented tooling and never executed (the sandbox has no route to
`dist.neo4j.org`); every code cell compiles and the pipeline is verified from the export
onward. (2) `colab/mesh_worker.ipynb` and the tunnel were never run against a real network;
`test31` runs the same CLI switches on loopback. The liveness window was tuned on loopback and
may need widening at tunnel latency — `member-lost`/`rejoined` pairs with no incident are the
symptom. (3) Both notebooks clone `arena/717c9822-cat-theo-machine` until this branch is
merged; a `master` coordinator does not speak the `artifact-*` frames.

**Scoreboard after this**: W1–W5, W8–W20 done (W6 closed as partial, W7 partial, W9(c) open).
Suite slots `test1`–`test32` taken; **the next free slot is `test33`**. Continuation: §7–§8 (opened 2026-10-19).

### 6.10 Third integration: the two post-W22 heads (2026-10-21)

Both post-W22 session lines descend from `45e4564` (W22) and were fast-forwarded from
`arena/717c9822-cat-theo-machine` (`a548d7d`) on 2026-10-19. They were integrated here
as a true merge (`--no-ff`) so both histories survive; the incoming head is merged
*into* this branch, not replaced by it.

| Branch | Head | What landed | Conflicts and how they were resolved |
| :--- | :--- | :--- | :--- |
| `arena/c58acfec-cat-theo-machine` (this line, via `arena/b94f5f2e-cat-theo-machine`) | `0b80aed`, then W33 `b7a94c6` | **W23** factorisation/`NatLess` substrate (`test35`); **W29** precise negative on the *n*=4 `EveryStateMoves` obligation (`test41`); constrained-natural witnesses (supplemental `test46`); **W33** mesh reconnect accounting (`test45`). | — |
| `arena/f0572ef6-cat-theo-machine` | `8fac788` | **W24** residue/divisibility schema wiring (`test36`); **W25** curriculum card loader (`test37`); **W26** geometry remainder (`test38`); editorial updates to `test21`/`test22`/`test24`/`test29`. | Exactly three files, listed below. |

Only three files had changed on both sides since the fork, and they were the only
conflicts; everything else auto-merged:

- `labels.py` — append-only union, per the standing rule. The two sides added 7 and
  48 `*Label` classes respectively since `45e4564`, with **zero shared names**; the
  merged registry has 498 classes, no duplicates, and the snapshot symbol table in
  `persistence.py` covers the union (the three classes registered by its runtime sync
  instead of the static list pre-date the fork, §6.2).
- `SWARM_EVOLUTION_DAG.md` — editorial union, no side's record dropped: §3 carries
  W23–W26, W29, W33; §4 runs W23, W24, W25, W26, W29, constrained witnesses, W33 in
  landing order with one integrated remainder; §5's gate count is now 41 suites; §7.2
  now states the signed-*expression* gap precisely (W23 supplies signed subtraction
  edges, W22's expression grammar still refuses signed operators); §7.5 records that
  the promotion loop has run in anger beyond `test22` (W24's transitivity, W26's
  Thales step); §8.1's start-now set is W27/W28/W32 with W30's receipt gate met.
- `delegation/README.md` — same treatment: W24–W26 marked landed with their suite
  counts, W30's row records its gate as met by W24/W26, and the dispatch-order
  paragraph describes the integrated three-parallel-session wave (W27, W28, W32).

**Constraint check on the merged tree.** `core.py` is byte-identical to `master` and
was touched by neither side. The kernel files (`machine.py`, `context.py`,
`labels.py`, `proof.py`, `trees.py`, `graph.py`, `matching.py`) grep clean for
`isinstance`/`hasattr`/`__class__`/`__new__`. No suite slot was renumbered: the
incoming `test36`–`test38` sit beside `test41` (W29), `test45` (W33) and the
supplemental `test46`, exactly as allocated.

**Full gate on the merged tree, 41/41 suites exit 0**, sequential on 2 vCPU,
~23 min; `snapshots/` untouched and no tracked file dirtied by the run. Suites with a
check fraction report it; the early demo-style suites pre-date the fraction
convention and are green in the §6.8 sense (run to completion, no exception — the
few with `assert`s would exit nonzero on failure; `test1`'s Failed root is its
longstanding recorded output, reproduced identically on the pre-merge head `b7a94c6`
as a control).

| Suite | Result | Wall clock |
| :--- | :--- | ---: |
| `test1`–`test11`, `test13`–`test20` | green | 4–54 s each |
| `test12` persistence | 10/10 | 10 s |
| `test21` geometry (updated by W26 line) | 37/37 | 51 s |
| `test22` funceq/combinatorics (updated) | all checks passed | 146 s |
| `test23` Engel | 80/80 | 47 s |
| `test24` tutor (updated) | 86/86 | 33 s |
| `test25` mesh | 51 passed, 0 failed | 137 s |
| `test26` descent | 43/43 | 45 s |
| `test27` prover swarm | 51 passed (kill phase: 1 redispatch; speedup 0.84×) | 235 s |
| `test28` consensus | 26/26 | 20 s |
| `test29` funceq parity (updated) | 26/26 | 117 s |
| `test30` nat index cost | 18/18 | 38 s |
| `test31` WAN mesh | 50 passed, 0 failed | 68 s |
| `test32` dump → shards | 35 passed, 0 failed | 45 s |
| `test33` witnesses (W21) | 8/8 | 4 s |
| `test34` grid proofs (W22) | 60 checks passed | 39 s |
| `test35` factorisation (W23) | 146/146 | 32 s |
| `test36` residue/divisibility (W24, new here) | 41/41 | 18 s |
| `test37` curriculum loader (W25, new here) | 62/62 | 18 s |
| `test38` geometry remainder (W26, new here) | 49/49 | 24 s |
| `test41` FLT *n*=4 (W29 negative) | 61/61 | 48 s |
| `test45` mesh reconnect (W33) | 20 passed, 0 failed | 26 s |
| `test46` constrained witnesses (supplemental) | 185/185 | 6 s |

**Scoreboard after this integration:** W1–W5, W8–W26, W33 done; W6 closed as
partial; W7 partial; W29 a precise negative (do not re-dispatch unchanged).
Remaining: W27, W28, W30, W31, W32. Suite slots `test1`–`test38`, `test41`,
`test45`, `test46` are taken; the next unoccupied allocated slot is `test39` (W27)
and the next never-allocated number is `test47`. Dispatch rules: §8.1 as integrated.

### 6.11 Fourth integration: the f42b3f12 head (2026-10-22)

`arena/f42b3f12-cat-theo-machine` forked at W33 (`b7a94c6`) — before the
§6.10 merge and before W27 — and landed three commits (`ff19a17`, `26a6969`,
`966e26f`) touching only `playground.py`, `main.py` (REPL dialogue, no new
agenda cases) and the new `validation/test47_dynamic_goal_lemma_suggestion.py`.
Content is recorded as the supplemental §4 entry above. After W27 landed
(`a603605`), the user asked for the latest commits to be pulled first; the
head was merged as a true merge (`a7aee56`, no conflicts — disjoint files),
so both histories survive.

**Defect found on integration**: the head was not green as committed.
`playground._pg_debug` called `sys.stdout` with no `sys` import; test47 and
test13 crashed with `NameError` on the merged tree (test18/test20, which do
not reach the debug path, passed). One-line repair on this branch
(`import sys`); test47 then passed **27/27** and test13 green. Recorded
here because "the suite on the branch" is only evidence once it has been
run on the tree that receives it.

**Full gate on the merged tree: 43/43 suites exit 0** (test39 53/53,
test47 27/27, test23 80/80, test21 37/37; demos rc=0). `core.py` untouched
on both sides. §5's gate count is now 43 suites; `test47` is taken as
supplemental, the next never-allocated number is `test48`, and the next
unoccupied allocated slot remains `test40` (W28). Scoreboard unchanged
otherwise: W1–W5, W8–W27, W33 done; W6/W7 partial; W29 precise negative.
Next work taken up on this branch at the user's direction: **W30**
(domain packs through the closed loop, slot `test42`) — its gate is met
(W24/W26 receipts) and W27 left it two transition-verified Engel
derivations awaiting receipts.

---

## 7. Five-dimension status (2026-10-19; integrated 2026-10-21, §6.10)

What the machine can do *now*, and what it still cannot, by dimension. Substrate (W1–W5, W16–W20, W18) is treated as the floor under all five, not as a sixth dimension.

### 7.1 Dimension 1 — FLT & Diophantine proving

**Done.**
- Modulus-4 obstruction for fourth powers is *discovered* by a Cartesian sweep, not written (`test18`). The machine's own arithmetic runs the residue case analysis; the promotion ledger refuses the candidate without a Checker B receipt.
- Modulus-9 obstruction for cubes, over the coprime-to-3 domain, is discovered the same way (`test20`). Generic quadratic-ring scaffolding (`RingAdd` / `RingMultiply` / `RingConjugate` / `RingNorm`) derives $N(1-\omega)=3$ from the relation $\omega^2=-1-\omega$; no norm formula is authored.
- Infinite-descent *strategy* is one authored schema (`Terminates(p) ∧ EveryStateMoves(p) → NoStates(p)`), on the same footing as `monovariant_terminates`. Pythagorean square identity in additive form, $x^4=(x^2)^2$, odd-squares $\equiv 1\pmod{4}$, and the mod-4 condition on $1+n^2\equiv m^2$ are *derived* by `PolynomialIdentityByGrid` / `ResidueTable` (`test26`, 43/43).
- Kernel lookup cost that made every sweep quadratic is gone (W18, `test30`). Arithmetic is flat-rate at ~40–75 ms/op (`core.py`'s `uuid4()` is the untouchable floor).

**Not done.**
- The $n=4$ theorem remains reduced to `EveryStateMoves(descent)` — "from every primitive solution a smaller one can be built". The original four-part substrate gap now has W21 witness introduction, W22 Checker-B grid proofs (not symbolic normalisation), and W23 subtraction/gcd-cofactor arithmetic plus Peano order schemas. These are enabling tools, **not** a derivation of "coprime factors of a square are squares" or of the descent's measure drop. W29 retried those obligations in test41 and reported a precise negative (§4), including the arithmetic value/identity transport gap. The theorem remains open.
- Unique factorisation in $\mathbb{Z}[\omega]$ and the cubic descent are not derived. W7 is `[~]`.
- Do not re-author a quartic or cubic pack. W6's withdrawal (`524de6f`) still binds.

**Continuation update.** W21–W23 are green (see §4). W28 ($n=3$) may start; W29 ($n=4$) has reported a precise negative and should not be rerun unchanged. W22 chose recorded grid proofs, not symbolic normalisation; its expression grammar still refuses signed operators even though W23 now supplies signed arithmetic subtraction.

### 7.2 Dimension 2 — IMO problems

**Done.**
- Goal-directed auxiliary constructions (`constructions.py`): bisector completion and circumcircle-at-a-vertex, instantiated through `Match` / `JoinPremises`, minted as anonymous `Thingy`s, dispatched as `Construction` planner methods. Negative controls: withhold the proposal, scalene the figure, or aim the goal at a length — nothing closes (`test21`, 36/36).
- Combinatorics / funceq / NT, two independent deliverables kept: (a) families 1–3 over the forward engine, miner and ledger (`test22`); (b) pack-based Cauchy and parity slice (`test29`). Cauchy is data; `math/funceq.py` compiles an equation into a unary rewrite schema. Family 1 closes a generic multi-premise rule on an opaque fact hypergraph, mines the terminating invariant, and promotes with a Checker B certificate.
- Multi-pass backward planner (W13, `test15`).
- **W9(c) closed by W24** (2026-10-19): eight constant-free schemas in `packs/funceq-nt.pack.yaml` consume `Divides` / `Gcd` / `Modulo` / `IsCoprime` records. Divisibility transitivity, the gcd's universal properties and Euclid's lemma are derived by the forward engine; residue addition and multiplication reduce through the machine's own `Mod` records. Checker B verifies the transitivity derivation and the ledger promotes it; `test36` 41/41.

**Not done.**
- No signed *expression* fragment in the funceq/schema compiler (W23 supplies signed arithmetic subtraction as edges, but W22's expression grammar still refuses signed operators), so residue-difference laws and d'Alembert-type equations remain out. Residue schemas are modulus-agnostic by construction but were exercised at 3, 5 and 7 only; no exhaustive modulus sweep is claimed.
- Chord/angle closure now exists (W26): same-segment equal angles, cyclic-quadrilateral opposite angles, Thales, and an antipode construction whose witness is minted -- so a circle feeds facts back into a goal instead of stopping at vertex incidence. Still open: angle measures and arithmetic on them (the centre-angle factor-two theorem), deciding a cyclic order from incidence, angle chasing beyond the bisector, projective collineations.
- W8's done-definition asked for Checker-B receipts, ledger records, evaluator ablation and figure sweeps. W26 supplied the first three for one configuration class (Thales, `test38`); the authoring suite `test21` still does not exercise them, and no figure sweep (randomised or enumerated configurations) is claimed.
- Curriculum held-outs are partly unblocked by W25: `IntegerLabel` / `ResidueLabel` / `CongruentLabel` and 27 more card-cited constructors exist, and two of the 24 cards compile (seven-glasses held-out solved through the Engel invariance schema, domino-board decoy refused). The other 22 still cite 48 absent constructors or lack an obligation generator, so extremal-set combinatorics remains without a held-out card; test22/[31] measures this rather than asserting impossibility.
- Closure engine is a single-chain saturator (test22/[32]): soundness, not completeness.

**Unblocks.** W27 landed 2026-10-22 (§4). W24, W25 and W26 are done. d'Alembert waits on a signed fragment that W22 did not deliver.

### 7.3 Dimension 3 — Engel strategies

**Done.**
- Strategy principles as *ontology and generic schemas*, not as three named problems: invariance, monovariants, semi-invariants, extremal, box-as-obligation (`packs/engel-strategies.pack.yaml`, `test23`, 80/80). Universality by fixpoint recursion over `MoveSet` (peel the head; empty list closes; a single failing move stops the recursion). Semi-invariant is honestly weaker (`NonIncreases` + obligated `EventuallyDecreases`). Box principle does not conclude a collision — `Pigeonhole` already obligationes the counting. Checkerboard colouring is invariance whose $\phi$ is a parity.
- Planner method terms `Monovariant`, `SemiInvariant`, `Invariance` with obligation/conclusion records.
- Two *unnamed* instances close through that machinery (W27, `test39` 53/53): Euclid-by-subtraction `Terminates` (144 states, 132 transitions) and chameleons `Unreachable`×3 (55 states, 108 transitions), built as graph facts in-suite; the pack is untouched (13 rules, re-pinned).
- Observables are data now: `LinearObservableLabel` heads a descriptor term (coefficient chain, modulus-or-raw) read by machine arithmetic. Ground-transition verifiers in `invariant_miner.py` certify or refute `Preserves` / `StrictlyDecreases` / `NonIncreases` over enumerated transition lists, refusing with (before, after, transition) witnesses; no transitions, no certificate. The chameleon observable (0,1,2) mod 3 was *mined*: 52 candidates swept, 10 certified, 42 refuted; with a lone-colour-change move added, nothing that survives separates (ablation).
- Strategies are proposed during planning: `ProposeStrategyMethods` turns declarations already in the facts (`Monovariant` + `MoveSet` + `BoundedBelow` under `Terminates`; `MoveSet` + `Reading`×2 + `Apart` under `Unreachable`) into method terms — term-equal to hand-written ones — and proposes nothing from incomplete declarations. `PlannerRun` decomposes the proposal and `PlannerStep` discharges at creation any method child whose goal is already a fact (withheld-fact ablation pinned per-child).
- Three older instance packs still work (`engel-coins`, `engel-means`, `engel-blackboard`). Curriculum rung builders exist (`curriculum.py`, `test10`) for synthetic graph tasks — not for the markdown cards.

**Not done.**
- Root closure *inside* `PlannerRun` / ordinary search is still open. Proposals fire and every supplied obligation discharges, but plan assembly to the root fails on this pack. Two blockers in `search/` were isolated and left unedited: a zero-step success is unrepresentable (an already-true goal yields an empty plan, recorded as failure — the same reason `test1`/`test2` roots are `FailedLabel`), and multi-pass fact saturation stalls after pass 1 though every rule passes the applicability filters and per-rule application derives each step (`test39` §[5] records the probes; the second blocker is observation-level). W27's two root pins are the checks that should flip when the search leg is repaired.
- Discovery is over finite enumerations with authored candidate spaces (linear forms, coefficients {0,1,2}, one modulus per sweep). No certificate quantifies over a symbolic move schema, and no domain pack (as opposed to in-suite graph facts) drives these rules from a real Engel problem that is not named in code.
- `StrictlyDecreases` / `NonIncreases` / `Preserves` claims are not independently verified as *discovered* claims: W25 hands them to the schema only after machine arithmetic has checked every split of the move, which verifies the premise's arithmetic but not the choice of observable. Held-out/decoy evidence now exists for one problem: seven-glasses closes through `thread_preserving_moves` → `preserving_moves_step` → `preserving_moves_empty` → `invariant_obstruction`; the domino decoy is refused (test37). The remaining 22 cards do not load. W27's certificates are the same kind of check, now over every enumerated transition, and the observable *choice* is mined and ablated — but no Checker-B receipt covers these Engel derivations yet (W30's remit).
- `main.py`'s theorem agenda still hardcodes `"Engel E1"`, `"Engel E2"`, `"Engel coin problem"`. Standing §5.3 tension; do not add more cases in that style.

**Unblocks.** W30: two transition-verified Engel derivations are now worth driving through the loop for receipts. The search-assembly repair is substrate work for whoever owns `search/` next; asked-for but not yet attempted: mining the seven-glasses observable (W25's held-out) with the ground-transition verifier, whose candidate space now exists.

### 7.4 Dimension 5 — Stories, explanations, Socratic tutor

**Done.**
- Surface grammar and lexicon (`surface_bridge.py`, `test11`).
- Proof storyteller: formal receipt $\to$ Markdown (`story_renderer.py`, `test14`).
- Socratic tutor as a *reader* of the machine, not a second knowledge base (`dialogue.py`, `test24`, 85/85). Concept inspection from loaded packs / definitions / ledger. Claims (arithmetic grammar) judged three ways: Checker-B verified, sweep-refuted, or undecided with both pieces of evidence. Questions from `BackwardObligations`, tagged with curriculum rungs. REPL fall-through in `live`, plus `load pack`.

**Not done.**
- Claim grammar is arithmetic-only. Other goals enter through `Tutor.set_focus_goal` / `assume`, not through the parser. Geometry, Engel, and FLT vocabulary are not conversational yet.
- Ledger ablation/holdout gates are *reported as not run*, not simulated — honest, but the tutor cannot yet explain a completed Dim-4 trial.
- Stories are of whatever receipt they are handed; they do not yet narrate a domain derivation from W8/W10/W6 because those receipts mostly do not exist.

**Unblocks.** W31, after W30 has receipts worth narrating. W31 can start earlier on existing arithmetic/Engel-pack goals if scoped that way.

### 7.5 Dimension 4 — Autonomous self-improvement

**Done.**
- Independent Checker B, including knowledge-rewriting / `FactsCover` (`test5`, `test19`).
- Invariant trace miner and candidate evaluator with ablation (`test8`, `test7`).
- Dual-ledger promotion loop; refuses entries without a receipt (`test9`).
- Byzantine ledger consensus: verification, not voting; peers re-derive receipts (`test28`).
- The closed loop exists as machinery.
- The loop has run over all three Phase 4b domains against one shared ledger (W30, `test42` 42/42): funceq transitivity, geometry Thales and both Engel closers promoted in sequence (versions 1–4); the two W27 Engel chains carry multi-step Checker-B receipts; gate 4 re-verifies ground-observable certificates by re-running the miner verifiers at promotion time (forged certificate refused); a withheld-rule ablation trial exists beside `AblationTrial`'s triviality check.

**Not done.**
- Most domain workers still do not *drive* the loop end-to-end. W8 and W10 authoring suites explicitly do not claim Checker-B / ledger / ablation, and W6/W7 discoveries are refused (correctly) because a sweep is not a derivation. The loop has now run beyond `test22` family 1, though: W24's divisibility transitivity is Checker-B verified and ledger-promoted (`test36`), and W26's Thales step carries a receipt plus evaluator/ablation/holdout (`test38`). W30 generalised this to the domain packs on a shared ledger (`test42`); what remains true is that the *authoring* suites (`test21`, `test23`) still do not exercise the loop themselves, and candidate macros remain single-rule-shaped -- multi-step domain arguments are receipted via `VerifyDerivation` and their closers are what the ledger promotes. Knowledge rewrite consumes matched premise facts, so replaying a monotone argument lists a multiply-used fact multiply.
- Two curriculum cards are evaluation data since W25 (one held-out solved, one decoy refused, test37); the other 22 still have no builder, so corpus-scale evaluation is not yet possible.
- A mined Engel observable is now promoted with its certificate re-verified at the gate (W30); nothing yet mines a *descent measure* (Dim 1) or a geometry observable and promotes it.

**Unblocks.** W31: real domain receipts -- four promotions on one ledger, plus two multi-step Engel derivations -- now exist for the storyteller/tutor to narrate. W28 would add Dim-1 receipts if the cubic descent ever closes.

### 7.6 Substrate notes that still matter

Independent of the five dimensions, still open, and *not* an excuse to reopen W1–W20:

- Swarm speedup **0.84×** on `engel_e2` (2 vCPU): the proof lives in one branch; unit-boot is 12–30 s (W32).
- Kill-phase race: **closed by W33** (2026-10-21, §4). A severed link is suspect for `reconnect_grace` (default 5 s) before it is a loss; only an absence longer than the grace still spends the one attempt, with W2's supersession as the outcome-side backstop.
- Snapshot format fork v3 vs v4: stay on v3; adoption unbought (§6).
- Real laptop ⇄ Colab trial and real Neo4j dump decode: user, not a sandbox worker (USER-1, USER-2).
- Merge this line to `master` so notebooks stop cloning a session branch (COORD).
- `core.py` `uuid4()` per allocation: out of scope.

---

## 8. Phase 4+ remaining-work DAG (opened 2026-10-19)

**Dispatch update:** W21–W26 are complete (§4). Their nodes below preserve the original
allocation/dependency plan, not instructions to re-run them. W28 may start; W29
has since reported a precise negative (§4) and must not be re-dispatched unchanged.
W33 is complete (2026-10-21, §4); do not re-dispatch it. The two post-W22 heads
were integrated on 2026-10-21 (§6.10); this tree descends from both.

```
═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
                          PHASE 4+ DAG — WHAT'S LEFT, WHO DOES IT, WHAT IT UNBLOCKS
═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════

[PHASE 4: Unblocking substrate]  (PARALLEL — 3 WORKERS; start immediately)
 ├── W21: Existential witness introduction
 │         Agent: Arena session on this repo, brief W21, slot test33
 │         Owns:  graph_task.py, checker_b.py (consume; do not weaken)
 │         Effect: a replacement variable unbound by premises mints a recorded
 │                 witness (Thingy/fresh atom). Descent steps can construct
 │                 (m,n) / (u,v,w) without authoring them. Checker B audits
 │                 the introduction or refuses it.
 │         Do not: edit core.py / machine.py / proof.py without coordinator
 │                 sign-off. Prefer minting in graph_task after Instantiate.
 │
 ├── W22: Algebraic rewriting
 │         Agent: Arena session, brief W22, slot test34
 │         Owns:  invariance.py (RewriteEquals), playground.py
 │         Effect: identities PolynomialIdentityByGrid already decides become
 │                 rewrite derivations, not evidence. Unblocks ring steps of
 │                 W6/W7 and d'Alembert (Dim 2).
 │         Do not: touch math/arithmetic.py (that's W23). Use WholeNegate /
 │                 "move subtraction across the equation" until W23 lands.
 │
 └── W23: Factorisation substrate & derived NatLess
           Agent: Arena session, brief W23, slot test35
           Owns:  math/arithmetic.py, math/peano.py (extend, sort-generic)
           Effect: subtraction / root-or-factor edges exist as *generic*
                   arithmetic; some schema concludes a NatLess fact from
                   machine arithmetic (not a sweep). Unblocks coprime-square-
                   factors (W6) and well-founded decrease (W6/W10).
           Do not: write unique factorisation in Z[ω] (that's W28). Do not
                   conclude FLT.

      │
      │   W21/W22/W23 have disjoint file ownership. labels.py is append-only
      │   union. If two sessions add the same label name, the later rebase loses.
      ▼

[PHASE 4b: Domain remainders that are unblocked *now*]  (PARALLEL with Phase 4 — 4 WORKERS)
 ├── W24: Residue / divisibility schema wiring  ✅ DONE  (Dim 2, was W9(c))
 │         Agent: Arena session, brief W24, slot test36 — landed 2026-10-19
 │         Owns:  packs/funceq-nt.pack.yaml, math/funceq.py
 │         Result: eight constant-free schemas derive residue and divisibility
 │                 facts from records of the existing Divides/Gcd/Modulo/
 │                 IsCoprime edges. test36 41/41; Checker B verified; ledger
 │                 promoted the transitivity schema. Do not re-dispatch.
 │
 ├── W25: Curriculum card loader  ✅ DONE               (Dims 2, 3, 4)
 │         Agent: Arena session, brief W25, slot test37 — landed 2026-10-19
 │         Owns:  curriculum.py, labels.py (IntegerLabel, ResidueLabel, …)
 │         Result: 24 records, 2 compiled, 22 refused with reasons; the
 │                 seven-glasses held-out closes through the Engel invariance
 │                 schema, the domino decoy is refused; 48 Ground 1 gaps
 │                 reported. test37 62/62. Do not re-dispatch.
 │
 ├── W26: Geometry remainder  ✅ DONE                    (Dim 2)
 │         Agent: Arena session, brief W26, slot test38 — landed 2026-10-19
 │         Owns:  constructions.py, packs/geometry-constructions.pack.yaml
 │         Result: three chord/angle schemas + antipode construction;
 │                 Checker B verified, ledger promoted, four ablations.
 │                 test38 49/49. Do not re-dispatch.
 │
 └── W27: Engel remainder                               (Dim 3)
           Agent: Arena session, brief W27, slot test39 — landed 2026-10-22
           Owns:  invariant_miner.py, planner.py, labels.py (append-only);
                  packs/engel-strategies.pack.yaml untouched
           Result: two unnamed instances closed; observable mined, not
                   handed in; strategies proposed in PlannerRun with
                   supplied obligations discharged; root closure inside
                   search pinned open (two search/ blockers). test39 53/53.
                   Do not re-dispatch.

      │
      ▼ (Sequential gate: W21 + W22 + W23 green. W24–W27 need not wait.)

[PHASE 5: FLT remainders]  (PARALLEL — 2 WORKERS; do not start early)
 ├── W28: Eisenstein UFD + cubic descent                (Dim 1, W7 remainder)
 │         Agent: Arena session, brief W28, slot test40
 │         Prereqs: W21, W22, W23, W7 [~]
 │         Effect: unique-factorisation *scaffolding* used on Z[ω]; cubic
 │                 descent attempted. Honest [~] still allowed. No cube
 │                 identity authored.
 │
 └── W29: Discharge EveryStateMoves                     (Dim 1, W6 remainder)
           Agent: Arena session, brief W29, slot test41
           Prereqs: W21, W22, W23, W6 [~]
           Effect: the missing list in test26 is re-tried with the new
                   substrate. First reachable of {full, partial, precise
                   negative}. Do not re-execute W06's brief as written.

      │
      ▼ (Sequential gate: at least one of W24–W29 produces a Checker-B receipt)

[PHASE 6: Closed loop and language]
 ├── W30: Domain packs through Checker B + ledger + ablation     (Dim 4)
 │         Agent: Arena session, brief W30, slot test42 — landed 2026-10-22
 │         Prereqs: W12 ✅, and receipts from W24–W27 (W28–W29 if present)
 │         Result: one shared ledger, four promotions across the three
 │                 domains; Engel chains Checker-B receipted; certificate
 │                 provenance re-verified at gate 4; withheld-rule ablation.
 │                 test42 42/42. Do not re-dispatch.
 │
 └── W31: Tutor and storyteller beyond arithmetic                (Dim 5)
           Agent: Arena session, brief W31, slot test43
           Prereqs: W15 ✅, W14 ✅; richer if W30 has run
           Effect: claim grammar and Socratic questions cover geometry /
                   Engel / (optionally) FLT vocabulary; a story is generated
                   from a real domain receipt, not a fixture.

[PHASE 7: Ops — independent of Phases 4–6, start any time]
 ├── W32: Swarm unit-boot cost                          (Infra)
 │         Agent: Arena session, brief W32, slot test44
 │         Owns:  persistence.py, search/distributed_engine.py
 │         Effect: per-unit boot no longer dominates swarm wall-clock;
 │                 test27 speedup re-measured and reported, not tuned.
 │
 ├── W33: Mesh reconnect attempt accounting  ✅ DONE    (Infra)
 │         Agent: Arena session, brief W33, slot test45 — landed 2026-10-21
 │         Owns:  networking/peer.py
 │         Effect: a 0.2 s coordinator-lost/rejoined is not a second
 │                 attempt; test27 kill phase is no longer racy.
 │                 test45 20/20 (§4). Do not re-dispatch.
 │
 ├── USER-1: Laptop ⇄ Colab WAN trial
 │         Agent: the user, not an Arena worker
 │         Effect: first real `--artifacts wire` + `--no-inbound` +
 │                 identity-verify run; colab/README.md names the ledger
 │                 events to read. Sandbox cannot do this.
 │
 ├── USER-2: Real Neo4j dump decode
 │         Agent: the user, on Colab
 │         Effect: neo4j-admin load + APOC export executed; W19's notebook
 │                 cells stop being documentation. Sandbox has no route to
 │                 dist.neo4j.org.
 │
 └── COORD: Merge this line to master
           Agent: repository owner
           Effect: notebooks clone master; a master coordinator speaks
                   artifact-* frames. Two stale pre-swarm PRs (#3, #4)
                   should be closed or rebased, not merged as-is.

[OUT OF SCOPE]
 └── core.py uuid4() per allocation (~40–75 ms/op floor)
 └── Snapshot v4 adoption (49 branches, +701/−225 in persistence.py, unread)
```

### 8.1 Dispatch rules for Phase 4+

1. **Start immediately (no prereq gate):** W32. W21–W27, W30 and W33 are done (§4); do not re-dispatch them. File ownership is disjoint except `labels.py` (append-only union, as in §6.2). W22 added the brief-authorised Checker-B grid clause after W21 landed; it preserves witness checking.
2. **W28 may start; W29 has reported.** W21–W23 are green, but test41 closes W29 as a precise negative. Reopen only after the named generic/proof gaps change. Do not treat gcd extraction as unique factorisation or a conditional order proof as a proved descent.
3. **W30 has landed** (`test42`): the shared-ledger promotions exist, gate 4 re-verifies ground-observable certificates, and the loop's current shape is pinned (single-rule macros; premise-consuming replay). W31 is richer now that real domain receipts exist; do not restate the loop over the same instances.
4. **One slot per brief**, already allocated above. `test33`–`test39`, `test41`, `test42`, `test45` and supplementals `test46`, `test47` are taken; the next unoccupied allocated slot is `test40` (W28). Do not invent a number for something else.
5. **W22 vs W23:** if a session believes it *must* edit the other's files, stop and report; do not take a silent dependency.
6. Honest `[~]` and precise negatives remain first-class outcomes (W6 is the model).
7. Work only on the branch the session is pinned to. Do not open a pull request. Report as in `delegation/README.md`.

### 8.2 Lineage note (2026-10-19)

`arena/5d1b2a18-cat-theo-machine` was opened from `master` (`428ecdc`, 2026-08-25) and fast-forwarded to `arena/717c9822-cat-theo-machine` (`a548d7d`, 2026-10-15) so this session would not re-fork the swarm. Notebooks still clone `717c9822` until COORD merges to `master`; that is USER/COORD, not a worker.

**Third integration (2026-10-21, §6.10).** The swarm forked again at W22
(`45e4564`) into `arena/c58acfec-cat-theo-machine` (`0b80aed`: W23 `7dc84ba`,
W29, constrained witnesses) and `arena/f0572ef6-cat-theo-machine` (`8fac788`:
W24 `02e8240`, W25 `8cde7c1`, W26). This branch is the first of those plus
W33 (`b7a94c6`, chosen because `networking/peer.py` was byte-identical on
both heads, `b4fcaea`); `f0572ef6` is merged into it as a true merge, so
both histories survive. The earlier warning against re-dispatching W24–W26
from the un-integrated tree is thereby discharged: on this tree they are
landed work (`test36`–`test38`), and the next unoccupied allocated slot was
`test39` (W27, since landed).
