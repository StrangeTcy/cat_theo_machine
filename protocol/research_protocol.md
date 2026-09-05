# research_protocol.md — the index (this lineage)

Maintained by INT. Everything below is inspected from the actual code of
this checkout, not assumed from any earlier charter. Wave-1 base tag:
`s1-relation-contracts` @ `897c07cdfbfec8866b2b0a0921012d13a646630a`.

## Roster, mapped to this session's reality

The 8-role roster (INT, S-eng, E-eng, G-eng, F-tools-eng, G/I-op, S/E-op,
F-op) assumes one clone per agent and per-track branches. This sandbox is
pinned to a single branch (`arena/01a064d5-cat-theo-machine`); no other
branch may be created or pushed from here. Consolidation in force, ratified
by the operator across prior turns: **INT + S-eng merged** (this agent);
operators are human and external; E/G/F tracks are parked with standing
rulings (E: awaiting substrate, none exists here; G: unstarted; F: parked
until structural parity). The never-merge rule (engineer/operator) holds:
no operator work runs in this sandbox.

## Lineage gap register (checked 2026-09-04, re-confirmed 2026-09-05)

Absent in this checkout, referenced by v1-era texts: `research.py`,
`provenance.py`, `explanation.py`, `LearnedMemoryCheckpointTest`,
`rule:`/`fact:` teaching path, `research_protocol` role table, FLT goal
term + decoy, `FireAny`, learned-memory masks, rent machinery, Step-39
contract system. Track S is executed under the ratified translation
(`verification/strack_translation_2026-09-05.md`); F remains parked.

## Interface-ownership table (from actual code)

| File | Symbol (line at base tag) | Semantics (measured) | Owner | Change path |
|---|---|---|---|---|
| testsuite.py | `_register_test` (~13855) | appends `Pair(name, Pair(inputs, Pair(edge, Pair(expected, empty))))` to the graph test-results context; registration order is shard-partition order | INT | [SHARED] proposal in protocol/S.md |
| graph.py | `TestShardAccept` / `TestShardConfigure` | round-robin shard gate over registration order; `tools/shard_suite.py` drives it | INT | [SHARED] |
| graph.py | `Proposal`/`Approved`/`ApprovedAuthority` (418 ff.) | adoption pipeline + human approval gate | S | [S] |
| graph.py | `EnumerateCandidatePatterns` (7398), `MineRecurringPatterns` (7677), `MineMetaPatterns` (6475) | bounded candidate/mining enumeration | S | [S] |
| graph.py | `RelationContractArity/ExtensionalAt/Contracts/Insert` (this tag) | S1 ground contract facts into the knowledge trie | S | [S] |
| knowledge.py | `KnowledgeTrie*` (134 ff.) | fact store: insert/lookup/has/facts | S (contracts), G (facts, unstarted) | [S]/[G] |
| graph.py | correspondence family: `CorrespondenceApply` (11348), `DefaultCorrespondenceVocabulary` (11405), `ConverseInterpretations` (13022), `SurfaceUnknownWords` (13943), `Converse` (14035), `MeaningEvaluate`/`PropositionEvaluate` (~11970/14400) | talk side: templates are laws; outcomes Understood/NotUnderstood/Ambiguous with structured reasons | INT | [SHARED] |
| proof.py | `MultiRule` (167), `CompileRuleChain` (299) | rule compilation; pool entries are raw rule edges | [SHARED] | [SHARED] |
| proof.py / graph.py | `CompileRuleToLaw` (graph 3692) | RAISES on non-rule input (does not refuse with EmptyList) — ledgered defect note 5 | [SHARED] | [SHARED] |
| graph.py | `CompileMultiRuleToLaw` (3803) | conjunctive-law compiler for multi-premise rules | [SHARED] | [SHARED] |
| search/engine.py | `SearchStep`/`_SearchStepKernel` (~2641) | job rule compilation + premise matching; item-2 selection witness still open here | [SHARED] | [SHARED] |
| persistence.py | `SnapshotCodec` (618) | namespace-driven at capture (`dict(vars(M))+vars(L)` in tests); serializes by identity | INT | [SHARED] |
| persistence.py | `SNAPSHOT_SYMBOL_NAMES` (202) | cold-restore fallback only; PARTIAL BY DESIGN — DividesLabel/ModuloLabel/GcdLabel absent; no test pins its length | INT | [SHARED] |
| labels.py | `sync_from_namespace` (2017) | restore-path rebinding `globals()[name] = namespace[name]` for listed names; partial (restore table, not a completeness gate) | INT | [SHARED] |
| runtime.py / main.py | `boot_from_packs`, `PACK_PATHS`, `_runtime_namespace` | boot; packs are rules-only (no `facts:` syntax exists) | INT | [SHARED] |
| planner.py | planner methods | G-eng surface (unstarted in this lineage) | G | [G] |
| — | learned-memory masks, rent/counterfactual | ABSENT. Rent defined measurably in the S translation (held-out SearchCost deltas) | S | [S] |

New-label rule for this lineage (replaces the v1 "both completeness
tables" rule, which assumed a pinning test that does not exist here):
register class + instantiation in labels.py; snapshot coverage is
automatic through the live namespace at capture; add to
`SNAPSHOT_SYMBOL_NAMES` + labels `sync_from_namespace` only when a term
carrying the label must survive cold restore (precedent: the
number-theory labels are absent from both and everything passes).

## Marked blocks

`# --- [S] ---` zones exist in labels.py and testsuite.py at this tag
(around the S1 contract labels and their two tests + registrations).
`[E]`, `[G]`, `[F]` zones will be marked when those tracks start; their
surfaces in this lineage are explanation (file absent), planner.py, and
tools/ respectively. research.py does not exist; S work lives in graph.py
under `[S]` until it does.

## Merge duty (single-branch adaptation)

With one branch there is no cross-branch merge; the duty becomes ordering
and labeling: `[SHARED]` commits carry instrument changes and precede
`[S]`/`[E]`/`[G]` commits in every push; every code commit re-cuts the
tag; every cut is classified SEMANTIC ( matcher/search/planner attempt
surface, codec reachability, registry order) or NON-SEMANTIC (docs,
comments, probes) with grounds; semantic cuts re-baseline operators. The
full two-shard suite runs before every tag; failure set must match or
shrink versus baseline (current baseline: 5 known reds, list in
protocol/preflight/ledger.md).

## Preflight status (this lineage)

Executed 2026-09-04 under tag `preflight-converse-outcome-guard`; full
report: `verification/preflight_2026-09-04.md`; ledger:
`protocol/preflight/ledger.md`. Items 1 and 3 have no subject in this
lineage (gap register); item 2 compile half verified, selection half open
(instrument locus named); item 4 complete, abort-as-defect-#1 applied
(D1). D2 and D3 fixed on later tags; correspondence family fully green.

## Blocked on operator

- CHARTER-v2 text (never supplied).
- TWO-PIPELINE.md full text (arrived truncated mid Text #3, 2026-09-05).
- The sealed Tier1 IMO manifest + its hash (F-track; parked regardless).
- Ratification of INT+S consolidation continuing under the 8-role plan
  (forced by single-branch pin; assumed yes absent objection).
