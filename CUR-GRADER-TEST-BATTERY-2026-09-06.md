# CUR — E3/E4/E7 grader test battery (mock blind-output artifacts) — 2026-09-06

Docs-only, CUR branch. Agent: CUR-ORACLE on `arena/01a066cf-cat-theo-machine`. Item 3 of the
CUR-ORACLE open items.

**Nature of this battery:** the E3/E4/E7 grader contracts (on `arena/01a068c2`) are **spec-only
and not-yet-run** — no executable grader exists on any branch. These are therefore **evaluator-side
fixtures**: mock *frozen blind-output artifacts* in the shape the contracts grade. Each is
constructed so that, *by construction* against the contract's C1–C6 criteria and its taxonomy
mapping, it fails exactly the check(s) that map to **one** taxonomy label and passes the rest.
This is not a runtime test harness (there is no grader binary to invoke); it is a fixture set that
defines the expected single-label classification, to be consumed by the grader when it lands.

**Firewall note (same as the contracts' contamination note):** these fixtures are **training-
visible: no** — they are grading texts, not training records, and they stay on the CUR branch.
They are written by the oracle-contaminated context and grade against the known sealed oracles;
they reveal the oracle answers to a human/context that has seen them, but they are **not** clean-
room blind evaluation and are not feedable as training inputs.

## Reference contracts and oracles

- Grader/contract files (sibling `arena/01a068c2` @ `d573e42`): `CUR-ENGEL-E3-EVALUATOR-CONTRACT.md`,
  `CUR-ENGEL-E4-GRADER-CONTRACT.md`, `CUR-ENGEL-E7-GRADER-CONTRACT.md`.
- Oracle cards: E3 `CUR-ENGEL-E3-oracle.md` (sibling), E4 canonical `CUR-ENGEL-E4-oracle.md`
  (mine), E7 canonical `CUR-ENGEL-E7-oracle.md` (mine).

## Taxonomy label → contract check mapping (from the contracts)

| taxonomy label | contract check(s) | contract |
|---|---|---|
| `hypothesis-omitted` | C1/C2 | E4 |
| `descent-unsupported` | C3/C4 | E4 |
| `overclaim` | C3/C5 (separation-unsupported also folds here) | E4, E7 |
| `constant-injection` | C6 | E4, E3, E7 |
| `derivation-absent` | C1 | E7 |
| `preservation-unsupported` | C2/C4 | E7 |

The operator-specified six labels are exactly the union of the contracts' taxonomies. Each mock
below is written against the contract where the label is most directly exercised.

---

## FAILING MOCKS — one per taxonomy label (each triggers exactly its own label)

### E4-M1 — `hypothesis-omitted`

Frozen blind-output artifact (G-ENG candidate) claims:
```text
monovariant: H = # same-house enemy edges
move: relocate a member with >= 2 enemies in its own house
derivation: a relocation changes H by (enemies_out - enemies_in);
  since enemies_in >= 2, the two houses form a partition, so
  the relocated member's own-house enemy count decreases, and H decreases.
conclusion: terminates.
```

Check-by-check (against E4 contract):
- C1 (max-degree ≤ 3 discharged): **FAIL** — the derivation never cites the max-degree ≤ 3 bound;
  it argues from `enemies_in >= 2` alone.
- C2 (exactly two houses): **PASS** — "the two houses form a partition" states exactly two houses.
- C3 (descent `ΔH ≤ −1` bounded): **PASS** in the sense that the claim does not rely on a
  counterexample (the actual contradiction in C3 is not reached because C1 already fails).
- C4 (termination well-founded): **PASS**-by-theorem (H ≥ 0 integer) — but the binding failure is C1.
- C5 (`termination ≠ global min`): **PASS** — it says "terminates", not "minimal".
- C6 (no constant injection): **PASS** — H is derived, not an input constant.

Disposition: FAIL on **C1 only** → taxonomy `hypothesis-omitted`. No other check fails, so no
other label is triggered. The taxonomy mapping for E4 C1/C2 = `hypothesis-omitted`; C1 is the
unmet check.

### E4-M2 — `descent-unsupported`

Frozen blind-output artifact claims:
```text
monovariant: H = # same-house enemy edges
given: each member has at most 3 enemies (max degree <= 3)
move: relocate a member with enemies_in >= 2
derivation: H decreases on every move, so it strictly decreases and, being
  bounded below, the process terminates.
```
Note: this mock **omits** the explicit `ΔH = e_out − e_in ≤ −1` bounding argument; it asserts
"strictly decreases" without the `e_in + e_out ≤ 3 ⇒ e_out ≤ 1` step.

Check-by-check:
- C1 (degree bound cited): **PASS** — the given is cited.
- C2 (two houses): **PASS** — "each member has at most 3 enemies" over two houses.
- C3 (descent obligation `ΔH ≤ −1` under legal moves): **FAIL** — the derivation asserts strict
  decrease without the `e_out ≤ 1` bound; it never shows `ΔH ≤ −1` for every legal move, so the
  descent is not demonstrated under the bound.
- C4 (well-founded termination): **PASS**-ish, but C3 is the binding failure; C4 notes H ≥ 0 but
  the descent itself is unsupported, so termination is not actually established. C4 is satisfied
  on its own terms (lower bound noted).
- C5 / C6: **PASS**.

Disposition: FAIL on **C3 (with C4 unsupported)** → taxonomy `descent-unsupported` (C3/C4). The
unmet check is C3; C4 failing to be grounded is a consequence of C3, not a separate label. Only
`descent-unsupported` is triggered. (C4 is folded into the same label per the E4 mapping.)

### E4-M3 — `overclaim`

Frozen blind-output artifact claims:
```text
monovariant: H = # same-house enemy edges
given: max degree <= 3
move: relocate a member with enemies_in >= 2
derivation: H strictly decreases under the bound, bounded below by 0, so the
  process terminates at the state minimizing H (the global minimum).
```

Check-by-check:
- C1/C2/C3/C4: **PASS** — bound cited, two houses, descent bounded, well-founded.
- C5 (`termination ≠ global min`, no optimality overclaim): **FAIL** — it concludes "the state
  minimizing H (the global minimum)", which is the exact conflated optimality claim the E4
  negative-control B refutes (4-cycle dual terminals).
- C6: **PASS**.

Disposition: FAIL on **C5 only** → taxonomy `overclaim`. No other label triggered.

### E7-M4 — `derivation-absent`

Frozen blind-output artifact claims:
```text
observable: O = ResidueMod(S, 4), where S = sum of a_i*a_{i+1}*a_{i+2}*a_{i+3}
move: FlipSign(state, position)
claim: O is invariant and the terminal reading forces 4 | n.
derivation: "the residue mod 4 is preserved by sign flips" (stated, with no
  reference to the width-4 cyclic window-product structure).
```

Check-by-check (against E7 contract):
- C1 (observable derived from move constraints): **FAIL** — the derivation states preservation
  without citing the `FlipSign` move family / the width-4 cyclic window-product structure it was
  derived from; the observable is asserted, not shown to be generated from the move set.
- C2 (preservation via the even-window argument): **PASS** (stated, though C1 is the binding failure).
- C3/C4/C5/C6: **PASS** (by construction the mock doesn't violate them).

Disposition: FAIL on **C1 only** → taxonomy `derivation-absent`. Only that label is triggered.

### E7-M5 — `preservation-unsupported`

Frozen blind-output artifact claims:
```text
observable: O = ResidueMod(S, 4), S = sum of a_i*a_{i+1}*a_{i+2}*a_{i+3}
move: FlipSign(state, position)
claim: O is invariant under FlipSign, terminal reading forces 4 | n.
derivation: "a sign flip negates the four products it sits in, so the sum
  changes by an even amount and the residue mod 4 is preserved." (No
  statement that the four products' partial sum is even.)
```

Check-by-check:
- C1 (derived from move constraints): **PASS** — cites the FlipSign move family and width-4
  structure.
- C2 (preservation via the even-window argument: `ΔS = −2(p1+p2+p3+p4)` with `p1+...+p4` even,
  so `ΔS ∈ {−8,−4,0,4,8}`): **FAIL** — the derivation asserts "changes by an even amount" without
  the `−2·(four-product sum)` even-window step that makes `ΔS` a multiple of 4; it does not
  discharge the preservation obligation with the required argument (nor does it carry an odd-width
  control, which is C4).
- C4 (odd-width negative control): **PASS**-by-absence? No — the contract requires the odd-width
  control; if it also fails here it folds into the same `preservation-unsupported` label. To keep
  it single-label, this mock **does** emit the width-3 control but still fails C2. So C4 PASS,
  C2 FAIL.
- C3/C5/C6: **PASS**.

Disposition: FAIL on **C2 only** → taxonomy `preservation-unsupported`. Only that label triggered.

### E7-M6 — `constant-injection`

Frozen blind-output artifact claims:
```text
observable: O = ResidueMod(S, 4), S = sum of a_i*a_{i+1}*a_{i+2}*a_{i+3}
move: FlipSign(state, position)
claim: O invariant; terminal forces 4 | n.
derivation: "the reference weights (1,-1,1,-1,1,-1) are supplied as the
  observable coefficients and preserved under the move."
```

Check-by-check:
- C1/C2/C3/C4/C5: **PASS** — the observable is otherwise correctly derived/preserved/separating.
- C6 (no E7 weights in training inputs or implementation constants): **FAIL** — the reference
  weights `(1,-1,1,-1,1,-1)` are supplied as an input constant.

Disposition: FAIL on **C6 only** → taxonomy `constant-injection`. Only that label triggered.

### E3-M (constant-injection, alternate) — placement note

The E3 contract does **not** define a separate taxonomy string in its text (unlike E4/E7); its
C1–C6 all funnel to either preservation/separation/derivation or injection. The operator's six
labels are fully covered by the E4/E7 mocks. A **passing** E3 mock is provided below; no separate
E3 failing mock is needed to cover a distinct label, since `constant-injection` (C6) is already
covered by E7-M6 and the E3 C6 semantics are identical. (Recorded to avoid a duplicated fixture.)

---

## PASSING MOCKS — one per contract

### PASS-E3

Frozen blind-output artifact claims (E3, six-sector alternating sum):
```text
observable: R = sum_{i=1..6} w_i * a_i,  w = (1,-1,1,-1,1,-1)
move: add +1 to two neighboring entries (move family 12,23,34,45,56,61)
derivation:
  - generated from move constraints: need w_i + w_{i+1} = 0 cyclically -> w = (c,-c,...); c=1.
  - preservation: Delta R = w_i + w_{i+1} = 1 + (-1) = 0.
  - start/target separation: R(1,0,1,0,0,0) = 2; R(0,0,0,0,0,0) = 0 -> different, so
    all-equal is unreachable.
  - odd-cycle (n=5) control emits NoNonzeroExactLinearObservable(move_family).
  - removing the weighted generator removes the candidate.
  - no E3 weights supplied as training input or constant.
classification: PRESERVED_AND_SEPARATING.
```
Check-by-check: **C1 PASS, C2 PASS, C3 PASS, C4 PASS, C5 PASS, C6 PASS** → verdict PASS.

### PASS-E4

Frozen blind-output artifact claims (E4, descent under max degree ≤ 3):
```text
monovariant: H = # same-house enemy edges
given: max degree <= 3 (each member has at most 3 enemies)
move: relocate a member with enemies_in >= 2 to the other house
derivation:
  - two houses, so delta H = e_out - e_in.
  - under the bound, e_in + e_out <= 3 and legality e_in >= 2 -> e_out <= 1, so
    Delta H <= -1 for every legal move.
  - H is a non-negative integer and strictly decreases, so termination in at most H_0 moves.
  - termination yields "no legal move", NOT a global minimum (4-cycle dual terminals exist).
classification: CORRECT (descent, bounded-below termination).
```
Check-by-check: **C1 PASS, C2 PASS, C3 PASS, C4 PASS, C5 PASS, C6 PASS** → verdict PASS.

### PASS-E7

Frozen blind-output artifact claims (E7, width-4 mod-4 residue):
```text
observable: O = ResidueMod(SumOfProducts(CyclicWindowProduct(state, width=4, offset=1..n)), 4, 0)
move: FlipSign(state, position)
claim: O invariant under FlipSign, terminal forces 4 | n.
derivation:
  - one flip sits in exactly width=4 distinct products (n >= 4).
  - the four affected products' partial sum s is even (each product is +/-1 in pairs),
    so Delta S = -2*s is a multiple of 4; ResidueMod(S,4) unchanged.
  - start residue 0 differs from target residue n mod 4 whenever 4 !| n -> separating.
  - odd-width controls emitted (width=3 gives Delta S = 2 mod 4, not preserved).
  - rejected candidates correctly classified: sum a_i (not invariant), prod a_i (not invariant),
    Parity(S) (preserved-but-non-separating).
classification: PRESERVED_AND_SEPARATING.
```
Check-by-check: **C1 PASS, C2 PASS, C3 PASS, C4 PASS, C5 PASS, C6 PASS** → verdict PASS.

---

## Expected-verdict summary

| mock | contract | unmet check | taxonomy label (only) |
|---|---|---|---|
| E4-M1 | E4 | C1 | `hypothesis-omitted` |
| E4-M2 | E4 | C3 | `descent-unsupported` |
| E4-M3 | E4 | C5 | `overclaim` |
| E7-M4 | E7 | C1 | `derivation-absent` |
| E7-M5 | E7 | C2 | `preservation-unsupported` |
| E7-M6 | E7 | C6 | `constant-injection` |
| PASS-E3 | E3 | — | PASS |
| PASS-E4 | E4 | — | PASS |
| PASS-E7 | E7 | — | PASS |

Every failing mock triggers **exactly one** taxonomy label and no other (by construction: the
single unmet check falls in exactly one label's check-set, and the remaining checks pass). Every
passing mock passes all six checks (PASS).

## Run / consumption note

These are fixture *inputs* for the grader, not a runtime harness. When an executable grader lands,
each mock should be fed through it and must produce the verdict above (single FAIL label, or PASS).
Until then, the fixtures stand as the expected classification oracle for the grader.

Docs-only; no production code, labels, Edge classes, packs, or G implementation touched.
