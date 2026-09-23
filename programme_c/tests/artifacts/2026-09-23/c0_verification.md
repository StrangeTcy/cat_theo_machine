# C0 Prerequisites — Route A (case-split-derived allowed_nats) verification

Date: 2026-09-23 — branch `arena/01a0bbdd-cat-theo-machine` HEAD `3b28f60` (+ this doc). Tag `cint-integrated-8b` at `4420ade` (8B rent) — not moved.Verification only, no route code. All loci at HEAD `3b28f60`.

---

## C0-1 — reflexive branch identification

**Question:** Given `candidate_list` = `exactly-one(same(d, one), same(d, prime))`, how does a route know `prime` is the reflexive (resolve to subject) and `one` is literal (resolve to Nat 1)?

**Answer: recoverable only by comparing filler against `Head(goal)`, not from any stored `ReflexiveLabel` marker. The `VarTag` is lost at install time.**

Loci:

* Fresh-teach `_propose_restriction_from_conditions` `main.py:3555-3715` rebuilds the split from the parsed `OnlyLabel` segment. At `main.py:3632-3644`:
  ```py
  part = Head(inner_scan)()
  if IsPair(part) and Compare(Head(part)(), VarTag)==truth:
      part_text = term_text   # term_text = "prime" (the definiendum word)
  else:
      if SurfaceChainHasWord(DEFINITION_STOP_WORDS, part)==false:
          part_text = str(part())
  ```
  For prime definition `a prime is a number divisible only by one and itself`, `items = [["one"], ["itself"]]` (where `itself` is `Pair(VarTag, Pair(Char("?self"), Empty))` after `ResolveReflexives` in `graph.py:20180`). The second item hits the `VarTag` branch and `part_text` becomes `term_text` = `"prime"`. Hence `branch_texts_reversed` = `["same(d, one)", "same(d, prime)"]` at `main.py:3658`, then parsed at `main.py:3672-3675`:
  ```py
  parsed_only = G.ParseRuleText(only_split_body, reading_policy, reading_digits, known_constructors, Char("exactly-one"))()
  only_split = Head(parsed_only)()
  only_exactly = CaseSplitExactlyOne(only_split)()
  ```
  The installed node is `Pair(CaseSplitLabel, Pair(Pair(ExactlyOneLabel, Pair(candidate_list, Empty)), Empty))` where `candidate_list = [ same(d, one), same(d, prime) ]`. Both fillers are bare `Char` atoms (`Char("one")`, `Char("prime")`). No `ReflexiveLabel` is stored. Live check: `G.CorrespondenceResolveWord(word_entries, Surface(Pair(item, Empty)))` is *not* called for the split; only for `ExactDivisorRestriction`'s `allowed` chain. The `VarTag` provenance is erased by `str(part_text)`.

* Rebuilding via `_propose_restriction_from_conditions` itself also loses it — the same `VarTag → term_text` mapping is used to *rebuild* after a prior install, confirming the stored shape has no VarTag to distinguish.

* `graph.py:20180 ResolveReflexives` does store a binder variable for `DefinitionNode` exact fillers path, but that path has count 0 (no `DefinitionNode`/`ExactFillers` installed, as censused). The case-split path never stores `ReflexiveLabel`.

**Consequence for Route A:** identification must be `filler == Head(goal)`:

```py
goal = Pair(Char("prime"), Pair(Char("seven"), Empty))  # P1
head_prime = Head(goal)()  # Char("prime")
candidate_list = Head(Tail(CaseSplitExactlyOne(split)())())()
branch0 = Head(candidate_list)()                         # same(d, one)   filler_one  = Head(Tail(Tail(branch0)())())()
branch1 = Head(Tail(candidate_list)())()                 # same(d, prime) filler_prime= Head(Tail(Tail(branch1)())())()
# reflexive = (Compare(filler, head_prime)==truth)
```

Live run on synthetic split (built via `ParseRuleText("same(d, one), same(d, prime)", …, Char("exactly-one"))`) confirms: `M.Compare(filler_prime, Char("prime"))==truth`, `M.Compare(filler_one, Char("prime"))==false`, and `M.Compare(filler_one, Char("one"))==truth`. So route checks `filler == Head(goal)` → reflexive (resolve to `subject_nat`), else literal `filler == Char("one")` → `Nat 1` via `NatFromRep(GMPRep("1"))`/`CorrespondenceResolveWord` fallback. The `d` binder variable is irrelevant to filler distinction; `same`'s first arg is always `Char("d")`.

No `ReflexiveLabel` marker is recoverable from the installed split; any code searching for it would miss.

---

## C0-2 — split-to-goal association

**Question:** With multiple installed splits (post-`5b809dd` packs + user definitions), how does a route select the split belonging to `prime`?

**Answer: filler-equality selection over `InstalledCaseSplits`, not predicate-head selection. The existing `7902` predicate-head relevance loop is insufficient for prime.**

Loci:

* `graph.py:8127 InstalledCaseSplits(learned_version)()` returns `Reverse(reversed_splits)` where `reversed_splits` collects every `Pair(CaseSplitLabel, Pair(ExactlyOne, Empty))` found via `GraphNodes` agenda (same walk as `InstalledTaughtRules` but for `CaseSplitLabel`). Number of splits grows with each `ProposalStoreSubmit` for `Only` definitions.

* Existing relevance for forward-chain case elimination at `main.py:7902-7940`:
  ```py
  relevance_candidates = Head(Tail(CaseSplitExactlyOne(Head(relevance_scan)())())())()
  if IsPair(Head(relevance_candidates)()) and Compare(Head(Head(relevance_candidates)())(), Head(goal)())==truth:
      case_relevant = truth
      relevant_splits_reversed = Pair(Head(relevance_scan)(), relevant_splits_reversed)
  ```
  `Head(Head(candidate))` is `Char("same")` for prime's split; `Head(goal)` is `Char("prime")`. Comparison fails → `case_relevant` remains `false`. So prime's split is *not* considered relevant by the current machine, which is consistent with the census gap: the working decider (`ExactDivisorRestriction` at `main.py:2603`) is not this case-query path. Route A cannot reuse `7902` predicate check.

* Origin `term_word` stored at proposal time `main.py:3685-3695`:
  ```py
  only_origin = Pair(Char("case-split"), Pair(only_exactly, Pair(term_word, Empty)))
  only_proposal = Proposal(only_split, only_origin)
  proposal_store = ProposalStoreSubmit(proposal_store, only_proposal)
  ```
  But `InstalledCaseSplits` does **not** persist `term_word` (only the `CaseSplit` node). After install, `GraphNodes` walk yields bare `CaseSplit` nodes; `term_word` is lost unless the proposal store is scanned separately (`G.ProposalStore` etc.). The durable selection must therefore inspect candidates.

* Correct Route A predicate (filler equality, verified live):

```py
splits = G.InstalledCaseSplits(learned_version)()          # graph.py:8127
selected = EmptyList
scan = splits
while scan != EmptyList:
    split = Head(scan)()
    exactly_one = G.CaseSplitExactlyOne(split)()            # graph.py:1179
    candidate_list = Head(Tail(exactly_one)())()
    probe = candidate_list
    found = false_value
    while probe != EmptyList:
        branch = Head(probe)()
        # branch = Pair(Char("same"), Pair(Char("d"), Pair(filler, Empty)))
        filler = Head(Tail(Tail(branch)())())()
        if Compare(filler, Head(goal)())==truth:            # "prime" == "prime"
            found = truth_value
            probe = EmptyList
        else:
            probe = Tail(probe)()
    if found == truth_value:
        selected = split
        scan = EmptyList
    else:
        scan = Tail(scan)()
```

Live verification: with two splits installed (`same(d, one)/same(d, prime)` and synthetic `same(d, two)/same(d, three)`), the scan returns the prime split uniquely; a query `prime(seven)` matches filler `prime`, `is seven even` would match none. This is robust to multiple splits and does not require `term_word` persistence. Alternative predicate `branch_texts contain Head(goal) word via PrettyTerm` is equivalent but more expensive; filler equality is exact.

If proposal-store `term_word` were desired, an additional accessor `InstalledProposalOrigins` would be needed, but filler equality is sufficient and already precedented at `main.py:8787` `why_not` branch where `Head(candidate) == why_not_head` checks head equality; for filler case the analogous check is second-arg equality.

---

## C0-3 — answer shape: prepend fact vs return string

**Question:** Should successful Route A prepend `prime(seven)` to `facts` before chaining (so `8190` goal scan finds it) or return an answer string directly?

**Answer: prepend to `facts` (working set) before the goal scan, mirroring `_computed_divisibility`'s computed-fact join at `main.py:7854`. Returning a string directly breaks provenance consumers at `main.py:11118` and `vocabulary.py:2701`.**

Loci:

* Goal scan after chaining `main.py:8195-8255`:
  ```py
  goal_found = false_value; goal_refuted = false_value
  fact_scan = facts
  while fact_scan != EmptyList:
      candidate_fact = Head(fact_scan)()
      if IsPair(candidate_fact) and Head(candidate_fact)==Char("not") and Head(Tail(candidate_fact)())()==goal: goal_refuted = truth
      goal_matches = Compare(candidate_fact, goal)()
      # SupportedLabel alias handling at 8205-8225
      if goal_matches==truth: goal_found = truth; fact_scan = EmptyList
      else: fact_scan = Tail(fact_scan)()
  last_goal = goal; _persist_talk_state()
  if goal_found==truth: return "yes; derived " + line[6:].strip() + " from the taught facts and approved rules."
  if goal_refuted==truth: return "no; …"
  forward_failure = "no; I could not derive " + line[6:].strip() + ( " within the forward-chaining cap." if chain_capped else ".")
  ```
  This is the *only* path that sets `last_goal`, persists `talk_ledger` via `FiringRecord` at `7635`, and feeds `why` at `main.py:11080`.

* Computed divisibility precedent `main.py:7854-7880` already demonstrates prepend:
  ```py
  division_verdict = _computed_divisibility(compute_target)()
  if division_verdict != EmptyList:
      if Head(division_verdict)==Char("holds"): facts = Pair(compute_target, facts)
      else: facts = Pair(Pair(Char("not"), Pair(compute_target, Empty)), facts)
  ```
  Followed by standard forward-chain and the same `8195` scan. No separate return string is emitted before chaining; the computed polarity *joins* the working set.

* Provenance consumers that require the prepend path:

  - `main.py:11080-11145` `why` for `prime(seven)`:
    ```py
    parsed_why = G.ParseRuleText(line[4:], …, truth_value)()
    why_target = Head(parsed_why)()
    why_conclusions = G.InstalledCaseConclusions(learned_version)()
    # scan for CaseConclusionCandidate == why_target → "case conclusion: … was established by the only consistent branch of …"
    why_derivations = G.InstalledTaughtDerivations(learned_version)()
    # scan for DerivationDerived == why_target → DerivationTree
    if why_derivation != EmptyList: return "because " + G.DerivationTreeText(DerivationTree(why_derivation, learned_version, "0")())()
    ```
    If Route A returns a string directly without `InstallTaughtDerivation`/`InstallCaseConclusion`, `InstalledTaughtDerivations` and `InstalledCaseConclusions` remain empty for `prime(seven)`, so `why prime(seven)` returns `"There is no recorded derivation …"` — provenance lost.

  - `vocabulary.py:2701 DerivationTree` (`graph.py: InstalledTaughtDerivations` walk) depth-bounded at 50, textual rendering via `DerivationTreeText`. Without a stored `TaughtDerivation` node, `DerivationTree` is empty.

  - The `why_not` path at `main.py:8787-8905` also assumes the same split accessor; a direct-return route would have no `CaseSplitQuery` evidence to answer `why not prime(seven)`.

  - Natural-language precedent `_question_graph_answer` at `main.py:2603-2625` *does* return a string directly (`"Yes: every divisor …"` / `"No: 3 divides 9 …"`), but that path is the definition's *question* graph answer, not the formal `query:` forward-chain path. Its answer is not persisted as a `TaughtDerivation` either, but the natural path is not expected to support `why` via `DerivationTree`; the formal path is.

**Recommended Route A shape (preserves provenance, consistent with `7854`):**

```py
# inside _respond, after computation_terms_reversed but before rounds loop
# or immediately before goal_early check at main.py:8105
case_splits = G.InstalledCaseSplits(learned_version)()          # 8127
selected_split = SelectPrimeSplit(case_splits, goal)             # C0-2 filler equality
if selected_split != EmptyList:
    # build allowed_nats as ExactDivisorRestriction does, but from split
    candidate_list = Head(Tail(CaseSplitExactlyOne(selected_split)())())()
    allowed_nats = BuildAllowedNats(candidate_list, Head(goal)(), subject_nat, word_entries, registry)  # C0-1 reflexive → subject_nat, else Nat 1 via NatFromRep
    # reuse existing subject_nat resolution: subject_word = Head(Tail(goal)())(), subject_nat via CorrespondenceResolveWord / NatRepOf
    searched = G.ExactDivisorRestriction(goal, subject_nat, allowed_nats, registry)()  # same edge, same evidence type
    verdict = Head(searched)(); evidence = Head(Tail(searched)())(); registry = Head(Tail(Tail(searched)())())()
    if verdict == truth_value:
        facts = Pair(goal, facts)   # prepend, as _computed_divisibility does
        # optionally persist as TaughtDerivation for why: InstallTaughtDerivation(learned_version, TaughtDerivation(goal, prime_computed_rule, evidence))()
        # or as CaseConclusion: InstallCaseConclusion(...)
        # then let existing 8195 scan find it and return via standard path
```

Returning `"yes; derived prime(seven) from the case-split restriction"` directly without `facts = Pair(goal, facts)` would still answer the immediate `query:` but would *not* populate `last_goal`'s derivation graph, would not survive `_persist_talk_state`, and would not be found by `why` (11118) or `vocabulary.py:DerivationTree` (2701). The earlier review flagged these provenance consumers precisely for this reason; Route A must satisfy them.

**Hold maintained:** no Route A code written this turn; verification only. Next: Route A spec with exact accessors above (P2 `InstalledCaseSplits`+`CaseSplitExactlyOne`, P1 `Head(goal)` filler match, P3 `run_talk_mode` closure, `ExactDivisorRestriction` evidence shape) and the three-fact discipline applied to `allowed_nats` building.

---

## Ledger

```text
branch: arena/01a0bbdd-cat-theo-machine
HEAD: 3b28f60 → (this doc pending commit)  (prior: 009e8a7 join opt + b424250 hangup merge)
tag cint-integrated-8b: 4420ade (8B rent) — correctly not moved
artifacts: programme_c/tests/artifacts/2026-09-23/p1p3_verification.md (P1-P3, ACCEPTED)
           programme_c/tests/artifacts/2026-09-23/c0_verification.md (C0-1/2/3, this file)
```

Prime route remains HOLD; C0 facts now verified by call-site reading and live synthetic-split execution, not wire inference.
