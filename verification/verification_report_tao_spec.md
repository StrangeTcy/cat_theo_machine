# Verification Report — tao_problem_1_1_hypergraph_spec.md

Verdict: **PASS** (all acceptance criteria verified against repository code).

## 1. AP predicates replaced with existing Sequence(name, base_value, pattern, replacement)
- Doc §"Arithmetic progression in the existing sequence representation" (L160–207) uses only the existing `Sequence` constructor; no invented AP predicate.
- `Sequence(name, base_value, pattern, replacement)` confirmed: `constructors.py:520–530` (exactly 4 stored args); accessors `SequenceName/Base/Pattern/Replacement` at `constructors.py:533–595`.
- Only concrete construction is `SqrtSeq` (constructors.py:665): base `a`, pattern = name applied to `Succ(n)`, replacement = Newton-step expression — matches doc L168.
- Doc claim "no IndexDomain, ConsecutiveIntegerDomain, TermAt, SequenceLength, binary ArithmeticProgression(q,d)" — repo-wide scan: none exist.
- Recurrence shape in doc (L172–191) maps q(0)=x, q(n+1)=q(n)+d onto the four Sequence fields; sampled at 0,1,2 (L193–197).

## 2. Explicit missing AP unfolding/equality rules (L209–257)
- Rule 1 base unfolding q(0)→x; Rule 2 successor unfolding via stored pattern/replacement; Rule 3 concrete q(1)→x+d, q(2)→(x+d)+d; Rule 4 normalization/equality q(0)=b−d, q(1)=b, q(2)=b+d, q(0)+q(2)=2b; Rule 5 finite-use boundary. Explicit.
- "No installed theorem or rewrite rule consumes SequencePattern/SequenceReplacement" verified: repo-wide only definitions (constructors.py:565,585), label plumbing (machine.py:165–166), exports (math/real.py) — no pack/rule consumption.

## 3. heuristics.py described accurately (L354–374), no misattribution
- Six controls: `Heuristic(search_mode, rule_order_mode, beam_width, alpha, beta, canonical_strength)` (heuristics.py:172–186).
- `HeuristicCanonicalize`: strength flag (0=off); normalizes knowledge, recursively canonicalizes pairs (heuristics.py:244–282).
- `HeuristicGoalHeadIndex` (heuristics.py:15–40), `HeuristicGoalHeadNeighborhood` (backward through unary rules whose replacement head is admitted; heuristics.py:42–86), `HeuristicGoalHeadAllowsSubterm` (heuristics.py:88–102) — all as described.
- Anchor preference order lower fanout → fewer variables → greater specificity → earlier premise position matches `DefaultAnchorPreferenceHeuristic` (heuristics.py:158–166); consumer in proof.py:821,939.
- "None of these operations creates a new goal" (L374) — accurate; planner section explicitly separates new behavior (L420, L464–465, L535); `GoalHeadRuleOrderer` exists (proof.py:1807) and only reorders rules.

## 4. One explicit goal per SearchJob; SearchState fields (L378–403)
- SearchJob fields start/goal/rules/heuristic/status/frontier+counters/result plan/visited/theorem-rule cache/rewrite-rule bundle match `SearchJob.__init__` (search/model.py:2073–2090); singular goal accessor `SearchJobGoal` (model.py:2178).
- SearchState: current, reversed plan, seen, steps remaining, cursor — exact match (model.py:1702–1709).
- Success test: engine.py:1017–1026 — knowledge state ⇒ goal occurs as a fact; otherwise current term equals goal — matches doc L158, L403 ("cursor … not a goal stack").

## 5. Exact proposed planner transitions + SearchJob integration (L418–508)
- Records PlannerProblem/Obligation/Dependency/Job/Variant/Transfer (L427–433); root transition (L437–448); backward decomposition with per-obligation single-goal SearchJobs and dependency edges (L450–465); modified-problem transition with variant + validation job (L482–502); scheduling/preservation preserving "one explicit goal per SearchJob" (L504–508).

## 6. core.py unchanged
- Doc states "No change to `core.py` is required" (L537); all additions placed "outside core.py" (L186, L435). No proposal anywhere to modify core.py.

## 7. Prohibited terms scan (whole document)
- No occurrences: isinstance, hasattr, __class__, standalone type, lists, dicts, python bools, helper functions, globals, "If you want", "matters" (case-insensitive + word-boundary scan).

## Additional spot-checks (all accurate)
- "ArithmeticProgressionLabel is unary; arithmetic pack derives only MiddleTermAverage(object)" — packs/arithmetic.pack.yaml rule `ArithmeticProgression(object) -> MiddleTermAverage(object)`.
- "FirstEdge(Edges(triangle))" selectors — FirstEdgeLabel/EdgesLabel present in geometry, geometry-ontology, trigonometry packs; geometry uses positional/collection terms (EdgesLabel, SideLengthsLabel), not Segment/binary Length.
- "Tao packs simulate strategy with labels such as EvaluateProblem, AlgebraicApproach, Solved" — geometry.pack.yaml L619/634 (EvaluateProblemLabel), L646/1023 (AlgebraicApproachLabel), SolvedLabel throughout; trigonometry.pack.yaml L45+ (SolvedLabel).
