Status: SUCCESS (all 9 items assessed)
Scope: proof.py, search/engine.py, search/model.py, search/runtime.py, knowledge.py, constructors.py, runtime.py, probes/

1. Production/Diagnostic Applicability Instrumentation Separation
Verdict: IMPLEMENTED ✅

File	Line(s)	Finding
proof.py	802–808	Docstring for FilterApplicableRules: "Contains no timing, no pretty-printing, no Peano probe counters and no per-rule debug calls. Diagnostic admission lives in FilterApplicableRulesProbe"
proof.py	811–918	FilterApplicableRules.__init__ / _filter — pure production code, zero timing, zero _debug, zero Peano counters
proof.py	921–1087	FilterApplicableRulesProbe — Mirrors FilterApplicableRules but records per-rule anchor/bucket/match timings, Peano attempt and rule-index counters, and emits a per-rule debug line. Never used by the production admission path.
proof.py	935	self._probe_rule_index = M.Zero — Peano counter confined to probe
proof.py	1006–1027	time.time() calls confined to FilterApplicableRulesProbe._rule_head_applicable
search/engine.py	700, 732	graph._search_probe_disable_applicable_shards gate controls shard vs. non-shard path — probe flag controls production behavior
2. Retained Head/Exact Indexes in SearchTheoremCursor
Verdict: PARTIAL ⚠️

File	Line(s)	Finding
search/model.py	1764–1836	SearchTheoremCursor struct: 8 slots: rules, generated, knowledge_head_index, knowledge_exact_trie, delta, next_delta, provenance, actions_rev — full struct exists
search/model.py	1856–1861	SearchTheoremCursorHeadIndex accessor — retrievable
search/model.py	1865–1872	SearchTheoremCursorExactTrie accessor — retrievable
search/engine.py	809–818	_theorem_cursor_for constructs cursor with all 9 args, including knowledge_head_index, knowledge_exact_trie, delta
search/engine.py	1174	_advance_theorem_cursor creates continuation cursor: SearchTheoremCursor(rest_rules, next_generated)() — only 2 args, OMITS head_index and exact_trie
search/engine.py	1203	Continuation cursor: SearchTheoremCursor(rest_rules, next_generated)() — same omission
Gap: When DFS creates continuation states for backtracking, the cursor is rebuilt with only rules and generated. The knowledge_head_index and knowledge_exact_trie are dropped, meaning subsequent cursor reuse loses the precomputed indexes.

3. Incremental Conclusion/Index Updates (Semi-Naive Closure)
Verdict: MISSING ❌

File	Line(s)	Finding
probes/theorem_closure_probe.py	55–74	Iterative closure: recomputes head_index and exact_trie from scratch per round via _theorem_indexes_for() — no delta propagation
search/model.py	1798–1803	SearchTheoremCursor has delta (slot 4) and next_delta (slot 5) fields — present but unused
search/engine.py	763–827	_theorem_cursor_for accepts and passes delta parameter (line 771: delta = knowledge_exact_trie) but no incremental update logic
knowledge.py	—	No KnowledgeTrieInsertDelta or incremental index update primitives exist
Gap: The struct has delta/next_delta scaffolding but no code implements delta-based incremental index building. Each theorem-cursor construction rebuilds head/exact indexes fully.

4. All-Binding Enumeration
Verdict: MISSING ❌

Search	Result
grep "all.binding|AllBinding|all_binding|enumerate.*binding|binding.*enum" across entire workspace	0 matches
All premise matching uses single-path M.Match + recursive _match_premises	No all-binding iterator exists
Gap: No all-binding enumeration primitive or pattern exists anywhere in the codebase. The system uses single-binding matching exclusively.

5. Admission/Readiness Fusion
Verdict: IMPLEMENTED ✅

File	Line(s)	Finding
proof.py	1181–1315	GoalHeadRuleOrdererWithIndex — single class that computes readiness AND ordering
proof.py	1231–1259	_make_entry: computes ready_count, total_count, unmatched = total - ready per rule — fused admission + ordering
proof.py	1266–1291	_prefer_left: sorts by (fully-ready first, higher ready count, fewer unmatched, higher total premises) — ordering key derived from admission data
proof.py	1240–1258	For rules with premise_meta present, uses cached premise metadata; falls back to live _premise_ready checks otherwise
The fusion means rules are admitted (filtered) and ordered in a single pass, avoiding separate admission and ordering phases.

6. Process Lifetime/Shard Sizing
Verdict: PARTIAL ⚠️

File	Line(s)	Finding
search/engine.py	635	shard_width = M.four — hardcoded constant for theorem applicability sharding
search/compare.py	53–60	_comparison_machine_parallelism derived from cpu_count(), capped at 4 (M.four), minimum 1 — concrete but not configurable per-search
search/runtime.py	509–577	_SearchModeWorkerExecutor: long-running while loop, receives setup/packets via queue — process pool with reuse for comparison mode
search/runtime.py	170–197	_SearchApplicableRulesShardWorker: one-shot fork process per shard, no pool reuse — no process lifetime for theorem sharding
probes/	—	No process-lifetime or shard-sizing probes exist
Gap: Sharding parallelism is hardcoded. Theorem applicability uses one-shot processes; only comparison mode has long-running executor processes. No configurable shard width or pool size parameter.

7. DFS Transposition
Verdict: PARTIAL ⚠️

File	Line(s)	Finding
search/engine.py	341–346	_search_mode_uses_global_visited() returns M.truth_value only for BFS/Beam/AStar — DFS/RewriteDFS return M.false_value
search/engine.py	369–371	_initial_search_job_visited() returns M.EmptyList for DFS modes
search/engine.py	1698–1702	_initialize_job_visited() returns M.EmptyList for non-global-visited modes
search/engine.py	1874–1879	_filter_new_child only applies to global-visited modes; DFS bypasses
search/engine.py	1119–1168	SearchBFS._advance_state — DFS path uses per-state seen chain (local) + generated Patricia tree (cursor-local), no transposition
search/engine.py	1187–1189	Theorem cursor checks self._tree_contains(generated, next_term) — cursor-local, not global
Gap: BFS/Beam/A* use Patricia-tree-based global visited transposition. DFS modes (both theorem and rewrite) use only local seen chains and cursor-scoped generated trees. No global transposition table for DFS.

8. Exact-Trie Goal Tests
Verdict: IMPLEMENTED ✅

File	Line(s)	Finding
search/engine.py	947–956	_goal_reached: when IsKnowledge(current), builds or uses knowledge_exact_trie and calls K.KnowledgeTrieHasFact(knowledge_exact_trie, goal, ...) — exact trie lookup for goal
proof.py	849–856	FilterApplicableRules._rule_has_missing_required_premise_head: for concrete (non-variable) premises, uses K.KnowledgeTrieHasFact(self._knowledge_exact_trie, premise, ...) — exact trie for premise validation
proof.py	884	FilterApplicableRules._rule_head_applicable: for variable-free anchors, returns K.KnowledgeTrieHasFact(self._knowledge_exact_trie, anchor, ...) — exact trie for anchor check
search/engine.py	969–973	_match_premises: for concrete premises, uses K.KnowledgeTrieHasFact(knowledge_exact_trie, premise, ...) — exact trie in matching
knowledge.py	172–182	KnowledgeTrieHasFact uses KnowledgeTrieLookup with ExactKey — correct O(log n) implementation
9. Proposed Edits Need Not Touch core.py
Verdict: CONFIRMED ✅

File	Line(s)	What it imports from core
runtime.py	15	from . import core as Core — only for Core.sync_from_namespace() at line 1571
constructors.py	57–84	Imports core primitives (Atom, Edge, EmptyList, Head, IdentityCompare, Pair, Tail, etc.) — the canonical indirection layer
proof.py	7–45	Imports from machine, heuristics, labels, schemata — never imports core
search/engine.py	10–21	Imports from machine, heuristics, labels, proof, etc. — never imports core
search/model.py	9–22	Same pattern — never imports core
knowledge.py	3–4	Imports from labels, machine — never imports core
search/runtime.py	10–25	Imports from machine, heuristics, etc. — never imports core
All new proof/search/knowledge constructs route through the constructors.py → machine.py layer. No edits to core.py needed.

Forbidden Constructs Already Present
These exist in files the user asked to audit, outside of explicit diagnostic-only classes:

File	Line(s)	Construct	Production/Diagnostic
proof.py	1090–1133	GoalHeadApplicableRuleBuckets: time.time(), _debug()	Production-accessible (no diagnostic label, called from GoalHeadRuleBuckets at line 1171–1178 and GoalHeadRuleOrderer at line 1800–1809)
proof.py	1885–1914	RewriteAtPath: _debug() with _debug_term()	Production-accessible (called from search engine)
proof.py	1924–1937	BuildDerivation: _debug() calls	Production-accessible
proof.py	2046–2062	ApplyAction (in proof.py continuation): _debug() calls	Production-accessible
proof.py	2405–3164	Prove._stage_*: extensive _debug() calls	Production-accessible
search/runtime.py	186–196, 537–546	print() + traceback.print_exc() in exception handlers	Error path only — low risk
Summary Table
#	Recommendation	Status
1	Production applicability instrumentation separation	✅ IMPLEMENTED
2	Retained head/exact indexes in SearchTheoremCursor	⚠️ PARTIAL (struct exists; continuation cursors drop them)
3	Incremental conclusion/index updates (semi-naive closure)	❌ MISSING
4	All-binding enumeration	❌ MISSING
5	Admission/readiness fusion	✅ IMPLEMENTED
6	Process lifetime/shard sizing	⚠️ PARTIAL (hardcoded, no per-search config)
7	DFS transposition	⚠️ PARTIAL (BFS/Beam/A* have it; DFS does not)
8	Exact-trie goal tests	✅ IMPLEMENTED
9	Edits need not touch core.py	✅ CONFIRMED
Key findings: 4 of 9 fully implemented; 3 partial with clear gaps; 2 missing entirely. The GoalHeadApplicableRuleBuckets class and RewriteAtPath/BuildDerivation/Prove methods contain timing/debug in production-accessible paths — cleanup candidates.