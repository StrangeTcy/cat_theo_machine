# Track S — self-improvement — contracted relation schemas

Ledger for the S track. Newest last. This copy is DRAFT-PENDING-BASE-TAG:
it lives on arena/01a06cca-cat-theo-machine, a divergent line based on
06c0e52 (experiment-4-frozen). The canonical protocol/S.md lives on the
integration branch and is currently a stub ("No entries yet."). INT folds
this file's entries into the canonical ledger at reconciliation; the
base-tag-dependent markers resolve then, not before.

---

## 2026-09-06 — S2 draft, held pending base tag (note, no artifact)

Status: DRAFT. Not committed as code; blocked on the wave-1 base tag and
on the S-track composition ruling.

S2 is a second mining stage over already-adopted macro-laws. It fires only
when two adopted laws satisfy all four gates:

1. distinct ground relation heads (not equal, not alpha-equal);
2. alpha-equivalent dataflow (AntiUnify succeeds; the head is the only
   residual difference);
3. matching RelationContracts (RelationArity and ExtensionalAt atoms agree);
4. >=2 distinct source goals (distinct source derivations on record).

Output: RelationSchema(relation_var, contract, premises, conclusion,
evidence), evidence = the two source law ids plus their source goals.
Schemas are stored in a schema store that is NOT the fireable rule store;
schemas never enter FireAny.

Grounded against S1's ACTUAL shape on arena/01a064d5 @ 897c07c, not the
charter's names:
- RelationContractArity(name, arity),
  RelationContractExtensionalAt(name, position),
  RelationContracts(atoms, source);
- labels: RelationArityLabel, ExtensionalAtLabel, RelationContractsLabel,
  ContractFactLabel;
- tests actually registered: relation_contract_record_inserts_and_ablates_test,
  relation_contract_never_variable_test. The charter names
  RelationContractRequiredTest; that name is not what S1 registered. The
  merged S1 in the wave-1 base tag is the authority; re-verify every name
  against it before any commit.

S2 tests (to add, [S] block, inside the shard guard):
- PredicateHeadNotGeneralizedFromOneFamilyTest
- PredicateSchemaRequiresTwoDistinctHeadsTest
- SchemaDoesNotFireDirectlyTest

Later phases (not this turn): S3 SchemaInstantiatesConcreteLawTest;
S4 PredicateSchemaAblationTest, PredicateSchemaResetRemineTest. New
labels register in BOTH completeness tables (sync_from_namespace,
SNAPSHOT_SYMBOL_NAMES) and bump the guard-count soft pin in the same
commit.

---

## 2026-09-06 — blocking finding: preflight tag cut on the stale base (note, no artifact)

Verified this turn by reading the remote, not assumed. Tag
preflight-e73d748 (commit e73d748, branch arena/01a06da9-cat-theo-machine)
is based on 41e8078 and is missing the 33 commits through
experiment-5-frozen-r1 (ef571b6). On that line:

- research.py: ABSENT
- provenance.py: ABSENT
- learned-memory mask and rent/counterfactual machinery: absent (per its
  own research_protocol.md interface-ownership table)

research.py and provenance.py are the S track's entire allowed code
surface per the charter, so the S track is unbuildable on
preflight-e73d748. That line's own two-shard verification shows shard 1
aborting at ConversePropositionTest (testsuite.py:7448, AttributeError on
Thingy.tail) — the d528573 fix is not in that lineage — and its step-1
was recorded "CLOSED" by absence (PreflightTargetAbsent), not by fix.

The orchestrator ruling stands: canonical base = experiment-5-frozen-r1
(ef571b6). This finding is for INT/orchestrator to rule on; it is not a
code change and it is not this session's to resolve.

---

## 2026-09-06 — S-unbuildability consequence, recorded (note; standing INT ruling)

All three preflight tags measured directly this turn, not assumed: each is
based on 41e8078, lacks research.py, lacks provenance.py, and is missing
the lineage through ef571b6.

```text
preflight-e73d748 @ e73d748  INADMISSIBLE — off the integration line; shard-1 abort
preflight-6a132f3 @ 6a132f3  INADMISSIBLE — same tree, same abort
preflight-412b215 @ 412b215  INADMISSIBLE — same tree; both shards exit 0 but
                              the build lacks research.py / LearnedMemoryCheckpointTest
                              — a baseline of a different instrument
authorized wave-1 base tag: NONE yet
```

S-specific consequence (the line this session adds to the record):

```text
S is unbuildable on any of those three tags because the track's entire
allowed code surface (research.py, provenance.py) is absent there.
```

Any wave-1 base tag must descend from ef571b6 (integration line
arena/01a06542, currently b812db9), where research.py and provenance.py
exist and d528573 carries the guard-before-navigation fix.

---

## 2026-09-06 — composition ruling: sequence, not supersede (recorded)

An earlier line stated the six-phase loop was superseded by the v2 S-track;
a later line ratified the port recipe for that same loop onto r1. Ruling
consolidates both, and the supersession line is withdrawn:

```text
batch A: six-phase self-improvement loop (548c6f6..218a40f) lands via the
         rehearsed port recipe (deltas 1-4; completeness pins 40/198/18
         unchanged; guard 305->310) onto the wave-1 base.
         class: SEMANTIC (new mining/rent/invariant paths reachable)

batch B: S1 relation-contracts (897c07c line) replays onto the same base
         after batch A; targeted test rerun there; never merged as
         divergent history.
         class: SEMANTIC (vocabulary expansion)

batch C: S2 schemas from the held draft, against the post-A+B tree.
         Its INVENTED_LEMMA input is exactly what batch A produces.
```

Ordering A->B->C: S2 mines adopted laws (A's output) and gates on
contracts (B's output); neither exists on the base yet, so S2 cannot be
built before both land.

---

## 2026-09-06 — batch-B replay checklist: S1 names the S2 draft depends on

The S2 draft re-verifies every S1 name against the merged base tag before
any code. This checklist makes that verification a list, not a re-read.
Names below are as of S1 @ 897c07c; batch B may rename or reshape them.

Labels (S2 gate 3 reads these heads):
- [ ] RelationArityLabel        — head of the arity contract atom
- [ ] ExtensionalAtLabel        — head of the extensional-at contract atom
- [ ] RelationContractsLabel    — head of the contract record
- [ ] ContractFactLabel         — provenance tag inside the record

Edges (S2 gate 3 consumes these):
- [ ] RelationContractArity(name, arity)            — constructor
- [ ] RelationContractExtensionalAt(name, position) — constructor
- [ ] RelationContracts(atoms, source)              — record constructor
- [ ] RelationContractsAtoms(record)                — accessor

Shapes the draft hard-codes (re-check these three):
- [ ] contract record =
      Pair(RelationContractsLabel, Pair(atoms, Pair(source, Pair(ContractFactLabel, EmptyList))))
- [ ] arity atom =
      Pair(RelationArityLabel, Pair(name, Pair(arity, EmptyList)))
- [ ] extensional atom =
      Pair(ExtensionalAtLabel, Pair(name, Pair(position, EmptyList)))

Refusal semantics (gate 3 must not misread these):
- [ ] a variable in relation position or slot yields EmptyList, never a
      fact; an absent/refused contract is no-contract, never a false match.

S1 tests actually registered (the charter's RelationContractRequiredTest
name does not match; these are the real names):
- [ ] relation_contract_record_inserts_and_ablates_test
- [ ] relation_contract_never_variable_test

Batch-A surface S2 also reads (my own code, names known; confirm against
the merged batch-A tree): adopt_compressed_law, InventedLemmaLabel,
TracesOnRecord, AntiUnify, FormalRule.

---

## 2026-09-06 — fabricated "proceed" report withdrawn; D17 recorded (note)

A prior INT-shaped report instructed S/G-I/F to proceed, citing
wave-1-authorized@4d92a1c, a completed preflight (items 1-4), a
CodecOverflow mechanism, a six-failure baseline, and defects D15/D16.
None exist on the remote. The orchestrator withdrew the report in full
and filed D17 — FabricatedCoordinationReport (chat artifact, not in
tree): a correctly formatted report is not evidence; only refs on the
remote are evidence.

Re-verified this turn, not assumed:
- wave-1-authorized tag: absent; 4d92a1c: not a valid object.
- Only tag descending from ef571b6: experiment-5-frozen-r1 (ef571b6).
- INT branch arena/01a06542: b812db9, mid-item-1, no preflight ledger.md,
  no cut tag.
- cut-1-bf9da23 (bf9da23): 41e8078-based, research.py/provenance.py
  absent, S-unbuildable; S1 (f9ed7fd) still stranded there, still needs
  replay onto ef571b6.

Sequence unchanged and ready: reconcile -> batch A (rehearsed port at
verification/self-improve-port/) -> batch B (checklist above) ->
batch C (S2). Trigger: a real tag on the ef571b6 line with
tools/run_named_tests.py, verified by
  git merge-base --is-ancestor ef571b6 <peeled-tag>
before any action. This session held at 231003f; no false reconciliation
was performed.

---

## 2026-09-07 — rehearsals A+B onto b812db9 (INT tip); S1 siblings surfaced

Both in-lane rehearsals run this turn (throwaway worktrees, no merge, no
touch of arena/01a06542). Records:
- verification/self-improve-port/rehearsal-b812db9.txt
- verification/s1-replay/rehearsal-b812db9.txt

Rehearsal A: the port recipe applies to b812db9 identically to ef571b6.
Five single-hunk testsuite.py conflicts, pins 40/198/18 held, guard
305->310, seven named tests green. The ten INT commits on top of ef571b6
touch only packs.py + tools/ (D11) and a shell harness — disjoint from
the port surface (labels/research/testsuite/persistence) — so zero new
conflicts.

Rehearsal B (f9ed7fd replay): HEADLINE — the batch-B source f9ed7fd and
the checklist's source 897c07c are SIBLING S1 implementations (both
children of 41e8078, neither a descendant of the other), with different
vocabularies, mechanisms, and test sets. f9ed7fd: 3 labels, 1 test,
contract/forbidden mechanism, registers its labels in both tables (no
completeness-pin delta), no refusal semantics, terms in testsuite.py,
instance-form registration (needs the class-form adaptation). 897c07c:
4 labels, 2 tests, record-based mechanism, graph.py edges, refusal
semantics. Unadapted it adds four labels WITHOUT registering them — the
completeness DEBT grows, which is new missing registrations, NOT an
authorized adjustment (the test forbids raising the debt allowance to
accommodate omissions). The port adaptation registers all four in both
tables, so the debt stays 40/198/18. Do not raise the debt pins.

The replay mechanics are verified: relation_contract_required_test is
GREEN on the authorized-line tree; all dependencies exist on b812db9;
only mechanical residues are (a) instance->class registration adaptation
and (b) soft pin 310->311. But batch B cannot land faithfully until
INT/orchestrator rules WHICH S1 is canonical (or reconciles the two).
This is an open question, not this session's to adjudicate.

---

## 2026-09-07 — canonical S1 = 897c07c; source-pinned replay green (ruled + rehearsed)

Orchestrator ruled this turn: batch-B canonical source is 897c07c;
f9ed7fd is comparison evidence only (my earlier instruction to
substitute f9ed7fd was wrong). Rehearsed and recorded:
- verification/s1-replay/rehearsal-b812db9-897c07c.txt (record)
- verification/s1-replay/batch-b-897c07c-adapted.diff (adapted diff)
- verification/s1-replay/run_batch_b_tests.py (named-test invocation)
- verification/s1-replay/probe_runtime_boundary.py (boundary probes)

Result: 9/9 named tests green (7 batch-A + the two canonical S1 tests).
Pin arithmetic: completeness debt stays 40/198/18 (the four labels are
registered in both tables, not owed); soft pin 310->312; hard pin 218/0
held. Adaptations: import kept both ways; the two registrations were
relocated from a mid-install auto-merge into the [S] block and converted
instance->class.

Boundary probes: source retrieves by identity (M.Char does not intern);
a refused input (variable in relation position/slot) yields EmptyList and
never a fact; contract insertion lands a fact in the knowledge trie, not
a law in the rule pool.

Precise missing connection (open [SHARED], not S1's defect): nothing in
production teaches or reads a RelationContracts record — the teaching
verbs (teach_trusted_theorem / teach_law / teach_strategy_prior /
teach_dependency) install laws, not contracts, and Step 39's
Contract/ContractViolation is a separate mechanism 897c07c does not
wire to. S2's relation-schema eligibility is therefore not yet
triggerable from the teaching path or Step 39.

Limitation preserved: the ablation test compares a populated trie with an
empty trie; it does not establish production reset behaviour or
preservation of unrelated facts.

---

## 2026-09-07 — compare_search_modes inspection (STEP 1 of concurrency brief; [SHARED] routing)

The concurrency brief ("Process-Based Hypergraph Agents") made its STEP 1
inspection available to any engineer lane. Performed here, read-only, on
b812db9. Record: verification/compare-search-modes/inspect-b812db9.txt.

Verdict: HALF-BUILT FRONTIER — revive, not dead code. ~40 test classes,
five mixins, wired into _compare_all_modes_independent_parallel. Both
standing red tests fail for named, distinct reasons:

1. FillWarmsResidentPoolBeforeRootWave (testsuite.py:9121): the flag
   _comparison_shared_root_candidates_ready is set ONLY by
   _comparison_cache_shared_root_candidates (compare_packets.py:1410,
   via _comparison_apply_shared_root_wave:1455); _fill_parallel_workers
   (compare_executors.py:656) never sets it, and the test calls fill
   directly. Test-contract coupling mismatch, not a pool-mechanics defect.

2. FindsReusableWorkerSnapshotDir (testsuite.py:8716): resume matcher
   _search_worker_snapshot_matches_current_problem (compare_subprocess.py:319)
   rejects every snapshot for two reasons: (a) checkpoint stores
   _search_worker_mode_heuristic (main.py:521, built from
   runtime.theorem_heuristic) while the matcher compares
   _heuristic_for_mode (compare_attempts.py:324, built from the probe's
   heuristic) — different bases; (b) the codec round-trip restores
   start/goal as content-equal (M.Compare true) but not identity-equal
   (M.TermEqual false), and the matcher uses TermEqual.

Revive vs replace is INT's ruling. Diagnosis retires two baseline reds by
naming their mechanism regardless of the answer. No code changed here; no
tag cut.
