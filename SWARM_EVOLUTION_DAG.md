# Hyge Multi-Agent Swarm Evolutionary Trajectory & DAG Specification

This document specifies the evolutionary architecture, dependency DAG, worker allocation, and synchronization protocols for coordinating Arena agents evolving the Hyge Theorem Prover.

Phases 0–3 (W1–W20) landed by 2026-10-15; their record is §2–§6. **Remaining work is §7 (five-dimension status) and §8 (Phase 4+ DAG, W21–W33).** Next free suite slot is `test33`. This copy of the tree was fast-forwarded onto `arena/5d1b2a18-cat-theo-machine` from `arena/717c9822-cat-theo-machine` (`a548d7d`) on 2026-10-19.

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
| **W22**| Algebraic rewriting (normalise identities) | Substrate / Dim 1 | `invariance.py` (`RewriteEquals`), `playground.py` | none | Grid-decided identities become rewrite derivations. Brief: `delegation/W22-algebraic-rewriting.md`. Slot `test34` |
| **W23**| Factorisation substrate & derived `NatLess` | Substrate / Dim 1 | `math/arithmetic.py`, `math/peano.py` | none | Subtraction/factor edges; a schema that concludes `NatLess`. Brief: `delegation/W23-factorisation-natless.md`. Slot `test35` |
| **W24**| Residue / divisibility schema wiring | Dim 2 | `packs/funceq-nt.pack.yaml`, `math/funceq.py` | W9 ✅ (edges already exist) | `Divides`/`Gcd`/`Modulo`/`IsCoprime` used by schemas, not just host edges. Brief: `delegation/W24-residue-divisibility-wiring.md`. Slot `test36` |
| **W25**| Curriculum card loader | Dim 2/3/4 | `curriculum.py`, `labels.py`, `curriculum/` | none | Markdown cards become executable graph tasks; held-outs load. Brief: `delegation/W25-curriculum-loader.md`. Slot `test37` |
| **W26**| Geometry remainder | Dim 2 | `constructions.py`, `packs/geometry-constructions.pack.yaml` | W8 ✅ W4 ✅ | Cyclic-quad / chord-angle schemas; Checker-B receipts in-suite. Brief: `delegation/W26-geometry-remainder.md`. Slot `test38` |
| **W27**| Engel remainder | Dim 3 | `packs/engel-strategies.pack.yaml`, `invariant_miner.py`, `search/` | W10 ✅ | Real Engel instances as evaluation data; strategies fire in search. Brief: `delegation/W27-engel-remainder.md`. Slot `test39` |
| **W28**| FLT $n=3$ UFD + cubic descent | Dim 1 | `playground.py`, `math/arithmetic.py` | W21, W22, W23, W7 `[~]` | Unique factorisation scaffolding used, cubic descent attempted. Brief: `delegation/W28-flt-n3-ufd-descent.md`. Slot `test40` |
| **W29**| FLT $n=4$ discharge `EveryStateMoves` | Dim 1 | `validation/test26_flt_descent.py` (do not weaken), new `test41` | W21, W22, W23, W6 `[~]` | Re-open W6 only after witness+factorisation land. Brief: `delegation/W29-flt-n4-everystate.md`. Slot `test41` |
| **W30**| Domain packs through the closed loop | Dim 4 | `checker_b.py`, `promotion_ledger.py`, `evaluator.py` | W12 ✅, W24–W27 | Geometry/Engel/funceq derivations earn receipts or stated refusals. Brief: `delegation/W30-domain-promotion-loop.md`. Slot `test42` |
| **W31**| Tutor/story beyond arithmetic | Dim 5 | `dialogue.py`, `story_renderer.py` | W15 ✅ W14 ✅ | Claims and stories over geometry/Engel/FLT vocabulary. Brief: `delegation/W31-dialogue-beyond-arithmetic.md`. Slot `test43` |
| **W32**| Swarm unit-boot cost | Infra | `persistence.py`, `search/distributed_engine.py` | W16 ✅ | Cut the 12–30 s per-unit boot that makes swarm speedup negative. Brief: `delegation/W32-swarm-boot-cost.md`. Slot `test44` |
| **W33**| Mesh reconnect attempt accounting | Infra | `networking/peer.py` | W2 ✅ W16 ✅ | Transient reconnect is not a second attempt; kill-phase race closed. Brief: `delegation/W33-mesh-reconnect-accounting.md`. Slot `test45` |

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
- [ ] **W21–W33 (Phase 4+, opened 2026-10-19)**: See §7–§8. None started. Next slot `test33`.

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
4. **Verification Requirement**: Every new worker module or pack must include an automated verification suite in `validation/` with $100\%$ green test results before promotion. There are currently **32** suites — `test1`–`test32` (no open slots; Phase 4 pre-allocates `test33`–`test45`, see §8) — each a standalone script. Run one with `PYTHONPATH=<repo-parent> python -u validation/testN_*.py` (the suites insert the package parent onto `sys.path` themselves and import as `cat_theo_machine.*`).
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

---

## 7. Five-dimension status (2026-10-19)

What the machine can do *now*, and what it still cannot, by dimension. Substrate (W1–W5, W16–W20, W18) is treated as the floor under all five, not as a sixth dimension.

### 7.1 Dimension 1 — FLT & Diophantine proving

**Done.**
- Modulus-4 obstruction for fourth powers is *discovered* by a Cartesian sweep, not written (`test18`). The machine's own arithmetic runs the residue case analysis; the promotion ledger refuses the candidate without a Checker B receipt.
- Modulus-9 obstruction for cubes, over the coprime-to-3 domain, is discovered the same way (`test20`). Generic quadratic-ring scaffolding (`RingAdd` / `RingMultiply` / `RingConjugate` / `RingNorm`) derives $N(1-\omega)=3$ from the relation $\omega^2=-1-\omega$; no norm formula is authored.
- Infinite-descent *strategy* is one authored schema (`Terminates(p) ∧ EveryStateMoves(p) → NoStates(p)`), on the same footing as `monovariant_terminates`. Pythagorean square identity in additive form, $x^4=(x^2)^2$, odd-squares $\equiv 1\pmod{4}$, and the mod-4 condition on $1+n^2\equiv m^2$ are *derived* by `PolynomialIdentityByGrid` / `ResidueTable` (`test26`, 43/43).
- Kernel lookup cost that made every sweep quadratic is gone (W18, `test30`). Arithmetic is flat-rate at ~40–75 ms/op (`core.py`'s `uuid4()` is the untouchable floor).

**Not done.**
- The $n=4$ theorem is reduced to `EveryStateMoves(descent)` — "from every primitive solution a smaller one can be built". Discharge is blocked by four missing *generic* abilities, not by a missing FLT pack: (1) existential witness introduction, so a rule can mint the $m,n$ / $u,v,w$ a descent step constructs; (2) ring normalisation, so `RewriteEquals` reaches identities the grid already decided; (3) a factorisation substrate, so "coprime factors of a square are squares" is derived rather than evidenced on 6 instances; (4) a schema that *concludes* a `NatLess` fact, so the measure drop is derived rather than swept.
- Unique factorisation in $\mathbb{Z}[\omega]$ and the cubic descent are not derived. W7 is `[~]`.
- Do not re-author a quartic or cubic pack. W6's withdrawal (`524de6f`) still binds.

**Unblocks.** W21, W22, W23 (substrate, parallel). Then W28 ($n=3$) and W29 ($n=4$).

### 7.2 Dimension 2 — IMO problems

**Done.**
- Goal-directed auxiliary constructions (`constructions.py`): bisector completion and circumcircle-at-a-vertex, instantiated through `Match` / `JoinPremises`, minted as anonymous `Thingy`s, dispatched as `Construction` planner methods. Negative controls: withhold the proposal, scalene the figure, or aim the goal at a length — nothing closes (`test21`, 36/36).
- Combinatorics / funceq / NT, two independent deliverables kept: (a) families 1–3 over the forward engine, miner and ledger (`test22`); (b) pack-based Cauchy and parity slice (`test29`). Cauchy is data; `math/funceq.py` compiles an equation into a unary rewrite schema. Family 1 closes a generic multi-premise rule on an opaque fact hypergraph, mines the terminating invariant, and promotes with a Checker B certificate.
- Multi-pass backward planner (W13, `test15`).

**Not done.**
- **W9(c)** — residue and divisibility schema *wiring*. `Divides`, `Gcd`, `Modulo`, `IsCoprime` exist in `math/arithmetic.py`; the funceq/NT packs do not use them. Residues beyond parity are a wiring task, not a missing substrate.
- Cyclic-quadrilateral conclusion schema; circumcircle stops at vertex incidence and does not feed chord/angle facts back into goals. Angle chasing beyond the bisector, projective collineations: open.
- W8's done-definition asked for Checker-B receipts, ledger records, evaluator ablation and figure sweeps. The authoring branch did not have those modules; they are on this tree now and `test21` still does not exercise them.
- d'Alembert-type equations need a minus term. Extremal-set combinatorics and curriculum held-outs are blocked on the card loader (W25): every corpus file is blueprint-only, `IntegerLabel` / `ResidueLabel` / `CongruentLabel` are absent, and test22/[31] asserts that held-out evidence is currently impossible.
- Closure engine is a single-chain saturator (test22/[32]): soundness, not completeness.

**Unblocks.** W24 (wiring, now), W25 (loader, now), W26 (geometry remainder, now). d'Alembert waits on W22.

### 7.3 Dimension 3 — Engel strategies

**Done.**
- Strategy principles as *ontology and generic schemas*, not as three named problems: invariance, monovariants, semi-invariants, extremal, box-as-obligation (`packs/engel-strategies.pack.yaml`, `test23`, 80/80). Universality by fixpoint recursion over `MoveSet` (peel the head; empty list closes; a single failing move stops the recursion). Semi-invariant is honestly weaker (`NonIncreases` + obligated `EventuallyDecreases`). Box principle does not conclude a collision — `Pigeonhole` already obligationes the counting. Checkerboard colouring is invariance whose $\phi$ is a parity.
- Planner method terms `Monovariant`, `SemiInvariant`, `Invariance` with obligation/conclusion records.
- Three older instance packs still work (`engel-coins`, `engel-means`, `engel-blackboard`). Curriculum rung builders exist (`curriculum.py`, `test10`) for synthetic graph tasks — not for the markdown cards.

**Not done.**
- No domain pack drives these rules from a *real Engel problem* that is not named in code. Discovery of a measure or an observable (rather than being handed one) is open. Strategy rules do not fire during ordinary search — nothing proposes them the way the planner methods do.
- `StrictlyDecreases` / `NonIncreases` / `Preserves` claims are not independently verified. Held-out/decoy evidence against `curriculum/heldout` and `curriculum/decoys` is blocked on W25.
- `main.py`'s theorem agenda still hardcodes `"Engel E1"`, `"Engel E2"`, `"Engel coin problem"`. Standing §5.3 tension; do not add more cases in that style.

**Unblocks.** W27 (remainder, now). Measure *discovery* also wants the miner (already there) plus W25 for held-outs.

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

**Not done.**
- Domain workers mostly do not *drive* the loop. W8 and W10 authoring suites explicitly do not claim Checker-B / ledger / ablation. W6/W7 discoveries are refused (correctly) because a sweep is not a derivation. Family 1 in `test22` is the one place the full loop has run on a combinatorics macro.
- Curriculum cards cannot be evaluation data until they load (W25).
- Nothing yet mines a descent measure or a geometry observable and promotes it.

**Unblocks.** W30, once W24–W27 (and later W28–W29) produce derivations rather than evidence.

### 7.6 Substrate notes that still matter

Independent of the five dimensions, still open, and *not* an excuse to reopen W1–W20:

- Swarm speedup **0.84×** on `engel_e2` (2 vCPU): the proof lives in one branch; unit-boot is 12–30 s (W32).
- Kill-phase race: a transient reconnect still counts as an attempt; W2's 2026-10-15 fixes close the *outcome* side (late success supersedes a recorded failure) but not the double-count (W33).
- Snapshot format fork v3 vs v4: stay on v3; adoption unbought (§6).
- Real laptop ⇄ Colab trial and real Neo4j dump decode: user, not a sandbox worker (USER-1, USER-2).
- Merge this line to `master` so notebooks stop cloning a session branch (COORD).
- `core.py` `uuid4()` per allocation: out of scope.

---

## 8. Phase 4+ remaining-work DAG (opened 2026-10-19)

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
 ├── W24: Residue / divisibility schema wiring          (Dim 2, was W9(c))
 │         Agent: Arena session, brief W24, slot test36
 │         Owns:  packs/funceq-nt.pack.yaml, math/funceq.py
 │         Effect: schemas derive residue and divisibility facts using the
 │                 existing Divides/Gcd/Modulo/IsCoprime edges. Family 3
 │                 grows past parity without new host arithmetic.
 │
 ├── W25: Curriculum card loader                        (Dims 2, 3, 4)
 │         Agent: Arena session, brief W25, slot test37
 │         Owns:  curriculum.py, labels.py (IntegerLabel, ResidueLabel, …),
 │                a loader over curriculum/tier0|tier1
 │         Effect: held-out and decoy cards become evaluation data. W9/W10
 │                 done-definitions that required them become reachable.
 │         Do not: encode solutions in cards; cards stay evaluation data.
 │
 ├── W26: Geometry remainder                            (Dim 2)
 │         Agent: Arena session, brief W26, slot test38
 │         Owns:  constructions.py, packs/geometry-constructions.pack.yaml
 │         Effect: at least one cyclic-quad or chord/angle schema; the suite
 │                 exercises Checker B / ledger / ablation that W8 deferred.
 │
 └── W27: Engel remainder                               (Dim 3)
           Agent: Arena session, brief W27, slot test39
           Owns:  packs/engel-strategies.pack.yaml, invariant_miner.py,
                  a search-hook (not a new agenda case in main.py)
           Effect: at least two unnamed Engel instances solved by the
                   strategy machinery; strategies proposed during ordinary
                   search; miner asked to find a measure on one of them.

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
 │         Agent: Arena session, brief W30, slot test42
 │         Prereqs: W12 ✅, and receipts from W24–W27 (W28–W29 if present)
 │         Effect: the closed loop is no longer only a combinatorics-family-1
 │                 demo. Geometry / Engel / funceq (and FLT if receipts exist)
 │                 either promote or refuse for a stated reason.
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
 ├── W33: Mesh reconnect attempt accounting             (Infra)
 │         Agent: Arena session, brief W33, slot test45
 │         Owns:  networking/peer.py
 │         Effect: a 0.2 s coordinator-lost/rejoined is not a second
 │                 attempt; test27 kill phase is no longer racy.
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

1. **Start immediately (no prereq gate):** W21, W22, W23, W24, W25, W26, W27, W32, W33. Nine sessions, disjoint file ownership except `labels.py` (append-only union, as in §6.2).
2. **Do not start W28 or W29** until W21–W23 have reported. Re-opening FLT without witness introduction will reproduce test26's negative account.
3. **W30 waits** on at least one new domain receipt. Running it against the present tree would only restate that W8/W10 suites do not exercise the loop.
4. **One slot per brief**, already allocated above. Do not invent `test33` for something else.
5. **W22 vs W23:** if a session believes it *must* edit the other's files, stop and report; do not take a silent dependency.
6. Honest `[~]` and precise negatives remain first-class outcomes (W6 is the model).
7. Work only on the branch the session is pinned to. Do not open a pull request. Report as in `delegation/README.md`.

### 8.2 Lineage note (2026-10-19)

`arena/5d1b2a18-cat-theo-machine` was opened from `master` (`428ecdc`, 2026-08-25) and fast-forwarded to `arena/717c9822-cat-theo-machine` (`a548d7d`, 2026-10-15) so this session would not re-fork the swarm. Further Phase 4+ work on this session lands here. Notebooks still clone `717c9822` until COORD merges to `master`; that is USER/COORD, not a worker.
