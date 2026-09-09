# G-ENG-ARTIFACT-SCHEMA

Describes the frozen G-ENG-style evaluator bundle that `tools/cur_extract_evidence.py` accepts, and
what its checked handlers require. This is **derived from the three checked handlers** (`_checked_e3`,
`_checked_e4`, `_checked_e7`) — it does not invent fields. It is the contract an author must satisfy
before submitting a frozen artifact to the grader lane.

- **Agent:** CUR-GRADER-ENG
- **Docs-only, evaluator-side; training-visible: no.**
- **Doc version:** pinned to the extractor `SCHEMA_VERSION` (currently **1**).

---

## 0. Capability ceiling (stated plainly)

This lane validates **checked, fixed-contract math**:

```text
frozen bundle → cur_extract_evidence.py → evidence manifest → cur_grade_artifact.py → C1..C6 verdicts
```

It is **tier-2.5**: it re-derives the pinned E3/E4/E7 facts (kernel, descent ΔH ≤ −1, mod-4 residue
ΔS ≡ 0) by computation against the fixed problem. It does **not** do tier-3 full proof-checker
replay of arbitrary cited nodes, and it does **not** read a bundle's self-declared verdict. A
recognized role **never** establishes an evidence bit by itself — a role only *selects* a handler.

---

## 1. Global bundle shape

Top-level object:

```json
{
  "schema": "geng-bundle/v2",
  "contract": "E3 | E4 | E7",
  "candidate": { "id": "...", "role": "candidate", "cites": [ "support-id", ... ] },
  "claims":  [ { "id": "...", "kind": "assumption", ... } ],
  "nodes":   [ { "id": "...", "role": "...", "kind": "derived|assumption",
                 "cites": [ "support-id", ... ],
                 "payload": { ... } } ],
  "records": { "name": [ { "id": "...", "role": "...", "cites": [ ... ], "payload": { ... } } ] },
  "parameters": { ... }
}
```

**Required:**
- `schema` must equal `geng-bundle/v2`.
- `contract` must be a string in `{E3, E4, E7}`. Anything else → extractor exit 2.
- `candidate` object with a string `id`.
- `candidate.cites` lists the support ids the candidate draws on; a candidate whose support does not
  resolve (unknown id, self-citation, cycle) is not trusted.
- `nodes` must be an array; each node must have a string `id` and, if present, `cites` must be an
  array of strings and `payload` (if present) an object.
- **IDs must be unique** across `claims` + `candidate` + `nodes` + `records`.

**Global failures (extractor exit 2, structured error, no manifest):**
- duplicate id
- non-array `cites` / non-array `nodes` / non-object `payload`
- unsupported `schema`
- unsupported `contract`

---

## 2. Proof-support dependency chain

The bundle's `claims` are **assumptions**. `nodes`/`records` are **derived conclusions** that cite
their support (in `cites`). Resolution rules:

- A derived item that cites **nothing** → `upstream` (unresolved) → the dependent evidence bit is
  **not** set, and a diagnostic is emitted.
- A derived item that cites itself → `self` → **not** set (diagnostic).
- A derived item that cites an **unknown id** → `unresolved upstream` → **not** set (diagnostic).
- A derived item that participates in a **support cycle** within the bundle → `cycle` → **not** set
  (diagnostic).
- Unrelated cycles in the machine's **general hypergraph** (outside the bundle) are **not** banned;
  only cycles inside this bundle's proof-support chain are rejected.
- Only support whose status is `assumption` or `ok` can be trusted as evidence source.

> Consequence: an author must cite *content-bearing* support, not just name the role.

---

## 3. FAIL vs CANNOT_DETERMINE (the single most important rule)

For every check the grader emits exactly one of PASS / FAIL / CANNOT_DETERMINE.

- **PASS** — the handler computed the pinned fact from cited payloads (evidence bit set).
- **FAIL** — the evidence is **present but wrong**: a payload exists but contradicts the pinned fact
  (e.g. degree-bound-violating move, a preservation claim refuted by a sample).
- **CANNOT_DETERMINE** — the evidence is **absent**: no valid payload, no cited count, no displayed
  sample. This is **not** a PASS and **not** a lazy FAIL.

The extractor sets a **FAIL bit only from present-but-wrong** content. Pure absence stays
CANNOT_DETERMINE. (This is why the role-only negative controls yield CANNOT_DETERMINE, not FAIL.)

If a single fixture produces two or more distinct discrepancy labels, the grader exits 2
`AMBIGUOUS_DISCREPANCY` (never picks one by iteration order).

---

## 4. Role vocabulary

A node's `role` selects the handler path. Roles are **not** evidence: a role with an empty or
unrelated `payload` produces no evidence bit.

| role | used by | meaning |
|---|---|---|
| `weights` | E3 | the candidate weight vector + provenance |
| `moves` | E3, E4 | the move family: E3 `pairs`, E4 `moves` records |
| `start` | E3 | the start-sector vector (and target family) |
| `odd-control` | E3, E7 | negative control record (E3 `target_n`, E7 `sample`) |
| `generation` | E3 | on/off candidate for the generator-removal check |
| `params` | E4, E7 | family parameters (houses/degree_bound; window_width/modulus) |
| `hypothesis` | E4 | alternative home for E4 params |
| `bound` / `wellfounded` | E4 | lower-bound / well-founded record |
| `terminal` / `terminus` | E4 | terminal-state claim (`no_legal_move` vs `global_min`) |
| `measure` / `monovariant` | E4, E7 | derived measure/observable provenance |
| `samples` | E7 | list of sign sequences exercising the flip delta |
| `separate` / `separation` | E7 | start/target residue separation |
| `control` | E7 | width-3 negative-control sample |
| `rejected` | E7 | rejected-candidate classification |
| `observable` | E7 | the derived observable (provenance) |

---

## 5. Per-family requirements (derived from the handlers)

### 5.1 E3 — six-sector alternating sum, adjacent-increment moves

Pinned facts: `w` in kernel of the move matrix; `R(start) = 2`; every all-equal reading is `0`;
the 5-sector odd cycle admits no nonzero exact linear observable.

| check | required payloads | bit true when | bit absent when | hard-fail |
|---|---|---|---|---|
| C1 kernel | `weights.vector`, `moves.pairs` | `w` in kernel (`w_i + w_j = 0` cyclically) and supplied move family == pinned 6-pair family | either field absent / family mismatch | `stated_without_move_family` if a weight present but not in kernel |
| C2 preservation | `weights.vector`, `moves.pairs` | every declared move gives `ΔR = w_i + w_j = 0` | missing / family mismatch | `a_move_changes_reading` if any move changes the reading |
| C3 separation | `weights.vector`, `start.vector` | `Σw = 0` and `R(start) ≠ 0` | either vector absent | `start_equals_target` if `Σw ≠ 0` or `R(start) = 0` |
| C4 odd control | `odd-control.target_n` | `target_n == 5` and kernel dim of the 5-pair family is `0` | `target_n` absent/unsupported | `odd_cycle_false_invariant` if kernel dim `> 0` |
| C5 removal | `generation.on_candidate` (+`off_candidate`) | on-run candidate reproduces the kernel line and off-run is empty | no generation payload | `candidate_survives_removal` if on-run not on kernel line or off-run nonempty |
| C6 no injection | `weights.provenance` | provenance `derived` and `weights.vector` on the kernel line | no payload | `weights_injected` if provenance `supplied` or vector off-line |

Adversarial cases that must **not** pass: role-only weights; empty `payload`; `weights` citing an
unknown node; self-citing weights; circular `weights↔moves`; an unresolved upstream move; a weight
not in the kernel; a contradictory pair of weight records.

### 5.2 E4 — descent, two-house partition, max degree ≤ 3

Pinned facts: exactly two houses; each member has ≤ 3 enemies; for a legal move (`e_in ≥ 2`,
`e_in + e_out ≤ 3`) `ΔH = e_out − e_in ≤ −1`; `H ≥ 0`; termination is "no legal move", not a global
minimum.

| check | required payloads | bit true when | bit absent when | hard-fail |
|---|---|---|---|---|
| C1 hypothesis | `params.houses`, `params.degree_bound` | `houses == 2` and `degree_bound ≤ 3` | no degree_bound and no descent argument | `argues_from_e_in_alone` if a descent arg present but no degree bound; or `cites_max_degree_le_3` absent when bound > 3 |
| C2 houses | `params.houses` | `houses == 2` | `houses` absent | `house_target_ambiguous` if `houses ≠ 2` |
| C3 descent | `moves.moves` (`{e_in,e_out}` or `{d,s}`) | every legal move has `ΔH = e_out − e_in ≤ −1` | no move record | `asserts_unbounded_descent` if a move violates the degree bound (e.g. `(d,s) = (4,2)`) or has `ΔH > −1` |
| C4 well-founded | `bound.lower_bound` (or `wellfounded`) | `lower_bound ≥ 0` | no bound record | `termination_no_lower_bound` if bound present but negative |
| C5 terminal ≠ min | `terminal.claim` | `claim == "no_legal_move"` | no terminal claim → CD | `concludes_global_minimum` if `claim == "global_min"` |
| C6 no injection | `measure.provenance` | provenance `derived` | no payload | `measure_injected` if provenance `supplied` |

Adversarial cases that must **not** pass: missing degree bound with a descent arg; a `(4,2)` move
treated as legal descent; a terminal-implies-unique-min overclaim; role-only E4.

### 5.3 E7 — width-4, mod-4 residue, sign-flip move

Pinned facts: observable = sum of cyclic 4-window products, taken mod 4; any single sign flip gives
`ΔS ≡ 0 (mod 4)`; a width-3 control gives `ΔS ≡ 2 (mod 4)`; `4 | n` when the start residue `S ≡ 0`.

| check | required payloads | bit true when | bit absent when | hard-fail |
|---|---|---|---|---|
| C1 derived | `params.window_width`, `observable.provenance` | `window_width == 4` **and** a derived observable (`provenance == "derived"`) | no observable node | `invented_without_move_set` if an observable present but not derived (a bare `window_width` tag alone is **not** a derivation) |
| C2 preservation | `samples.sequences` (each a `±1` list) | every single flip leaves `ΔS ≡ 0 (mod 4)` at width 4 | no valid width-4 sample | `preservation_no_even_argument` if a width-3 sample or a sample whose residue changes |
| C3 separation | `separation.start_residue`, `.target_residue`, `.n` | `4 ∤ n` and the residues differ | insufficient | `cannot_separate_4_divides` if residues coincide |
| C4 odd control | `control.sample` (width-3) | `ΔS ≡ 2 (mod 4)` under a single flip at width 3 | no control sample | `omits_odd_width_control` if the width-3 control is absent or ΔS ≠ 2 |
| C5 rejected | `rejected.candidates` (`name`, `class`) | candidates classified `not_invariant` / `preserved_but_non_separating` | no rejected-candidate record | `misclassifies_rejected` if a candidate is classed `invariant` / `separating` |
| C6 no injection | `observable.provenance` | provenance `derived` | no payload | `weights_injected` if provenance `supplied` |

Adversarial cases that must **not** pass: a bare `window_width: 4` tag with no derived observable;
a `window_width` tag of 4 with a width-3 sample; a preservation sample that changes residue; no
samples at all (→ CANNOT_DETERMINE, never PASS); role-only E7.

---

## 6. Schema / ruleset binding

The emitted evidence manifest validates against the grader's pinned identity:

- `schema_version` = the grader's `SCHEMA_VERSION` (currently **1**).
- `ruleset_id` = the grader's `RULESET_ID` (SHA-256 digest of the grader's rule tables).
- `contract_ref` / `rubric_ref` = the grader-pinned authoritative contract/rubric paths, plus the
  pinned source **commits** and **content digests** (the in-tree reconstruction path is recorded
  separately from the grader-pinned authoritative path; they are different files).

The extractor reads the grader's constants directly, so a manifest it emits always carries a matching
`schema_version`/`ruleset_id`. A manifest that does not match is rejected by the grader (exit 2).

---

## 7. Exit codes (extractor)

| code | meaning |
|---|---|
| 0 | manifest written; no unresolved/broken refs |
| 1 | manifest written; at least one unresolved/broken ref (partial extraction) |
| 2 | malformed / unsupported / unsupported-contract input (no manifest written) |

Downstream rule: extractor exit 0 or 1 → run `cur_grade_artifact.py`; exit 2 → do not grade.

---

## 8. Identity & reproducibility

The manifest carries an `identity` block: `bundle_digest` (SHA-256 of the canonical bundle), the
extractor's implementation identity + version, the grader ruleset identity, and the pinned
contract/rubric commits + content digests. Digests establish **identity**, not mathematical
validity. The raw transcript records real UTC start/end and the renderer timezone, so a filename
date is never mistaken for the clock.

---

*End of schema.* Author against it; the checked handlers reject anything the schema does not fix.
