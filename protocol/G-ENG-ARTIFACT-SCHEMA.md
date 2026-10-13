# G-ENG-ARTIFACT-SCHEMA

Generated from the single declarative field table in `tools/cur_artifact_schema.py`, which is derived from what `tools/cur_extract_evidence.py`'s checked handlers read. It is the contract an author must satisfy before submitting a frozen artifact to the grader lane. No timestamps are embedded in this generated output.

- **Agent:** SCHEMA-eng
- **Evaluator-side, training-visible: no.**
- **Schema version:** `1` (pinned to the grader `SCHEMA_VERSION`).
- **Ruleset id:** `e3e4e7-grader-v1-7ae056945c93e3d8`
- **Bundle schema:** `geng-bundle/v2`
- **Extractor version:** `3.0.0`

## Capability ceiling (stated plainly)

This lane validates **checked, fixed-contract math**:

```text
frozen bundle -> cur_extract_evidence.py -> evidence manifest -> cur_grade_artifact.py
             -> C1..C6 verdicts
```
It is **tier-2.5**: it re-derives the pinned E3/E4/E7 facts (kernel, descent ΔH <= -1, mod-4 residue ΔS ≡ 0) by computation against the fixed problem. It does not read a bundle's self-declared verdict, and it does not tier-3 replay an arbitrary proof. A recognized role **never** establishes an evidence bit by itself — it only *selects* a handler.

The schema layer distinguishes four states and never conflates them:

| State | Meaning | Established by |
|---|---|---|
| `SCHEMA_VALID` | top-level shape, id uniqueness, citation arrays, collection shapes, numeric domains, and declared canonical move forms all hold | this module |
| `CHECKABLE_CONTENT_PRESENT` | the payload fields a check needs are present (metadata, never a verdict) | this module |
| `CHECK_ESTABLISHED` | an evidence bit set by actual computation against the pinned problem | the extractor's checked handlers |
| `PROOF_REPLAYED` | tier-3 full proof-checker replay of arbitrary cited nodes | **not supported** on this lane |

**Schema validity never implies mathematical validity.** A bundle can be `SCHEMA_VALID` yet yield `CANNOT_DETERMINE` (or `FAIL`) downstream when its required payload is absent, empty, or unrelated.

## Global bundle shape

```json
{ "schema": "geng-bundle/v2", "contract": "E3 | E4 | E7",
  "candidate": { "id": "...", "role": "candidate", "cites": ["support-id", ...] },
  "claims": [ { "id": "...", "kind": "assumption", ... } ],
  "nodes": [ { "id": "...", "role": "...", "kind": "derived|assumption",
              "cites": ["support-id", ...], "payload": { ... } } ],
  "records": { "name": [ { "id": "...", "role": "...", "cites": [...], "payload": {...} } ] } }
```
**Required:** `schema` == `geng-bundle/v2`; `contract` in `{E3, E4, E7}`; a `candidate` object with a string `id`; `nodes` an array whose nodes have string `id`s, and (if present) string-array `cites`/`refs` and an object `payload`. **IDs must be unique** across `claims` + `candidate` + `nodes` + `records`.

Global malformations => `exit 2` (no manifest): duplicate id, non-array `cites`/`nodes`, non-object `payload`, unsupported schema, unsupported contract.

## Field definitions

Each record: field name (dotted), contract families, JSON shape, required/optional, numeric/domain constraint, checks fed, `CANNOT_DETERMINE`-when-absent effect, canonical representation, and the known validation limit of this schema layer.

### FIELDS `E3` family

| field | contract | shape | required | domain | checks fed | CD-when-absent | canonical | validation limit |
|---|---|---|---|---|---|---|---|---|
| `schema` | E3, E4, E7 | string | yes | must equal "geng-bundle/v2" | structural | extractor exit 2 (unsupported bundle schema); no manifest | BUNDLE_SCHEMA = "geng-bundle/v2" | equality to the fixed literal; no schema negotiation |
| `contract` | E3, E4, E7 | string | yes | member of {E3, E4, E7} | structural | extractor exit 2 (unsupported contract); no manifest | one of E3 / E4 / E7 | family fixed to the three glued contracts |
| `candidate.id` | E3, E4, E7 | string | yes | non-empty string | structural | extractor exit 2 (candidate must have a string id); no manifest | candidate id | must be unique across claims+candidate+nodes+records |
| `candidate.cites` | E3, E4, E7 | array<id> | no | array of string ids | structural | candidate support not traced -> support-dependent checks stay CD | array of cites/refs ids | only string ids validated; an unresolved ref -> CD, not a schema reject |
| `claims` | E3, E4, E7 | array<object> | no | array; each has a string 'id' and optional 'kind'/'text' | structural | assumptions absent -> no top-level support to resolve | array of assumption records | ids are pooled for uniqueness but absent claims are not a reject |
| `nodes` | E3, E4, E7 | array<object> | yes | array; each node has a string 'id', optional 'role'/'kind'/'cites'/'payload' | structural | extractor exit 2 (nodes must be an array); no manifest | array of node records | a node with no payload is schema-valid (role-only) but not checkable |
| `records` | E3, E4, E7 | object<name, array<object>> | no | mapping name -> array; each record has 'id'/'role'/'cites'/'payload' | structural | no named record collections; handler falls back to node roles | object of named record arrays | record ids pooled for uniqueness; absent records are not a reject |
| `node.cites / node.refs` | E3, E4, E7 | array<id> | no | array of string ids ('cites' preferred, 'refs' accepted as alias) | structural | derived with no support -> upstream, CD for dependent bits | array of support ids | unresolved/self/circular refs are CD, not schema rejects |
| `node.kind` | E3, E4, E7 | string | no | 'assumption' or 'derived'; absent defaults to derived | structural | treated as derived (assumption only if kind == assumption) | 'assumption' or 'derived' | controls resolution classification only; never sets an evidence bit |
| `node.payload` | E3, E4, E7 | object | no | object if present | structural | role-only node -> all dependent checks CANNOT_DETERMINE | object of named payload fields | an empty/absent payload is schema-valid but not checkable |
| `weights.vector` | E3 | array<number> | yes | length == E3_N (6); every element an integer | C1, C2, C3 | C1/C2/C3 CANNOT_DETERMINE (no vector to check) | length-6 integer vector | checker verifies shape/length/numeric; kernel membership is computed by the extractor |
| `weights.provenance` | E3 | string | yes | 'derived' or 'supplied' | C6 | C6 CANNOT_DETERMINE (no provenance to classify) | 'derived' | string equality only; no semantic check of how it was derived |
| `moves.pairs` | E3 | array<[integer, integer]> | yes | length == E3_N; pairs are adjacent sectors of the 6-cycle | C1, C2 | move family undetermined -> C1/C2 stay CD | E3_MOVE_PAIRS (the pinned 6-cycle) | checker validates shape; the extractor compares to the pinned family for family_ok |
| `start.vector` | E3 | array<number> | yes | length == E3_N (6); every element an integer | C3 | C3 CANNOT_DETERMINE (no start vector) | length-6 integer start vector | checker validates shape, not the reading value |
| `odd-control.target_n` | E3 | number | yes | == E3_ODD_N (5) | C4 | C4 CANNOT_DETERMINE (no odd-control size) | target_n = 5 | checker validates numeric equality to the pinned odd size; kernel dim is computed |
| `generation.on_candidate` | E3 | array<number> | yes | length == E3_N (6) | C5 | C5 CANNOT_DETERMINE (no candidate-on reading) | length-6 integer reading | checker validates shape; same-line check is computed by the extractor |
| `generation.off_candidate` | E3 | array<number> | null | no | null/empty (candidate removed) or array | C5 | defaults to candidate survives -> C5 can FAIL | null (removed) or empty array | checker validates shape; deciding removal is the extractor's job |

### FIELDS `E4` family

| field | contract | shape | required | domain | checks fed | CD-when-absent | canonical | validation limit |
|---|---|---|---|---|---|---|---|---|
| `schema` | E3, E4, E7 | string | yes | must equal "geng-bundle/v2" | structural | extractor exit 2 (unsupported bundle schema); no manifest | BUNDLE_SCHEMA = "geng-bundle/v2" | equality to the fixed literal; no schema negotiation |
| `contract` | E3, E4, E7 | string | yes | member of {E3, E4, E7} | structural | extractor exit 2 (unsupported contract); no manifest | one of E3 / E4 / E7 | family fixed to the three glued contracts |
| `candidate.id` | E3, E4, E7 | string | yes | non-empty string | structural | extractor exit 2 (candidate must have a string id); no manifest | candidate id | must be unique across claims+candidate+nodes+records |
| `candidate.cites` | E3, E4, E7 | array<id> | no | array of string ids | structural | candidate support not traced -> support-dependent checks stay CD | array of cites/refs ids | only string ids validated; an unresolved ref -> CD, not a schema reject |
| `claims` | E3, E4, E7 | array<object> | no | array; each has a string 'id' and optional 'kind'/'text' | structural | assumptions absent -> no top-level support to resolve | array of assumption records | ids are pooled for uniqueness but absent claims are not a reject |
| `nodes` | E3, E4, E7 | array<object> | yes | array; each node has a string 'id', optional 'role'/'kind'/'cites'/'payload' | structural | extractor exit 2 (nodes must be an array); no manifest | array of node records | a node with no payload is schema-valid (role-only) but not checkable |
| `records` | E3, E4, E7 | object<name, array<object>> | no | mapping name -> array; each record has 'id'/'role'/'cites'/'payload' | structural | no named record collections; handler falls back to node roles | object of named record arrays | record ids pooled for uniqueness; absent records are not a reject |
| `node.cites / node.refs` | E3, E4, E7 | array<id> | no | array of string ids ('cites' preferred, 'refs' accepted as alias) | structural | derived with no support -> upstream, CD for dependent bits | array of support ids | unresolved/self/circular refs are CD, not schema rejects |
| `node.kind` | E3, E4, E7 | string | no | 'assumption' or 'derived'; absent defaults to derived | structural | treated as derived (assumption only if kind == assumption) | 'assumption' or 'derived' | controls resolution classification only; never sets an evidence bit |
| `node.payload` | E3, E4, E7 | object | no | object if present | structural | role-only node -> all dependent checks CANNOT_DETERMINE | object of named payload fields | an empty/absent payload is schema-valid but not checkable |
| `params.houses` | E4 | integer | yes | == E4_TWO_HOUSES (2) | C2 | C2 CANNOT_DETERMINE (no house target) | houses = 2 | checker validates integer/equality; the partition claim is the extractor's |
| `params.degree_bound` | E4 | integer | yes | <= E4_MAX_DEGREE (3) | C1 | C1 FAIL if a descent argument is present, else CANNOT_DETERMINE | degree_bound = 3 | checker validates integer/ordering; a descent-from-e_in-alone claim is graded by the extractor |
| `moves.moves` | E4 | array<move> | yes | each move is a record; see canonical move forms below | C3 | C3 CANNOT_DETERMINE (no move record) | canonical form is {e_in, e_out}; {d, s} accepted as a documented alternate | checker validates shape and dual-form equivalence; descent delta computed by the extractor |
| `move.e_in` | E4 | integer | yes | >= 0; legal move requires e_in >= 2 | C3 | move not parseable -> C3 may stay CD / FAIL | e_in (enemies in own house) | checker validates non-negative integer |
| `move.e_out` | E4 | integer | yes | >= 0 | C3 | move not parseable -> C3 may stay CD / FAIL | e_out (enemies in the other house) | checker validates non-negative integer |
| `move.d / move.s` | E4 | integer | no | d = e_in + e_out, s = e_in (documented alternate) | C3 | allowed; only the canonical e_in/e_out form is required | d = degree, s = same-house; e_in = s, e_out = d - s | if both forms appear and disagree -> contradiction (schema reject) |
| `bound.lower_bound` | E4 | integer | yes | >= 0 | C4 | C4 CANNOT_DETERMINE (no lower bound claimed) | lower_bound = 0 | checker validates integer/ordering |
| `terminal.claim` | E4 | string | yes | 'no_legal_move' or 'global_min' | C5 | C5 CANNOT_DETERMINE (no termination claim) | 'no_legal_move' | checker validates membership; the global-min overclaim is the extractor's |
| `measure.provenance` | E4 | string | yes | 'derived' or 'supplied' | C6 | C6 CANNOT_DETERMINE (no measure provenance) | 'derived' | string equality only |

### FIELDS `E7` family

| field | contract | shape | required | domain | checks fed | CD-when-absent | canonical | validation limit |
|---|---|---|---|---|---|---|---|---|
| `schema` | E3, E4, E7 | string | yes | must equal "geng-bundle/v2" | structural | extractor exit 2 (unsupported bundle schema); no manifest | BUNDLE_SCHEMA = "geng-bundle/v2" | equality to the fixed literal; no schema negotiation |
| `contract` | E3, E4, E7 | string | yes | member of {E3, E4, E7} | structural | extractor exit 2 (unsupported contract); no manifest | one of E3 / E4 / E7 | family fixed to the three glued contracts |
| `candidate.id` | E3, E4, E7 | string | yes | non-empty string | structural | extractor exit 2 (candidate must have a string id); no manifest | candidate id | must be unique across claims+candidate+nodes+records |
| `candidate.cites` | E3, E4, E7 | array<id> | no | array of string ids | structural | candidate support not traced -> support-dependent checks stay CD | array of cites/refs ids | only string ids validated; an unresolved ref -> CD, not a schema reject |
| `claims` | E3, E4, E7 | array<object> | no | array; each has a string 'id' and optional 'kind'/'text' | structural | assumptions absent -> no top-level support to resolve | array of assumption records | ids are pooled for uniqueness but absent claims are not a reject |
| `nodes` | E3, E4, E7 | array<object> | yes | array; each node has a string 'id', optional 'role'/'kind'/'cites'/'payload' | structural | extractor exit 2 (nodes must be an array); no manifest | array of node records | a node with no payload is schema-valid (role-only) but not checkable |
| `records` | E3, E4, E7 | object<name, array<object>> | no | mapping name -> array; each record has 'id'/'role'/'cites'/'payload' | structural | no named record collections; handler falls back to node roles | object of named record arrays | record ids pooled for uniqueness; absent records are not a reject |
| `node.cites / node.refs` | E3, E4, E7 | array<id> | no | array of string ids ('cites' preferred, 'refs' accepted as alias) | structural | derived with no support -> upstream, CD for dependent bits | array of support ids | unresolved/self/circular refs are CD, not schema rejects |
| `node.kind` | E3, E4, E7 | string | no | 'assumption' or 'derived'; absent defaults to derived | structural | treated as derived (assumption only if kind == assumption) | 'assumption' or 'derived' | controls resolution classification only; never sets an evidence bit |
| `node.payload` | E3, E4, E7 | object | no | object if present | structural | role-only node -> all dependent checks CANNOT_DETERMINE | object of named payload fields | an empty/absent payload is schema-valid but not checkable |
| `params.window_width` | E7 | integer | yes | == E7_WINDOW (4) | C1 | C1 CANNOT_DETERMINE (no family width) | window_width = 4 | checker validates integer/equality; derivation is the extractor's |
| `params.modulus` | E7 | integer | yes | == E7_MODULUS (4) | C1, C2, C4 | residue arithmetic undetermined -> dependent checks CD | modulus = 4 | checker validates integer/equality |
| `samples.sequences` | E7 | array<array<number>> | yes | each sequence length >= declared window width (else window undefined) | C2 | C2 CANNOT_DETERMINE (no sample sequence) | array of numeric sequences of length >= window_width | checker validates sequence shape + length-vs-width; residue delta computed by the extractor |
| `samples.window_width` | E7 | integer | no | >= 1; per-record override of the family width | C2 | falls back to params.window_width | per-record width, or the family width when absent | a non-canonical width is graded by the extractor (width-not-4 FAIL), not a schema reject |
| `separation.target_residue` | E7 | integer | yes | integer residue | C3 | C3 CANNOT_DETERMINE (no separation target) | target_residue != 0 when 4 does not divide n | checker validates integer; the divide-4 separation is the extractor's |
| `separation.start_residue` | E7 | integer | no | integer residue | C3 | C3 uses target residue + n when present | integer start residue | checker validates integer, not the residue relationship |
| `separation.n` | E7 | integer | yes | integer length; separation requires n % 4 != 0 | C3 | C3 CANNOT_DETERMINE (no length to divide) | n not divisible by 4 | checker validates integer; divisibility is the extractor's |
| `odd-control.sample` | E7 | array<number> | yes | numeric sequence; length >= E7_ODD_WINDOW (3) | C4 | C4 CANNOT_DETERMINE (no odd-width control sample) | length->=3 numeric sequence | checker validates shape; the width-3 delta == {2} is computed by the extractor |
| `rejected.candidates` | E7 | array<object> | yes | each has 'name' and 'class' in the allowed set | C5 | C5 CANNOT_DETERMINE (no rejected-candidate classification) | class in {'not_invariant','preserved_but_non_separating','invariant','separating'} | checker validates membership; the misclassification is the extractor's |
| `observable.provenance` | E7 | string | yes | 'derived' or 'supplied' | C1, C6 | C1/C6 CANNOT_DETERMINE (no derived observable) | 'derived' | string equality only |

## Canonical move forms

- **E3:** exact integer weights (length `E3_N` = `6`), complete declared move family `E3_MOVE_PAIRS` = `[[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 0]]`.

- **E4:** canonical move form is `{e_in, e_out}`; `{d, s}` (degree & same-house) is accepted only as a **documented alternate** (`e_in = s`, `e_out = d - s`). If both forms appear in one move and disagree, the schema is contradictory and rejected. Max degree `E4_MAX_DEGREE` = `3`; `E4_TWO_HOUSES` = `2`.

- **E7:** explicit sequence, window width `E7_WINDOW` = `4`, modulus `E7_MODULUS` = `4`, and flip samples; a sample sequence must be long enough to realize its window width (a shorter sequence with a declared width is a structural contradiction). Odd-width control uses `E7_ODD_WINDOW` = `3`.

## Pinned source identities

| identity | value |
|---|---|
| contract refs | {"E3": "CUR-ENGEL-E3-EVALUATOR-CONTRACT.md", "E4": "CUR-ENGEL-E4-GRADER-CONTRACT.md", "E7": "CUR-ENGEL-E7-GRADER-CONTRACT.md"} |
| contract commits | {"E3": "c10011bfabc73b55c7a3de80c4ff14a78234f17b", "E4": "c10011bfabc73b55c7a3de80c4ff14a78234f17b", "E7": "c10011bfabc73b55c7a3de80c4ff14a78234f17b"} |
| contract content digests | {"E3": "98d700321bd58e1ed43fabcde8c044ff87673ea97d34e6b3a04a4b9a24ec1809", "E4": "94c5d80cca5c2c29edfa23b8ad55c068411a2c439de18c1ab4924be5ef2a34ab", "E7": "b06703d561e4d89232aeb76206d51d5f98be4838b1eb6b44b7a97336b0de4e17"} |
| in-tree contract paths | {"E3": "CUR-ENGEL-E3.md", "E4": "CUR-ENGEL-E4.md", "E7": "CUR-ENGEL-E7.md"} |
| rubric ref | `CUR-GRADER-RUBRIC.md` (commit `70271007ba5292e782c223bca1474dce8ced8168`, digest `c4c420bd55f019fcd7c2f3ee468dfbe10fad937d5009d1cdc6cb5d374b04518e`) |

## Notes

- A role only selects a handler; it does not itself assert a fact.
- Unknown payload keys are tolerated (ignored by the extractor); this layer reports known-field validity rather than rejecting unknown keys, matching extractor semantics.
- This generated output is deterministic: it embeds no timestamps and no run-specific state. Execution time and test results live in the separate verification artifact.
