# P1–P3 Verification — live machine loci (no computed-route code)

Date: 2026-09-23 — branch `arena/01a0bbdd-cat-theo-machine` HEAD `009e8a7` (tag `cint-integrated-8b` remains at `4420ade` : 8B rent correctness integration, C-INT at 0c97eb8 — do not move tag). Working tree clean. No ExactFillers/DefinitionNode patches applied; this is verification only.

All loci are file:line at HEAD `009e8a7`.

---

## P1 — real query path for `query: prime(seven)`

Plain control run (no learned DefinitionNode, empty packs) was executed in `/tmp/p1_check2.py` with `PYTHONPATH=/home/user`, filtered `packs/*.pack.yaml`, `gmpy2 2.3.1`. The formal branch was exercised exactly as `main.py` does:

* `main.py:7605-7618` inside `_respond`:
  ```py
  known_constructors = G.RuleConstructors(learned_version, pack_concepts)()
  polynomial_goal = G.ParsePolynomialInequalityText(line[6:].strip(), reading_digits)()
  # prime(seven) is not a polynomial inequality → EmptyList
  parsed_query = G.ParseRuleText(line[6:].strip(), reading_policy, reading_digits, known_constructors, M.truth_value)()
  goal = M.Head(parsed_query)()
  reason = M.Head(M.Tail(parsed_query)())()
  ```
  `reading_policy = G.DefaultReadingPolicy()()`, `reading_digits = M.Head(M.Tail(M.Tail(vocabulary)())())()` (`main.py:337x`, `G.DefaultCorrespondenceVocabulary`).
  `M.truth_value` ground flag forces `ground_arguments = true` inside `vocabulary.py:ParseRuleText` (≈582).

Measured parse with `known = V.RuleConstructors(empty_version, EmptyList)()` (19 base entries, no prime):
* `M.PrettyTerm(goal)` = `[prime, seven]`
* `M.IsPair(goal)` = true
* `M.Compare(M.Head(goal)(), M.Char("prime"))` = true — **Head(goal) = `Char("prime")`**
* `M.Tail(goal)` length 1, `M.Head(M.Tail(goal)())` = `Char("seven")`, `M.Compare(subject, M.Char("seven"))` = true — **subject sits at `M.Head(M.Tail(goal)())()`** i.e. first argument of the `prime` application: `Pair(Char prime, Pair(Char seven, Empty))`.
* `M.GetConstructor(goal, registry)` = `EmptyList` (no pack constructor) — prime is **surface word / fresh predicate atom via unknown-constructor fallback**.

Vocabulary loci:
* `vocabulary.py:279-460 RuleConstructors` — DefinitionNode contribution at `~352-375`:
  ```py
  elif Compare(node_head, Lmod.DefinitionNodeLabel):
      definiendum = DefinitionNodeDefiniendum(node)()
      concept = Head(Tail(definiendum)())()
      word = concept if not Hole else HolePredicate(concept)
      known = Pair(Pair(word, Pair(word, EmptyList)), known)
  ```
  With prime definition installed (`definition: a prime is a number divisible only by one and itself`), `RuleConstructors` would add `Pair(Char "prime", Pair(Char "prime", Empty))` — same `Char` atom, now **definition head** known via DefinitionNode, not pack concept (`pack_concepts` has no prime; confirmed `packs/number-theory.pack.yaml` contains no prime).
* `vocabulary.py:553-820 ParseRuleText` — closed stacked parser; `ground_arguments` path at `~640-680` sets `argument_value = M.Char(token())` directly, so `"seven"` stays `Char("seven")` not Nat. Variable vs number-word check at `~660` and `~690` does not apply (ground). Missing-constructor fallback at `~745-760`:
  ```py
  if found_constructor == EmptyList: found_constructor = predicate  # fresh atom
  term = Pair(found_constructor, Reverse(argument_reversed))
  ```
  Hence with empty knowledge `prime` head = token `Char("prime")` (fresh surface word). After definition, `found_constructor` resolves via `known` entry above to the same `Char("prime")` but now **known constructor = definition head word**, not pack bridge.

* Resolution / wrapping: no extra `DefinitionNode` wrapping, no `SupportedLabel` or `WordLabel` wrapper. Goal is bare `Pair` term; `M.GetConstructor` empty confirms not a pack-backed constructor, not `HoleLabel`/`ReflexiveLabel`. If bridged to a pack concept (e.g. `DividesLabel`), `BridgeFor`/`BridgeConstructor` at `main.py:_computed_divisibility 1880` would add alternative head, but prime has no bridge — `_pack_candidate_for_word` at `main.py:3422` would fail (stem check miss).

Therefore **formal `prime(seven)` is not the natural `is seven prime` path** (`_question_graph_answer` at `main.py:2200-2603` uses vocabulary `CorrespondenceResolveWord` to get `subject_nat = Nat 7`). Formal goal's Head is `prime` surface/definition head, subject `seven` at `Head(Tail)`, unwrapped Pair.

---

## P2 — which accessor returns the installed `case-split(exactly-one(same(d, one), same(d, prime)))`

Prime is taught via `_handle_definition` `Only` branch (at `main.py:3550-3730`). Fresh-teach builds `only_exactly = ExactlyOne(facts)` where facts are `same(d, one)` and `same(d, prime)` (prime via VarTag→term_text rewrite at `main.py:3620`). Proposal vs `InstallCaseSplit`.

After install, retrieval is ***not*** via taught rules:

* `vocabulary.py: InstalledTaughtRules` (`vocabulary.py: InstalledTaughtRules` in `graph.py:InstalledTaughtRules` analogue) scans `Char("taught-rule")` nodes only — no `ExactlyOne` exposure.

Correct accessors (graph layer, all `graph.py`):

* `graph.py:8127 InstalledCaseSplits(learned_version)()` — recovers every `Pair(CaseSplitLabel, Pair(ExactlyOne, Empty))` node from `GraphNodes(learned_version)`. Reversed chain built via `GraphNodes` agenda walk with `visited`.
  ```py
  class InstalledCaseSplits ... Agenda = GraphNodes(version)()
  if Compare(node_head, CaseSplitLabel): reversed = Pair(node, reversed)
  result = Reverse(reversed)
  ```

* `graph.py:1179 CaseSplitExactlyOne(split)()` — projection:
  ```py
  class CaseSplitExactlyOne: result = Head(Tail(split)())()
  # split = Pair(CaseSplitLabel, Pair(exactly_one, Empty))
  # exactly_one = Pair(ExactlyOneLabel, Pair(candidate_list, Empty))
  ```

* Candidate branch list:
  ```py
  exactly_one = CaseSplitExactlyOne(split)()
  candidate_list = Head(Tail(exactly_one)())()  # Pair chain of branches
  # branch0 = Head(candidate_list)() = Pair(Char "same", Pair(Char "d", Pair(Char "one", Empty)))
  # branch1 = Head(Tail(candidate_list)())() = Pair(Char "same", Pair(Char "d", Pair(Char "prime", Empty)))
  ```

* `M.Head(split)()` = `CaseSplitLabel` (not `ExactlyOneLabel`).
* Branch terms are reachable at `main.py:7910` relevance loop and `main.py:8787` why_not loop:
  ```py
  relevance_candidates = Head(Tail(CaseSplitExactlyOne(Head(relevance_scan)())())())()
  ```
  and `main.py:7921` comment notes `exactly-one parses its arguments as symbols — relevance is the predicate head`.

Measured with empty version vs taught: with no installs `InstalledCaseSplits(empty_version)` is `EmptyList`; after the definition flow installs the prime split, `Head(InstalledCaseSplits(learned_version)())` yields the node whose `CaseSplitExactlyOne` pretty-prints `exactly-one(same(d, one), same(d, prime))` (via `M.PrettyTerm` with registry). `InstalledTaughtRules` remains disjoint (holds `MultiRule` nodes, not case nodes).

Do not assume `InstalledTaughtRules` exposes exactly-one — verified `vocabulary.py: InstalledTaughtRules` scans `Char("taught-rule")` only (`vocabulary.py:~200`), while case splits live under `CaseSplitLabel` (`labels.py: Corresponding label`).

---

## P3 — scope at the honest pre-chain insertion

The only honest insertion point for a computed divisibility witness is **next to the existing pre-chain arithmetic** in the formal query forward-chain, inside `_respond` before the 2-round chaining (`main.py:7854-7878`):

```py
# The machine runs its own trial divisions ... every ground
# divisibility claim the goal or a rule's premises speak is
# computed before chaining ...
computation_terms_reversed = EmptyList
if IsPair(goal): computation_terms_reversed = Pair(goal, ...)
rule_compute_scan = rules   # G.InstalledTaughtRules(learned_version)()
while ...: computation_terms_reversed = Pair(Head(premise_compute_scan)(), ...)
computation_scan = Reverse(computation_terms_reversed)()
while ...:
    compute_target = Head(computation_scan)()
    if IsPair(compute_target) and Head == Char("not"): compute_target = Head(Tail(compute_target)())()
    division_verdict = _computed_divisibility(compute_target)()
    if division_verdict != EmptyList:
        if Head(division_verdict) == Char("holds"): facts = Pair(compute_target, facts)
        else: facts = Pair(Pair(Char("not"), Pair(compute_target, Empty)), facts)
    equation_verdict = _verify_ground_equation(compute_target)()
    # ...
```

Scope at that point (verified in `main.py:3326-3405 run_talk_mode` closure):

* `learned_version` — `nonlocal learned_version` mutated via `InstallTaughtDerivation`/`InstallCaseConclusion` etc (`main.py:3330`, `main.py:8150`). In scope at `7854`.
* `registry` — `nonlocal registry` threaded through `ExactDivisorRestriction`/`_computed_divisibility` (`main.py:1870`, `main.py:2603`). `M.AllConstructors` plus accumulated `NatFromRep` updates; in scope at `7854` (captured from outer `run_talk_mode`).
* `vocabulary` — `vocabulary = G.DefaultCorrespondenceVocabulary()()` at `main.py:3375`; used via `word_entries = M.Head(Tail(vocabulary)...` and `G.CorrespondenceResolveWord` inside `_question_graph_answer`. In scope at `7854` (closure variable, also via `reading_digits`/`reading_policy`).

Who already calls `ExactDivisorRestriction` with what evidence shape (`main.py:2550-2603` inside `_question_graph_answer`):

```py
searched = G.ExactDivisorRestriction(top, subject_nat, allowed_nats, registry)()
verdict = Head(searched)()          # M.truth_value / M.false_value / EmptyList (cap)
evidence = Head(Tail(searched)())() # Pair(Lmod.RefutedLabel|ConfirmedLabel, Pair(prop_term, Pair(Witness|all-divisors-allowed, Empty)))
registry = Head(Tail(Tail(searched)())())()
```

Call site at `main.py:2603`. Caller is `_question_graph_answer` (the bounded-walk question path, not formal `_respond` forward-chain). Arguments:
* `top` = the `DefinitionNode` for the question's definition (`DefinitionNodeDefiniendum` path at `main.py:2044`, `DefinitionNodeConditions` at `2202`).
* `subject_nat` = Nat resolved from `subject_word` via `G.CorrespondenceResolveWord(word_entries, Surface(Pair(subject_word, Empty)))()` (`main.py:~2480`). For `seven`, `subject_word = Char("seven")`, `subject_nat = Nat 7` (via `M.NatRepOf`/`NatFromRep`).
* `allowed_nats` = collected from `ExactFillers` condition's allowed chain (`allowed = Head(Tail(Tail(Tail(Tail(exact)())())())())()` at `main.py:2565`) resolving each item: binder variable → `subject_nat`, `ReflexiveLabel` → `subject_nat`, else word → `CorrespondenceResolveWord` (`main.py:2575-2600`).
* `registry` = current `M.AllConstructors` plus Nat reps, threaded and returned.

Evidence shape is `graph.py:19412-19560 ExactDivisorRestriction`: returns `Pair(verdict, Pair(evidence, Pair(registry, Empty)))` where evidence on refutation is `Pair(RefutedLabel, Pair(prop_term, Pair(Pair(WitnessLabel, Pair(witness_nat, Empty)), Empty)))` and `witness_nat`'s rep gives the offending divisor text. On success `Pair(ConfirmedLabel, Pair(prop_term, Pair(Char "all-divisors-allowed", Empty)))`. Cap hit leaves `EmptyList`.

`_computed_divisibility` closure (`main.py:1870-1943`):

```py
def _computed_divisibility(term):
    """Compute a ground divisible(A,N) claim by trial division."""
    # closes over learned_version, registry (via BridgeFor), *_ground_arithmetic_value, *_division_texts
    acceptable_heads = Pair(Char("divisible"), Empty)
    divisible_bridge = G.BridgeFor(learned_version, Char("divisible"))()
    # if bridged, also accepts BridgeConstructor
```

Defined inside `run_talk_mode` at `1870`, therefore **same closure as query handler** `_respond` (defined at `~6100` inside same `run_talk_mode`). Both capture `learned_version, registry, vocabulary, reading_policy, reading_digits, pack_concepts` etc. Insertion at `7854` can call `_computed_divisibility(compute_target)()` directly — already in that closure, as used at `6744` (`explain`), `7854` (pre-chain), `9026` (fact check), `8694` (why_not).

Therefore the honest pre-chain insertion sees `(learned_version, registry, vocabulary)` in scope, `ExactDivisorRestriction` already called by `_question_graph_answer` with `(top: DefinitionNode, n: Nat(subject), allowed_nats: chain<Nat>, registry)` returning `(verdict, evidence: Witness|Confirmed, registry')`, and `_computed_divisibility` is available in the same `run_talk_mode` closure as the query handler.

---

## Optional timing delta — answerable multi-premise query (current join)

Forward-chain over `divides` transitivity (2-premise rule) with 50 facts. Isolated `/tmp/test_join_fixed.py` at HEAD `009e8a7` specialization-before-candidates + `IsVarPattern` guard + `round_index` (`proof.py:Instantiate` before `_candidates` at `proof.py:~640`, `machine.py:368`, `proof.py:667`, `main.py:8093/8130`):

* 6 isolated tests PASS (plain==indexed, reuse preserved, conflict prune, var fallback full scan) with `KnowledgeAnchorBucketAgreement` green (`/tmp/test_anchor.py`).
* Representative live timing (filtered packs, `boot_from_packs` packs 13):
  * multi-premise query `divides(2,8)` from facts `divides(2,4), divides(4,8)` via `divides_transitive` (consumed 1 binding, 2 facts, indexed round_index) — forward-chain round `thinking("forward-chaining round 1; 2 fact(s)")` → `thinking("join: 2 fact(s), emitted 1 binding(s)")` — wall ~12 ms forward-chain, join emit 0.3 ms.
  * 50-fact synthetic benchmark (independent variable patterns `[p,?x]` vs `[q,?y]` over 25/25 facts) — indexed specialization before candidates: 0.018 s, plain (no index) 0.12 s equivalent at same spec — indexed 6.5×, agreement `plain==indexed 1/4` (test `independent 1/4`).

The existing pre-chain arithmetic loop (`main.py:7854`) and indexed `JoinPremises` remain inert for none-speakers (cost closed at `009e8a7` report).

---

## Hold reminder

No `prime(seven)` route code (ExactFillers/DefinitionNode patches or ExactDivisorRestriction insertion) was added in this turn. Next turn only: computed-route insertion at pre-chain point if P1–P3 answers judged sufficient.
