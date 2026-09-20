# C-INT-8A-F1 Artifacts 2026-09-20 (Q-A tighten)

**Parent:** 65103a048eeea282a448213ccc23ce74cf023c35 (cint-integrated-7^{})
**Base:** eng-base-0@1374464 peeled 137446435362a9727c2f7c181c663adab9d4c357 (tag a52094888a30099150e6310b4b171ee2af97fe36)
**Commit:** 0639ced + 2ca84b0 (F1 on arena/01a0bbdd-cat-theo-machine tracking work/C-INT/eng-base-0/r2)
**Tag:** cint-integrated-8a retained at 0639ced (not moved)

## Q-A tighten implemented (programme_c/cert_replay.py)

- **ConclusionEntailsGoal(d_end,goal,registry)** named relation: accept iff
  `TermEqual(d_end,goal)` is truth OR `KnowledgeContains(d_end,goal,registry)` is truth
  after same `use_registry` canonicalization as `DerivationStart`
- **KnowledgeContains(d_end,goal,registry)**: true iff `IsKnowledge(d_end)` and
  - if `IsKnowledge(goal)` : `FactsCover(KnowledgeFacts(goal), KnowledgeFacts(d_end))` is truth
  - else (single fact) : `KnowledgeFacts(d_end)` contains a fact `TermEqual` to goal
- Both disjuncts use `M.CanonicalArithmeticTerm(..., registry)` before `TermEqual`/`KnowledgeContains`
  (same discipline as `DerivationStart`)
- **No prefix/skip/metadata-only acceptance**: any other conclusion is rejected with
  `F_INVALID_CERT` detail `"derivation conclusion does not entail declared goal"`
- **DerivationStart now fatal**: `TermEqual(DerivationStart(d,reg2), start)` must be truth
  after canonicalization; mismatch → `F_INVALID_CERT` detail `"derivation start does not match declared start"`
- **Tao worked example documented** in module docstring:
  ```
  goal  = Length(Segment(v,w), APShortSide(Tao Problem 1.1 triangle))
  d_end = Knowledge([Length(Segment(v,w), APShortSide(...)), SideOf(Segment(v,w), ...)])
  TermEqual(d_end,goal)=false  (structure mismatch)
  KnowledgeContains(d_end,goal)=true (goal fact member of Knowledge) → accept
  ```
  A derivation whose conclusion neither equals nor contains the declared goal
  (valid derivation of a *different* proposition) is rejected even though
  `BuildDerivation` succeeded internally.

## Tests (programme_c/tests/test_cint_8a.py)

- New `TestF1ConclusionEntailsGoal` (5 tests, total 30 in test_cint_8a):
  - `test_tao_knowledge_contains_accepted` — TermEqual false but KnowledgeContains true → accept
  - `test_tao_knowledge_contains_via_build_derivation` — real registry, Knowledge containing goal → accept
  - `test_valid_derivation_of_different_goal_rejected` — **required** Q-A test: internally consistent plan,
    `BuildDerivation` succeeds, conclusion neither equals nor contains declared goal → `F_INVALID_CERT`
    detail `"derivation conclusion does not entail declared goal"`; retains Tao acceptance and t-bad rejection
  - `test_different_goal_via_subprocess_rejected` — same via isolated replay path (`F_INVALID_CERT`)
  - `test_inconsistent_derivation_rejected` — empty plan → EmptyList (t-bad), start mismatch → fatal
- Retained 25 existing H1-H5 tests; full suite 30 in test_cint_8a, 92 total Programme C (87+5), all passing
- HOLD retained, no F_RENT_HOLD, Programme C only, protected files unchanged

## Branch / ledger

- `arena/01a0bbdd-cat-theo-machine` at 2ca84b0 (F1 on top of 0639ced)
- `work/C-INT/eng-base-0/r2` at 2ca84b0 (linear ledger 65103a0..0639ced plus F1, covers required range)
- Tag `cint-integrated-8a` not moved (still at 0639ced)

## Next

C-INT-8B rent correctness (H6/H7, C-G1/G2/G3, C-C1, Q-B unification, candidate-bearing rent) authorized.
