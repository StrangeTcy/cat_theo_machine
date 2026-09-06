# research_protocol.md — the index (this lineage)

Maintained by INT. Everything below is inspected from the actual code of
this checkout, not assumed from any earlier charter.

WAVE-1 BASE: none authorized. Candidate: `partition-32bc569` @
`32bc569a5e596081c4693e00098bfe9868c81504` (must contain the partition).
Authorization gate (Wave-0 ruling, 2026-09-05): lineage variances
recorded; A1 selection demonstrated; suite matches-or-shrinks; S1
persistence result recorded. Status of each: variances recorded (below);
A1 selection demonstrated at interface level with stand-in rules — the
real nosolutions pair is a recorded variance (protocol/preflight/
a1-selection.txt); S1 persistence measured (verification/2026-09-05-
s1-checkpoint-roundtrip.txt: cold round-trip succeeds, no registration
required). Operator acceptance of interface-level A1 closure (or a
supplied real pair) is the remaining authorization step.

## Roster, mapped to this session's reality

The 8-role roster (INT, S-eng, E-eng, G-eng, F-tools-eng, G/I-op, S/E-op,
F-op) assumes one clone per agent and per-track branches. PER THE WAVE-0
RULING (2026-09-05): the platform's single-branch pin does not alter role
ownership — the earlier INT+S consolidation has ENDED. This agent is INT
only: preflight repair, protocol index, suite evidence, tags, merge queue.
It does not begin S2. Track engineering (S2 onward) belongs to a separate
S-eng agent in its own sandbox on its own branch, spawned by the operator
from the authorized Wave-1 base tag; the landed S1 work
(tag `s1-relation-contracts`, commits 897c07c and its predecessors) stands
as an experimental source artifact for S-eng to import as an exact source
commit or a reviewed port. E/G/F remain parked/unstarted with standing
rulings; operators are human and external, and no operator work runs in
this sandbox.

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

## Preflight status (this lineage) — BLOCKED AT STEP 2

Executed 2026-09-04 under tag `preflight-converse-outcome-guard`; full
report: `verification/preflight_2026-09-04.md`; ledger:
`protocol/preflight/ledger.md`.

- PreflightTargetAbsent(item_1, LearnedMemoryCheckpointTest, lineage) —
  recorded variance; the equivalent swallowed-fault class was found,
  named D1, and fixed (guard-before-navigation, the ruling's own rule).
- PreflightTargetAbsent(item_3, FLTGoalParserSurface, lineage) — recorded
  variance; no FLT goal term or decoy exists anywhere in this checkout.
- item_2: compile YES (both rules through CompileMultiRuleToLaw);
  selectable — interface-level YES with stand-in rules: JoinPremises
  binding-sets found against a ground instance of the toy shape
  Eq(Add(x,1),x), and ApplyKnowledgeRewrite fired the structurally
  verified replacement Eq(two, Add(two, one)); evidence:
  protocol/preflight/a1-selection.txt. The REAL nosolutions pair is a
  lineage variance (no v1 research_protocol.md here). "D11", referenced
  by the ruling, is undefined in every text this session received and in
  this ledger; no port was routed; flagged to the operator.
- item_4: complete; dated two-shard artifact:
  verification/2026-09-05-partition-two-shard.txt (and the rerun log
  appended to it).

D2 and D3 fixed on later tags; correspondence family fully green.

## S1 persistence (measured, 2026-09-05)

Cold round-trip SUCCEEDS without fallback registration: capture
name-records label objects per-label; cold load resolves names through
_runtime_namespace_for_restore() which carries vars(Lmod). Restored head
IS the module singleton; trie answers HasFact on restored atoms. Measured
exemption documented in verification/2026-09-05-s1-checkpoint-roundtrip.txt;
no [SHARED] registration required. Registration in SNAPSHOT_SYMBOL_NAMES
would be needed only for bootstrap contexts that do not pass the full
labels namespace.

## Blocked on operator

- CHARTER-v2 text (never supplied; absence recorded in protocol/CHARTER-v2.md).
- TWO-PIPELINE.md text (never supplied; absence recorded in
  protocol/TWO-PIPELINE.md).
- UNIFIED-LAUNCH texts #4-#8 (received portion ends mid Text #3;
  truncation marked in protocol/UNIFIED-LAUNCH.md).
- A1 gate: accept interface-level selection closure with stand-in rules,
  or supply the real nosolutions pair / the v1 protocol document defining
  it; also define "D11" (undefined here).
- Wave-1 authorization: ruling on the above; then S-eng spawn on its own
  branch from the authorized base tag.
- The sealed Tier1 IMO manifest + its hash (F-track; parked regardless).
