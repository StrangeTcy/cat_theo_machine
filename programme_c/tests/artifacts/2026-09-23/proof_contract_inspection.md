# Proof-contract inspection — can the installed split + ExactDivisorRestriction produce a checker-replayable derivation of `prime(seven)`?

Date: 2026-09-23 — HEAD `d23dfce` (prior `3b28f60`), tag `cint-integrated-8b` at `4420ade` (not moved). HOLD, no fact injection, no install-path change. Report-only.

Question: *Can the installed definition and case split, together with `ExactDivisorRestriction`, produce a checker-replayable derivation of the exact parsed goal `Pair(Char("prime"), Pair(Char("seven"), Empty))`?*

Answer: **Unresolved** — no checked obstruction yet, but no positive checker path either. The four contracts below show why a divisor-walk success alone is insufficient and what is missing for `why` to replay.

---

## 1. Persisted link from split to owning definition and binder

**None survives as a traversable edge.**

Loci:

* `graph.py:1150 CaseSplit` stores `Pair(Char("case-split"), Pair(exactly_one, Empty))` only. `CaseSplitExactlyOne` at `1179` is `Head(Tail(split)())`. No definiendum, no binder, no term word.
* `graph.py:8127 InstalledCaseSplits` walks `GraphNodes(learned_version)()` and collects nodes where `Head(node)==Char("case-split")`. The walk expands `ChainHasTerm`-visited shared subterms but never follows a definition edge.
* `graph.py:8157 InstallCaseSplit` splices both `split` and `exactly_one` into `GraphNodes`:
  ```py
  next_version = GraphVersion(Pair(split, Pair(exactly_one, GraphNodes(...))), GraphEdges(...), Invariants(...))
  ```
  Idempotent on `Compare(node, split)==truth`. No definition, no `OnlyLabel`, no binder variable is spliced.
* Origin carrying `term_word` exists only transiently in the proposal path `main.py:3685-3705`:
  ```py
  only_origin = Pair(Char("case-split"), Pair(only_exactly, Pair(term_word, Empty)))
  only_proposal = Proposal(only_split, only_origin)
  proposal_store = ProposalStoreSubmit(proposal_store, only_proposal)
  ```
  `ProposalOrigin` (`1031`) and `ProposalStore` (`2039`) hold that pair, but `InstalledCaseSplits` does **not** read the proposal store. After `InstallCaseSplit` + `ProposalStoreApproved`→`InstallCaseSplit` daemons, the approved split node in the graph has no edge to the proposal or to the definition. `GraphNodes` after approval contains both the `DefinitionNode` chain element and the `CaseSplit` node as disjoint splices.

* `graph.py:20005 DefinitionNode` is `Pair(DefinitionNodeLabel, Pair(definiendum, Pair(binder, Pair(conditions, Empty))))`. `DefinitionNodeDefiniendum` (`20038`), `DefinitionNodeBinder` (`20047`), `DefinitionNodeConditions` (`20056`) are the only traversals. Census at review: `DefinitionNodeLabel: 0`, `ExactFillersLabel: 0`. At `d23dfce` the only installed prime restriction observed via `InstalledCaseSplits` is the `case-split` over `same(d, one)/same(d, prime)`; no `DefinitionNode` with `ExactFillers` is installed, so there is nothing to link *to*, even if the split stored it.

* Dynamic check (no persistence to follow): `C0-1` showed `VarTag` → `term_text` erasure at `main.py:3632-3644`. The installed branches are `Char("one")` and `Char("prime")`; the `self_variable = Pair(VarTag, Pair(Char("?self"), Empty))` created at `graph.py:InterpretDefinitionBody` (`~20100`) never appears in the split.

**Conclusion for Q1:** Do not reconstruct ownership from matching display words. There is **no persisted `split → DefinitionNode` edge and no binder surviving in the split**. Any Route A selection must remain a heuristic (`filler == Head(goal)`) unless a new edge is installed (which this inspection forbids). This is the obstruction to “certified split-to-goal association” noted in the prior review.

---

## 2. Direction of the installed implication

**Neither direction is installed as a checked rule; the split is an `ExactlyOne` assertion about `same(d, …)`, not about `prime`.**

Loci:

* The prime definition path at `main.py:2062 _definition_graph_answer` installs a `DefinitionNode` with `holed_conditions` built via `PredicateHoles` (`~2205`) and `DefinitionNode(Definiendum, Binder, holed_conditions)`. For the body `a number divisible only by one and itself`, `InterpretDefinitionBody` (`graph.py:~20180`) creates conditions that include an `OnlyLabel` segment whose items become `ExactFillers` in the *interpreted* condition chain (via `graph.py:InterpretOperators`). The *case-split* path at `main.py:3555-3715 _propose_restriction_from_conditions` re-derives that `Only` segment as `same(d, one), same(d, prime)` and proposes the split, but **no `Rule`/`Law` is compiled linking `prime(x)` to the divisor check**.

* `graph.py:21591 InstallDefinitionLaws` and `graph.py:21683 InstallDefinition` are the only places definitions become laws. `InstallDefinitionLaws` is invoked at `main.py:3158, 4113, 4194, 5282` for process/definition compilation, but the prime text’s operator path gates on the case-split proposal, not on law compilation. No `MultiRule` with `P.RulePremises` containing `prime` and `P.RuleReplacement` containing `same` (or converse) is installed for prime at this HEAD.

* `CaseSplit` semantics `graph.py:1359 CaseSplitQuery` are `facts, rules, splits, goal → (status, kind, conclusion, …)`. The verdicts are `all-branches-refuted`, `multiple-consistent-cases`, `consistent-case-does-not-prove-goal`, `truth` with `InstallCaseConclusion`. The query evaluates `goal` across *branches* where branches are assumptions `same(d, one)` vs `same(d, prime)`. For `goal = prime(seven)`, `CaseSplitQuery` at `main.py:7902` relevance selects only splits whose branch predicate head equals `Head(goal)` (`prime`). Since branch heads are `same`, `case_relevant` stays `false`, so `CaseSplitQuery` is never invoked with the prime split for `prime(seven)`. The installed implication in the store is therefore **not `prime(x) ↔ divisor-restriction(x)` in either direction** as a `LawInterface`-checkable law.

* The only checked implications for prime-like behavior would be via `G.InstalledTaughtRules` (`vocabulary.py: RuleConstructors`-adjacent) — none.

**Conclusion for Q2:** The split alone does not establish “restriction ⇒ prime” (sufficiency) nor “prime ⇒ restriction” (necessity) as a `Proof`-checked rule. `ExactDivisorRestriction`’s walk being positive does not logically become `prime(seven)` without a separate sufficiency rule that has not been shown to exist or to be checked.

---

## 3. Precise contract of `ExactDivisorRestriction`

**Locus:** `graph.py:19412 ExactDivisorRestriction(M.Edge)` — docstring and body at `19412-19560`.

```
Inputs:  (prop_term, n:Nat, allowed_nats:chain<Nat>, registry)
Output:  Pair(verdict, Pair(evidence, Pair(registry', Empty)))
  verdict = truth_value | false_value | EmptyList
  evidence on verdict==false_value: Pair(RefutedLabel, Pair(prop_term, Pair(Pair(WitnessLabel, Pair(witness_nat, Empty)), Empty)))
  evidence on verdict==truth_value: Pair(ConfirmedLabel, Pair(prop_term, Pair(Char("all-divisors-allowed"), Empty)))
  EmptyList = cap reached or n has no Nat rep ("not knowing is not no")
```

Contract:

* **Positive (`truth_value`):** Walk `d = 1..n` incrementing `d_text = GMPSuccText(d_text)()`. For each `d`, decide `d divides n` via monotone multiple-walk (`multiple_text = d_text; stepping adds d_text until `GMPEqualText(multiple_text, n_text)` or `GMPLessText`). If divides and `d_text` not in `allowed_texts` (`allowed_nats` converted via `NatRepOf → GMPRepText`), set `counterexample_text = d_text` and stop. After loop, if `counterexample_text == ""` and `GMPLessText(n_text, d_text)==truth` (i.e., walked past `n`), then `complete = truth` and `verdict = truth` with `ConfirmedLabel`. Establishes: **every divisor of `n` is among `allowed_nats`**. It does *not* establish prime in any other sense; it is an allowed-set membership check.

* **Negative (`false_value`):** Same walk finds first divisor outside allowed. `witness_nat` is `NatFromRep(GMPRep(counterexample_text))`, `evidence` carries `RefutedLabel` + `WitnessLabel(witness_nat)`. Establishes: **there exists a divisor of `n` not allowed**, with witness Nat as evidence.

* **Budget-limited (`EmptyList`):** If `n_rep == EmptyList` (no Nat rep for `n`), or `GMPEqualText(d_text, cap_text)==truth` before completing (`cap_text = GMPRepText(WITNESS_SEARCH_CAP)()`), then neither `counterexample_text` nor `complete` triggers and `verdict` stays `EmptyList`. Section at `19480-19495`:
  ```py
  if GMPEqualText(d_text, cap_text)==truth: pass  # stop walking
  ```
  The caller at `main.py:2585-2615` treats this as `"The search hit its cap before deciding; I do not know."` — not `false`. No evidence is produced.

* **Boundary `n=1`:** `n_text="1"`, `allowed_texts` from `[one→Nat 1, prime(reflexive)→Nat 1]` is `["1", "1"]` (duplicate allowed). Walk: `d=1`, `multiple_text="1"`, `GMPEqualText("1","1")==truth` ⇒ `divides=truth`, `allowed_here` probe finds `Char("1")==Char("1")` ⇒ `truth`, so `counterexample_text` stays `""`, `d_text` becomes `"2"`, next iteration `GMPLessText("1","2")==truth` ⇒ `complete=truth`, `verdict=truth` with `Confirmed`. **Thus `ExactDivisorRestriction` reports positive for `n=1` under `allowed={1,n}`**, even though `1` is not prime (`NatLess(one, n)` fails, but `ExactDivisorRestriction` does not check it). The separate sieve `graph.py:19650 TrialSieveMembership` correctly handles this as `boundary-below-two` with `false_value`, but `ExactDivisorRestriction` is not that gate. This matches docstring “Walks d = 1..n” without a distinctness or size check.

* **Consequence for prime use:** A positive verdict on its own does not establish “therefore prime” unless an additional checked condition (e.g., `NatLess(one, n)` and `|allowed|==2` with distinctness) is conjoined. The current `ExactDivisorRestriction` alone is **insufficient for sufficiency**.

---

## 4. Existing path by which a computed result + evidence becomes a recorded derivation that `why` can replay

**No existing path turns an `ExactDivisorRestriction` positive/negative verdict into an `InstalledTaughtDerivations` or `InstalledCaseConclusions` entry that `why prime(seven)` replays.**

Loci:

* `why` entry at `main.py:11080-11145`:
  ```py
  parsed_why = ParseRuleText(line[4:], reading_policy, reading_digits, known_constructors, truth_value)()
  why_target = Head(parsed_why)()
  why_conclusions = InstalledCaseConclusions(learned_version)()  # graph.py:InstalledCaseConclusions  (char "case-conclusion")
  # scan for CaseConclusionCandidate == why_target → "case conclusion: ... was established by the only consistent branch of ..."
  why_derivations = InstalledTaughtDerivations(learned_version)()  # vocabulary.py:InstalledTaughtDerivations (char "taught-derivation")
  # scan for DerivationDerived == why_target → DerivationTree(why_derivation, learned_version, "0") → DerivationTreeText
  ```
  There is no branch scanning `ExactDivisorRestriction` evidence or `ConfirmedLabel`/`RefutedLabel` witnesses. The only replayable provenance types are `taught-derivation` nodes (`vocabulary.py: TaughtDerivation → Pair(Char("taught-derivation"), Pair(derived, Pair(rule, Pair(premises, Empty))))`) and `case-conclusion` nodes (`graph.py: CaseConclusion`). Both are written only via `InstallTaughtDerivation` (`vocabulary.py: InstallTaughtDerivation` at `vocabulary.py:~80`) and `InstallCaseConclusion` (`graph.py: InstallCaseConclusion`), invoked respectively at `main.py:8140` inside forward-chain and at `main.py:8095`/`~8096` inside `CaseSplitQuery` success.

* Forward-chain computed facts precedent at `main.py:7854-7880` (`_computed_divisibility`/`_verify_ground_equation`) does **not** install:
  ```py
  division_verdict = _computed_divisibility(compute_target)()  # 7854
  if verdict != EmptyList:
      if Head(verdict)==Char("holds"): facts = Pair(compute_target, facts)
      else: facts = Pair(Pair(Char("not"), Pair(compute_target, Empty)), facts)
  ```
  `facts` here is the local `Pair` chain for this `query:` call, not `learned_version`’s `GraphNodes`. No `InstallTaughtDerivation` follows. The same for `equation_verdict`. So a query-local prepend is **not persisted** and `why` after the query will not find it.

* `_question_graph_answer` path at `main.py:2603-2625` (the natural “is seven prime?” path that *does* call `ExactDivisorRestriction`) returns a string directly:
  ```py
  searched = G.ExactDivisorRestriction(top, subject_nat, allowed_nats, registry)()
  if verdict==truth: return "Yes: every divisor of " + subject_word + " is among the allowed ones."
  if verdict==false: return "No: " + GMPRepText(witness_rep) + " divides " + subject_word + " ..."
  ```
  No `GraphVersion` is returned with a new `taught-derivation`; `registry`’ is threaded but `learned_version` is unchanged. `why` for that natural question would fall through to the same “no recorded derivation” case.

* Forward-chain new facts at `main.py:8140-8155` *do* install, but only for rule-fired derivations:
  ```py
  taught_derivation = G.TaughtDerivation(derived, taught_rule, instantiated_premises)()
  learned_version = G.InstallTaughtDerivation(learned_version, taught_derivation)()
  facts = Pair(derived, facts); growing = truth
  ```
  There is no analogous `InstallPrimeWitnessDerivation` for a `ConfirmedLabel` evidence. Hence even if Route A did `facts = Pair(goal, facts)` locally, without an explicit `InstallTaughtDerivation` or `InstallCaseConclusion`, the very next `why` call (new `_respond` activation) scans `learned_version` and misses.

**Conclusion for Q4:** Do not prepend the goal. There is **no checked `computed→recorded-derivation` path for `ExactDivisorRestriction` witnesses**. Any Route A that wants `why` to replay must create one, and that new path itself needs a contract (what rule, what premises, what evidence is stored, and how the checker revalidates it). That is a non-trivial install-path change, contrary to “Route A reuses verified P2 accessors only.”

---

## Grading

Grade passes only if the **checker derives the declared goal** (`Compare(DerivationDerived(why_derivation), goal)==truth` or `Compare(CaseConclusionCandidate(why_conclusion), goal)==truth`), not if the divisor walk alone succeeds.

* **Subject `1` (boundary):** With `allowed_nats=[Nat 1, Nat 1]` (reflexive collapses), `ExactDivisorRestriction` verdict = `truth_value` (`Confirmed, all-divisors-allowed`) — walk completes, no divisor outside allowed. **Obstruction:** `1` would be incorrectly prime under allowed-set check alone. Correct prime requires `NatLess(one, n)` (as in `TrialSieveMembership` `boundary-below-two` at `~19700`), which `ExactDivisorRestriction` does not check. So even a positive walk is not sufficiency. Grade: if Route A relied on `ExactDivisorRestriction` positive ⇒ would misclassify `1`. This is a checked obstruction, not merely “unknown.”

* **Small valid subjects `2`, `3`, `7`:** Walk enumerates `d=1..n`. Divisors are `{1, n}` only, both in `allowed_texts` (`"1"` and `GMPRepText(NatRepOf(n))`). No counterexample ⇒ `truth_value`. For `n=7`, `d_text` walk is `1,2,3,4,5,6,7,8` with divides checks at each `d` via multiple-walk; all non-divisors (`2..6` excluding `7`) are ignored because `divides==false`. Positive result is *walk-correct* but, per Q4, not yet a replayable derivation. Grade: walk positive, checker derivation **absent** ⇒ result **unresolved**, not positive.

* **Composite subjects `4`, `9`, `25`:** Example `n=4, allowed=[1,4]`. Walk: `d=1` divides+allowed, `d=2` divides (`2*2==4`) via `multiple_text` loop, `allowed_probe` for `"2"` misses (`["1","4"]`) ⇒ `counterexample_text="2"`, `verdict=false_value`, `evidence=Pair(Refuted, Pair(top, Pair(Witness(Nat 2), Empty)))`. **Correct negative** with witness. However again witness is not installed as a `taught-derivation`; `why prime(four)` would not replay the witness unless Route A installs it. Grade: walk negative is correct, but checker replay for `prime(four)` itself is not defined (prime is false, but there is no `not(prime(four))` derivation installed either). Negative answer needs its own checked obstruction; none exists in the store.

* **Unrelated definition with similar split:** Suppose another term `lonely` defined with `only by one and two` → split `same(d, one), same(d, two)`. Filler-equality heuristic `filler==Head(goal)` where `goal=prime(seven)` yields `filler "prime" != "one","two"` ⇒ no split selected. If goal were `lonely(seven)`, filler `"lonely"` also mismatches, so the split would not be selected either. This demonstrates the fragility: the heuristic happens to select the prime split only because filler text equals definiendum word, not because of a persisted ownership edge. An unrelated split with filler `"prime"` (unlikely but possible) would be spuriously selected. Grade: association remains **unverified heuristic**, not certified.

* **Budget-limited run:** With `WITNESS_SEARCH_CAP` (default text at `graph.py:19470` via `G.WITNESS_SEARCH_CAP`, textual value not printed here but inspected as large; synthetic small-cap test would set `cap_text="5"` via monkey patch), walk for `n=7` with `cap="5"` stops at `d=5` with `GMPEqualText("5", cap)==truth` → `pass` (no complete), `verdict` stays `EmptyList`. Caller at `main.py:2585` returns `"The search hit its cap before deciding; I do not know."` — **budget-limited contract holds** (`EmptyList` ≠ `false`). No false negative. However again no derivation is installed. Grade: unresolved, correctly handled as “don’t know,” but not a positive derivation.

**Overall grading:** No case yields a **positive checker replay** (goal found via `InstalledTaughtDerivations`/`InstalledCaseConclusions` with `Compare(…, goal)==truth`). No case yields a **checked negative obstruction** that `why` can display as a derivation either. Hence per the bounded-item rubric the answer is **unresolved** — the walk is inspectable, the replay is missing.

---

## Separation from indexed-join work

The join-cost work at `009e8a7` (`proof.py:Instantiate before _candidates`, `machine.py:368 FindBinding guard`, `main.py:8093 round_index`) was verified only on **round-start facts**. Bucket agreement (`KnowledgeAnchorBucketAgreement` via `_candidates` vs plain) does **not** settle same-round prepend visibility.

Locus for required differential test before any live rerun:

* `main.py:8093` `round_index = K.KnowledgeHeadIndexInsertChain(M.EmptyTree, facts, registry)()` — built once per round from `facts` as it stood at round entry.
* `main.py:8145` inside `while bindings != EmptyList`: `facts = Pair(derived, facts); growing = truth` — new `derived` facts are prepended to the `facts` chain *during* the round, **after** `round_index` was built.
* `main.py:8130` `bindings = P.JoinPremises(P.RulePremises(taught_rule)(), facts, EmptyList, index=round_index, registry=registry)()` consumes `round_index`, not a fresh index over `facts` after prepend.

Whether a second `JoinPremises` call *within the same round* (next `taught_rule` iteration at `8130` next `remaining_rules` cycle) sees the just-prepended fact depends on whether `round_index` is rebuilt or the new fact happens to share the old bucket. The “6 isolated tests PASS” and `KnowledgeAnchorBucketAgreement` green were over static `facts` snapshots, not over this intra-round mutation. A differential test must: (a) build `round_index` from `facts@round_start`, (b) prepend `prime(seven)` (or any computed divisor witness) to `facts`, (c) run `JoinPremises` for a rule whose second premise needs that new fact, once with the stale `round_index` and once with a fresh index built from `facts@after_prepend`, and compare `Compare(emitted bindings)==truth` and `Compare(DerivationDerived,…)==truth`. Without that test, a Route A that prepends then continues the same round risks silently missing its own just-added evidence.

This bucket-same-round question is independent of the proof-contract grading above and must be settled before a live `learned_version` rerun is claimed.

---

## Standing

Prime route remains **HOLD**. No new fact injection (`facts = Pair(goal, …)`), no `InstallDefinition`/`InstallCaseSplit` change, no tag movement (`cint-integrated-8b` at `4420ade`). Next step is a Route A specification only if the four contracts above are satisfied with a checked `computed→recorded` derivation path; otherwise the next bounded item should address that path explicitly, separately from join indexing.

