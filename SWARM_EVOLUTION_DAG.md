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
| **W7** | FLT $n=3$ Eisenstein Factorization | Dim 1 | `playground.py` (`RunPlaygroundFilteredPowerSweep`, `DiscoverSeparatingModulus`), `math/arithmetic.py` (`Ring*`), `validation/test20_flt_eisenstein_discovery.py` | W3 | Mod-9 obstruction discovered live, $N(1-\omega)=3$ derived; UFD and cubic descent open |
| **W8** | IMO Geometry & Aux Construction | Dim 2 | `constructions.py`, `packs/geometry-constructions.pack.yaml`, `planner.py` (`Construction`) | W4 | Goal-directed auxiliary-point schemas, slot `test21` |
| **W9** | IMO Combinatorics & Func-Eq | Dim 2 | `math/funceq.py`, `graph_task.py` (`ForwardDeriveFacts`), `packs/funceq-nt.pack.yaml` | W4 | Families 1–3 over the forward engine / miner / ledger (slot `test22`); pack-based functional-equation and parity slice (slot `test29`) |
| **W10**| Engel Monovariants & Invariants | Dim 3 | `packs/engel-strategies.pack.yaml`, `planner.py` (`Monovariant`, `SemiInvariant`, `Invariance`) | W3, W4 | Semi-invariants, colouring as invariance, box principle obligationed; suite slot `test23` |
| **W11**| Invariant Trace Miner & Evaluator| Dim 4 | `invariant_miner.py`, `evaluator.py`| W4 | Trace state extractor, holdout regression gate |
| **W12**| Dual-Ledger Promotion Loop | Dim 4 | `promotion_ledger.py` | W11, W1 | End-to-end autonomous discovery & rollback ledger |
| **W13**| Multi-Pass Backward Planner | Dims 1,2,3 | `planner.py`, `graph_task.py` | W6, W8, W9, W10 | Decomposed goal scheduler, auxiliary search |
| **W14**| Proof Storyteller & Narratives | Dim 5 | `story_renderer.py` | W5, W4 | Formal receipt $\to$ LaTeX/Markdown mathematical story |
| **W15**| Socratic Dialogue & Tutor | Dim 5 | `dialogue.py`, `main.py` | W5, W12 | Interactive concept inspection, counterexample REPL |
| **W16**| Distributed Prover Swarm | Swarm | `search/distributed_engine.py`, `networking/jobs.py`, `main.py` (`swarm`, `mesh --swarm`) | W2, W13 | Partitioned frontier worker mesh, work-stealing; `validation/test27_distributed_prover_swarm.py` (51/51, ~340 s) |
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
- [ ] **W15 (Conversational Socratic Tutor & Concept Explorer)**: Ready for execution.
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
- [ ] **W17 (Byzantine Ledger Consensus & Monotonic Snapshot Broadcast)**: Dependent on Phase 2;
  W2 ✅, W12 ✅, W1 ✅ — unblocked, not started.

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
4. **Verification Requirement**: Every new worker module or pack must include an automated verification suite in `validation/` with $100\%$ green test results before promotion. There are currently **26** suites — `test1`–`test23`, `test25`, `test27`, `test29` (slots 24, 26, 28 are pre-allocated to W15, W6-remainder, W17 and still open) — each a standalone script. Run one with `PYTHONPATH=<repo-parent> python -u validation/testN_*.py` (the suites insert the package parent onto `sys.path` themselves and import as `cat_theo_machine.*`).
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

**Snapshot format fork (open item).** Both reconciled lineages write snapshot format **version 3**, and agreement was mistaken for safety: across all 72 branches, **49 write version 4 and only 22 write version 3**. This branch's codec raises `Unsupported snapshot version` on a v4 file, so real state on those branches — `snapshots/set-b-cumulative.json`, `snapshots/library-only-control.json`, and the `search_compare` runs on the `01a05cb0` / `01a05d5d` / `01a06274` / `01a06542` / `01a06923` / `01a06cca` family — cannot be loaded here. The incompatibility is one-directional: v4's loader gate is `version not in (3, 4)`, so v4 branches *can* read what this branch writes. Neither fork is a superset — v4 routes `constructor_registry` through a `_registry_entries_snapshot_root()` abstraction and has **no** `nodes`/`edges` root and **none** of the four optional roots, so it lacks both this branch's hypergraph fix and the lineages' planner/ledger/task/invariant state. Decision: stay on v3, because ingesting foreign graphs needs exactly the three things v4 lacks. Cost of a later adoption is **unknown and deliberately unbought** — v4's `persistence.py` differs by +701/−225 lines and nobody has read them. Revisit only if state from those 49 branches becomes wanted.

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
list) and `test27` green; `git status snapshots/` clean. Suite count is now **26** (§5 rule 4).

Stale note corrected: the W9 (b) entry above says “the machine has no modulo, subtraction or
division” — true on the bare-`master` branch it was written on, not on the integrated tree, which
carries `Divides`, `Gcd`, `Modulo`, `IsCoprime` (`math/arithmetic.py`, from `91dd5f7`) and the
signed `Whole*`/`Ring*` edges (W7). Residues beyond parity and divisibility chains are therefore a
wiring task for the functional-equation schemas, not a missing substrate.
