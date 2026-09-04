# Track S translation for this lineage — 2026-09-05

Operator ruling (this turn): map the S-track onto `EnumerateCandidatePatterns`
machinery; define translated S1/S2/S3 acceptance criteria before any S-track code.
This document is that definition. No S-track code ships with it.

## What the charter assumed vs. what this tree has

| Charter term (v1 lineage) | This lineage's carrier | Status |
|---|---|---|
| `research.py` mining/schema | `graph.py`: `EnumerateCandidatePatterns`, `MineRecurringPatterns`, `MineMetaPatterns` | present, different shape |
| `provenance.py` | `graph.py`: `Proposal`/`Approved`/`ApprovedAuthority` (line 418 ff.), `TrainingRecord` in `training.py` | present, thinner |
| `rule:`/`fact:` teaching path | packs are rules-only (`grep facts: packs/` empty); fact store is `knowledge.py` `KnowledgeTrie*` | partial: rules yes, facts no pack syntax |
| rent gate | none | absent — see S3 |
| `FireAny` activation | rule pool chains / template chains (`CompileRuleChain`, correspondence laws) | present under another name |
| learned-memory lifecycle | induced-law lifecycle: `AntiUnifyCorrespondence` → `Proposal` → `Approved` → active | present for correspondence laws |
| `Divides` / `Congruent` relations | `DividesLabel`, `ModuloLabel`, `GcdLabel` (number-theory pack: Divides is the hub; parity/modulo/gcd translate into it) | present; no Congruent label |

Track S touch list translated: mining classes and schema registry in `graph.py`,
contract records and trie insertion in `knowledge.py`/`graph.py`, tests in
`testsuite.py`. No `main.py` talk dispatch, no packs, no explanation code.
`core.py` untouched, as ever.

## S1 — contracts as ground facts about named relations

Contract atoms are machine terms:

- `RelationArity(name, n)` — `name` a Char-chain name constant for a relation
  label (e.g. the name of `DividesLabel`), `n` a Nat.
- `ExtensionalAt(name, position)` — same name encoding; `position` a Nat
  (1-based argument position).

Never a variable in relation position. They are ground facts about *named*
relations, per the standing ruling; the schema stage reads them as side
conditions by lookup (`KnowledgeTrieHasFact`), never as matched premises.

Teaching path: S is barred from packs, and packs carry no `facts:` syntax, so
contracts enter through a `RelationContracts` record (constructor class in
`graph.py`, modeled on `TrainingRecord`) whose load inserts the atoms via
`KnowledgeTrieInsertChain` and whose provenance field names the human source.
Ablation = dropping the record and rebuilding the trie; the audit header lists
the record. Provenance constant: `CONTRACT_FACT` (new label, listed in
`labels.py` alongside the other provenance constants this tree already uses).

**S1 acceptance (all must hold, each as a named test):**
1. `RelationContractRecordInsertsAndAblatesTest` — after load,
   `KnowledgeTrieHasFact(RelationArity(name-of Divides, 2))` is truth; after
   ablation and rebuild it is false.
2. `RelationContractNeverVariableTest` — constructing a contract atom with a
   variable in relation position yields `EmptyList` (refusal), not a fact.
3. Audit listing: the loaded-classes header of a session boot includes the
   contracts record — verified in the same test as (1) via the record chain.
4. Contracts are not laws: `CompileRuleToLaw` on a contract atom refuses
   (it is not a rule shape) — asserted, so contracts can never enter a rule pool.

## S2 — schema candidates over adopted machine-written laws

Adopted-law registry for this lineage: `Approved` proposals whose law term the
machine produced (induced via `AntiUnifyCorrespondence`, mined via
`MineRecurringPatterns`), excluding human pack rules — library theorems are not
evidence for invented schemas. Stage position: runs after adoptions settle,
consumes the registry only, emits into a **separate schema registry** (a
`RelationSchemas` record chain, its own constructor class), never into rule
pools or template chains.

Grouping key `(skeleton_id, contract_vector_id)`:
- `skeleton_id` — alpha-equivalence class of the law's premise/conclusion
  dataflow, computed by bounded structural anti-unification (the
  `AntiUnifyCorrespondence` walker is the in-tree precedent for the traversal;
  rename normalization over the law's variables).
- `contract_vector_id` — (arity, ordered extensional positions) that the
  member's relation carries in the contract store; must be identical across
  members, by lookup.

Gates (all required, each independently tested — carried over verbatim from the
accepted v1 design): (1) k ≥ 2 members; (2) pairwise distinct relation heads;
(3) alpha-equivalence re-asserted at emit; (4) identical contract vector;
(5) ≥ 2 distinct source goals in the union of member evidence; (6) every member
adopted (Approved) at mining time.

Output: `RelationSchema(relation_var, contract, premises, conclusion, evidence)`
with provenance `INVENTED_SCHEMA` (new label). `relation_var` exists only
inside the schema term and is substituted exactly once, at instantiation, by a
name constant.

**S2 acceptance:**
1. `PredicateHeadNotGeneralizedFromOneFamilyTest` — two adopted laws, same
   head, two goals → no schema.
2. `PredicateSchemaRequiresTwoDistinctHeadsTest` — gate 2, same shape.
3. `RelationContractRequiredTest` — members whose relations carry no contract
   facts → no schema. The load-bearing negative: same arity, same argument
   shape, `ExtensionalAt` absent → instantiation-side lookup fails → no
   instantiated law. Lookup, not unification.
4. `SchemaDoesNotFireDirectlyTest` — schema present, goal matches its body;
   the search pool and template chain are byte-identical to schema-absent
   (compared via `CompileRuleChain` output identity).
5. Gate 5: single source goal → no schema (folded into test 1).
6. Gate 6: an ablated member's law → no schema at mining time (stale-mark
   semantics from the accepted design deferred to S3 — v1 ruling: stale-mark,
   not drop, so reset stays the single authority).

## S3 — instantiation through the existing adoption path

For a target relation whose contract vector matches, substitute the name
constant for `relation_var` → a `Proposal` with the instantiated law and
provenance `INVENTED_LEMMA` (new label) → the **existing** `Approved` human
gate → activation through the same channel induced laws use today. No new
activation path. No `FireAny` equivalent ever sees a schema.

Rent, translated for this lineage (the v1 rent gate has no carrier here, so it
is defined measurably rather than imported): **a law pays rent iff, on a
held-out goal set, the search counters (`SearchCostExpanded`, `SearchCostGenerated`
— `search/engine.py`) drop with the law enabled versus disabled, with zero new
failures.** Rent is computed by a tool, recorded on the proposal, and a law
that fails rent for two consecutive held-out rounds is reported for ablation.
This is an instrument definition, not a promotion path; the human approval gate
stays mandatory and is not delegated.

**S3 acceptance:**
1. `SchemaInstantiatesConcreteLawTest` — contracted third relation → Proposal
   with correct substitution; content equals the hand-written expected law.
2. `PredicateSchemaAblationTest` — ablate a member → schema stale-marked; the
   flag surfaces on the instantiation output, the approval view, and the audit.
3. `PredicateSchemaResetRemineTest` — reset (clear adoption registry and schema
   registry) → schema gone and instantiated law inert; restore adoption,
   re-mine → schema returns.
4. Rent accounting: instantiated law carries a rent record after the held-out
   measurement; ablation of a rent-failing law removes its speedup (counters
   return to disabled values).

## S5 — near-transfer rerun, translated

Train: two contracted relations (`DividesLabel`, `ModuloLabel` families).
Hold out: `GcdLabel` (contracted, pack-present, distinct head). Five
configurations, `SearchCostExpanded` recorded each time: absent → long route;
schema enabled → short route; disabled → long; reset → gone; re-mine →
returns. The single acceptance sentence for S in this lineage: *a held-out
proof closes in fewer steps by a law the machine wrote, and the speedup
vanishes on reset and returns on restore.*

## Stop lines (unchanged in translation)

No far transfer; no second-order premises; no cross-domain schemas; contract
atoms never enter premise matching; schemas never enter rule pools or template
chains; no private promotion path around `Approved`.

## Order of work

S1 first (contract record + labels + tests), then S2 gates 1–6 over fixture
adoptions, then S3 instantiation + rent instrument, then the S5 rerun. Each
phase lands as its own `[S]` commit with its named tests; every code commit
re-cuts the tag. The first S1 commit will follow only after this document is
reviewed, per the operator's instruction.
