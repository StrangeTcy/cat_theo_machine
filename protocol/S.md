# protocol/S.md — track S (contracts → schemas → instantiation)

Branch: single-branch program; S commits label `[S]` and follow `[SHARED]`
commits in every push. Base for r1 work: tag `s1-relation-contracts`.

## Surfaces (this lineage, ratified)

- labels.py `# --- [S] ---` zone (contract labels live there now).
- testsuite.py `# --- [S] ---` zone (S tests + registrations).
- graph.py S constructors (`RelationContract*`, later schema stage);
  research.py does not exist — S mining work lands in graph.py beside
  `EnumerateCandidatePatterns`/`MineRecurringPatterns` until a split is
  warranted.
- knowledge.py trie (contracts + later G facts share it; [SHARED] for
  trie semantics themselves).

## Forbidden

main.py talk dispatch, packs (rules-only in this lineage regardless),
explanation code, planner methods, FLT content. Shared primitives
(matcher, codec, registry order, engine): stop and request `[SHARED]`
here; never fork.

## Status

- S1 LANDED (tag `s1-relation-contracts`): ground contract atoms
  (RelationArity/ExtensionalAt name-constant form), RelationContracts
  record with CONTRACT_FACT provenance + named human source, trie
  insertion, ablation = rebuild; two green tests
  (`relation_contract_record_inserts_and_ablates_test`,
  `relation_contract_never_variable_test`).
- S2 NEXT: schema-candidate stage, six gates, separate registry; test
  names and the load-bearing negative per
  verification/strack_translation_2026-09-05.md.
- S3/S4 after; S5 is an operator session (not this sandbox).

## Rent (definition in force)

A law pays rent iff held-out SearchCost counters (expanded/generated)
drop with it enabled versus disabled and no new failures; recorded on the
proposal; two failed rounds → reported for ablation. Approval stays
human, always.
