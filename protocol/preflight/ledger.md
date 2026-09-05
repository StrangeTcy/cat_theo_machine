# Defect ledger — running, this lineage

Format: numbered, named, locus, status, fixed-at. Found by running, never
by inspection alone. D1–D3 mirror verification/preflight_2026-09-04.md.

1. **D1 — suite detonation on NotUnderstood outcome.** Locus:
   testsuite.py `ConversePropositionTest.__init__` (base line ~7448).
   Guard-after-navigation: read Tail^4 off every Converse outcome before
   checking UnderstoodLabel; a three-slot outcome raised during
   `install_default_tests`, aborting the whole shard-1 install. Same
   crash at parent 227ddf7 → inherited, not a branch regression.
   FIXED at `3cac74c` (tag `preflight-converse-outcome-guard`):
   guards hoisted before navigation; failing outcome now fails only its
   own test. This is the charter's "abort is defect #1" rule applied.
2. **D2 — canonical equality sentence got no correspondence.** Locus:
   graph.py `Converse`/`ConverseInterpretations`/
   `DefaultCorrespondenceVocabulary`. All words known, no template for a
   plus-phrase subject; flat matcher binds one word per variable.
   FIXED at `b9a76f5` (tag `d2-equality-subject-template`): one new
   template law `is ?a plus ?b equal to ?c` → Equal(Add(?a,?b), ?c), in
   the vocabulary's own one-phrasing-one-law philosophy. Evaluation path
   unchanged (MeaningEvaluate recurses; NatEq answers; yes/no rendered).
3. **D3 — bare word lost its own reading.** Locus: graph.py
   `ConverseInterpretations`. Bare-genus template (Surface ?a) matched
   every single word; the direct word/spliced-Nat reading was computed
   only on an empty template scan, so a bare known word carried only the
   valueless genus reading → NotUnderstood(ReasonEvaluation). Both the
   test and the template landed in bulk `428ecdc`; red since.
   FIXED at `a93f128` (tag `s1-relation-contracts`): word reading seeds
   the interpretation list before the scan; templates and dedup
   unchanged.
4. **(carried, unresolved) five red tests, pre-existing at base
   `41e8078`, undiagnosed, two families:** shard 0:
   `tree_insert_deep_pair_lookup_avoids_recursion_test`,
   `compare_search_modes_fill_warms_resident_pool_before_root_wave_test`;
   shard 1: `heuristic_canonical_knowledge_agreement_test`,
   `curator_report_test`,
   `compare_search_modes_finds_reusable_worker_snapshot_dir_test`.
   This set of 5 is the current admission baseline (matches-or-shrinks).
5. **Instrument note — CompileRuleToLaw raises on non-rule input**
   (graph.py 3692) instead of refusing with EmptyList; a host-level
   AttributeError, not a machine term. No fix made: pre-existing,
   guarded around (S1 law-refusal assertion rides IsLawTerm). Revisit if
   any track needs programmatic refusal.
6. **Instrument note — item-2 selection witness open.** With two
   stand-in MultiRules as the whole SearchDFS pool, the job compiles and
   the start expands (`expanded: 1`) but no successor generates
   (`generated: 0`); locus search/engine.py `_SearchStepKernel` premise
   matching. Gating for F only; F is parked.
7. **Instrument note — sandbox resets rewind the checkout** to base
   `41e8078` between turns (three occurrences: before tags
   `d2-equality-subject-template`, `s1-relation-contracts`, and this
   turn). Recovery: fetch tip, byte-identity check of every tracked
   modification, `reset --hard` to tip, reinstall gmpy2/pyyaml
   (`pip --break-system-packages`, never conda). No loss to date; every
   green step is pushed immediately.

## Environment event log

- 2026-09-05: reset #3 before the partition turn; reconciled to
  `897c07c`; deps reinstalled. Recorded in the turn report.
