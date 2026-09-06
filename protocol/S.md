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
