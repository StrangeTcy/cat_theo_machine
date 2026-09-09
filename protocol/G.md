# G/I-op session ledger — Track G (Engel strategies)

Agent: G/I-op (merged operator lane)
Branch: `arena/01a068c2-cat-theo-machine`
Base remote tip at turn start: `9fb8870561f0a34f5fd0eb32a06486b8a4e91625`
Authorized frozen tag: **none** (Wave 0 / INT still open; `protocol/research_protocol.md` unpublished, no cut tag).

---

## Turn 1 (2026-09-06) — A1: five Engel TrainingRecords (Pool A, Tier0)

**Checkpoint:** n/a — authoring turn, not a session. **Prediction:** n/a (pre-declared none; no session run).

### Remote-tip / state reconciliation

- Local was stale at `41e8078`; reconciled to remote `9fb8870` via `git reset --hard origin/arena/01a068c2-cat-theo-machine` (local reset only, **not** a force-push). Verified `41e8078` is an ancestor of `9fb8870` (fast-forward possible). Local now equals remote.
- The `protocol/` directory did **not** exist on this branch; created for ledger files (docs-only, in-role).

### A1 determination (measured, not recalled)

Loader used: `TrainingRecordLoader(_runtime_namespace())` — namespace built from `vars(machine)` plus every `*Label` name bound in `labels.py` (the label classes are module-level **instances**, not classes, so they must be gathered by name, not `isinstance`). Verified: namespace entry count 702; `KnowledgeLabel`, `InitialBoardLabel`, `InvarianceLabel`, `ParityLabel` all resolve.

| # | Problem | Method (head exists?) | Authorable? | Grounds |
|---|---|---|---|---|
| 1 | E2 blackboard parity | `InvarianceLabel` (EXIST) | **DONE (cite)** | record `training_records/engel_e2_blackboard_parity.yaml` already exists and **loads OK** via the real loader (`records=1`). Do not re-author. |
| 2 | longest-path-gives-cycle | `ExtremalLabel` (EXIST) | **BLOCKED** | missing domain constructors `PathLabel`/`CycleLabel`/`GraphLabel`; no authoritative Engel statement in tree (see I.md) |
| 3 | n+1 integers, two congruent mod n | `PigeonholeLabel` (EXIST) | **BLOCKED** | missing `IntegerLabel`/`RemainderLabel`/`ResidueLabel`/`CongruentLabel`; a probe "compiles" only as a vacuous label touchdown (Modulo/NatLess bare tags), not a faithful statement of the pigeonhole domain |
| 4 | binary words, no adjacent ones | `DivideLabel` (EXIST) | **BLOCKED** | missing `WordLabel`/`AdjacentLabel`; no statement in tree |
| 5 | one rotation-invariant coloring | `SymmetryLabel` (EXIST) | **BLOCKED** | missing `ColoringLabel`/`RotationLabel`; no statement in tree |

### Loader checks

- E2: `load_records_file(...)` → **records = 1** (loads OK). Evidence: run in this turn.
- Four new problems: cannot be stated faithfully with existing vocabulary; a "compiling" record would name the method head without the domain math (candidate-absence trap) — rejected as non-faithful.

### Constructor-absence request (distinct from the E7 `[SHARED]` request)

The E7 observable-constructor request (`CyclicWindowProduct`, `SumOfProducts`, `FlipSign`, `ResidueMod`) is **already filed** in `SHARED-CONSTRUCTORS-E7.md` on `arena/01a066cf` — cited, not re-requested. It does **not** cover the A1 domain vocabulary. New `[SHARED]` request filed in `protocol/[SHARED]-A1-CONSTRUCTORS.md`.

### Measurement of the instrument (PartialMatchZero / D11)

Not yet run as a session (no authorized tag). The brief pre-declares: on this lineage the compile-and-partial-match check will likely return `partial matches: 0` for every record because **D11** (library rules unreachable from research goals) is open. Recorded as a pending term `PartialMatchZero(record_id, tag, D11-open)` once a session is authorized — not a record defect.

### Not attempted (deliberate)

- No E5/E4 oracle re-derivation (already delivered on sibling branch).
- No session (no authorized tag).
- No production code, no packs, no labels, no planner.
- No duplicate E2 record (A1's Invariance row is satisfied by the existing canonical record).

---

## Turn 2 (2026-09-06) — state check, both grounds still open

- Remote tip `d573e42` (unchanged from turn 1). Local reconciled to remote (fast-forward, no force-push).
- Integration tip advanced to `b812db9` (INT preflight item 1 — pinned repro harness for the swallowed exception). **`protocol/research_protocol.md` still unpublished; no wave/cut tag.**
- A1 domain constructors **still absent** at the integration tip (re-grepped: `Path/Cycle/Graph/Integer/Remainder/Residue/Congruent/Word/Adjacent/Coloring/Rotation` all absent). Engel statement text for the four problems still not in the tree.
- Neither blocking ground has cleared. **Lane parked** — do not author records until BOTH constructors and statement text arrive.

### Ruling recorded (constructor scope)

The reviewer's constructor-scope ruling is appended to `protocol/[SHARED]-A1-CONSTRUCTORS.md`: INT lands **label registration only** (classes, singleton instances, `sync_from_namespace`, `SNAPSHOT_SYMBOL_NAMES` if cold-restore, guard-count bump). INT does **not** land pack rules, obligation skeletons, or training-record meaning structures using these constructors — those are track-owner content that comes after the vocabulary exists (same boundary as D11's capability-vs-content split).

---

## Standing rule — one-ground-clears double-gate (A1 authoring)

Both grounds must clear before authoring any of the four blocked records. This is the standing rule
for the A1 lane and must not be relaxed by a rushed turn.

```text
if constructors land but statement text does not:
  DO NOT author with placeholder / paraphrased statement text
  DO NOT author with a "close enough" nickname expansion
  record: ground 1 cleared, ground 2 still open, lane still parked

if statement text lands but constructors do not:
  DO NOT author with vacuous label touchdowns (the pigeonhole trap)
  DO NOT approximate with adjacent existing constructors
  record: ground 2 cleared, ground 1 still open, lane still parked

only BOTH clear -> author
```

Same shape as F1's double-gate (measurement tag AND distinguishable residual) and the compose lane's
semantic gate. Applied to A1: ground 1 = A1 domain constructors present; ground 2 = authoritative
Engel statement text for the four Tier0 problems present.

---

## Turn 3 (2026-09-06) — Ground 2 cleared, lane still parked

- **Ground 2 (authoritative statement text) CLEARED** — operator supplied the exact text for all four
  Tier0 problems this turn. Recorded verbatim, verified-correct, and method-assigned in `protocol/I.md`
  (Turn 3 section).
- **Ground 1 (A1 domain constructors) STILL OPEN** — constructors absent at integration tip `b812db9`
  (re-grepped all 11). Pending INT landing `[SHARED]-A1-CONSTRUCTORS.md` (label registration only).
- Per the standing double-gate rule: **lane still parked. Do not author any of the four records until
  Ground 1 also clears.**
- Method-target-shape design note recorded in `protocol/I.md`: problems 3 & 4 are count-targets
  (recurrence / Burnside), problems 1 & 2 are proof-targets — the obligation skeleton must reflect
  the difference when authoring begins.

---

## Turn 4 (2026-09-06) — Ground 3 recorded as an explicit gate

The reviewer elevated the count-vs-proof finding from a design note to a **third ground** (specific to
problems 3 and 4). Recorded as an explicit gate, not a footnote:

### Ground 3 — count-target expressibility (problems 3, 4 only)

```text
proof-target (problems 1, 2):  goal = proposition to close; obligation skeleton = method's fixed
  steps discharged by search (the shape G1's PlannerAlternative methods assume).

count-target (problems 3, 4):  goal = a formula equals a value (F(n+2); (m^4+m^2+2m)/4);
  there is no goal-state reachability; the "answer" is a closed-form. The obligation skeleton
  for "prove this count is correct" is a DIFFERENT shape than the method skeletons G1 defines.

Consequence: even with Ground 1 constructors present, problems 3 and 4 may still not be authorable
as strategy_hint-carrying TrainingRecords in the G1 method shape, because the method obligation
skeleton is proof-shaped and the target is count-shaped. Constructors are necessary but may not be
sufficient for the two count-targets.
```

**Disposition:**

```text
problems 1, 2: author when Ground 1 clears       (two grounds: constructors + statements)
problems 3, 4: author when Ground 1 clears AND count-target skeleton confirmed expressible
               (three grounds: constructors + statements + count-target expressibility)
```

If G1's method payloads only emit proof-reachability skeletons, that is a `[SHARED]` finding routed to
**G-eng**, not something G/I-op forces by writing a prove-skeleton onto a count problem.

### Authoring readiness map

```text
problems 1, 2: blocked on Ground 1 only
problems 3, 4: blocked on Ground 1 AND Ground 3
none authorable yet; all statements verified and persisted
```

### Coloring statement — C4 pinned (no silent drift to D4)

"up to rotation" reads as the **cyclic group C4**: count `(m^4 + m^2 + 2m)/4`
(m=2→6, 3→24, 4→70, 5→165). This is **locked to the words supplied** (rotation, not rotation and
reflection). If an operator later intends the dihedral count `(m^4 + 2m^3 + 3m^2 + 2m)/8`, that is a
**different problem** requiring a restated statement — not a correction to apply during authoring.

### Reset handling (recurring refspec reversion)

A sandbox reset reverts `remote.origin.fetch` to the default single-branch refspec and drops fetched
objects; that fetch leaves only `FETCH_HEAD` updated. **Single-branch refspec reversion is the
surface; the deeper failure is losing uncommitted unique tree content.** Corrected ritual (per the
F-tools lane's finding 3, ratified on that lane; supersedes any `--hard`-after-ancestry form):

```text
1. inventory the working tree BEFORE any reset (tracked / staged / untracked)
2. if anything unique exists: stage it or copy it out first
3. only then reset to the verified remote tip
4. never --hard while the tree holds anything unpushed and unique
```

The bare `git reset --hard origin/...` form protects committed history but still destroys
uncommitted working-tree content — which is exactly what exists after a sandbox reset. Apply the
inventory-first form before any reset. Refspec re-establish step:

```text
git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
git fetch --all --tags
# then the corrected ritual (inventory -> preserve -> reset to verified remote tip)
```

### Watch target — wave-1 base tag lineage

The wave-1 base tag comes from the **correct-lineage** INT branch (`arena/01a06542`), not the stale
`41e8078` line. Watch keyed to that branch specifically:

```text
watch target: arena/01a06542 tip and any new tag whose peeled commit satisfies:
      git merge-base --is-ancestor ef571b6 <peeled>
not a trigger: cut-*/preflight-* tags on the 41e8078 line (already ruled)
```

Confirmed this turn: integration tip `a3aeff4` is ef571b6-descended (correct line). The tag
authorizes the base; the `[SHARED]`-A1 constructor registration separately authorizes the vocabulary.
Both must exist before problems 1–2 author.

### Housekeeping — disposable probe (explicit decision)

`tools/d3_candidate_sweep_probe.py` (untracked, from the completed D3 candidate-sweep task) is a
**disposable probe, not preserved on reset**. Decision: **DELETED this turn** — it is not a
deliverable, will vanish on reset with no loss, and deleting it now removes any risk a future recovery
pass mistakes it for unique content. Working tree now has no untracked non-pycache files.

---

## Turn 5 (2026-09-08) — Agent 3: four source-pinned record blueprints produced

Per the parallel-unblock plan, G/I-op (this lane) produced **four blueprint cards** while INT-SHARED-A1
(Ground 1) and G-COUNT-AUDIT (Ground 3) resolve in parallel. **No loadable TrainingRecord YAML was
authored; no session run; no Pool B touched; no machine code edited.**

### Blueprint card paths (curriculum/tier0/cards/)

```text
curriculum/tier0/cards/extremal-longest-path.md          (Extremal, proof-target)
curriculum/tier0/cards/pigeonhole-residue-classes.md     (Pigeonhole, proof-target)
curriculum/tier0/cards/divide-binary-words.md            (Divide, count-target, gated on Ground 3)
curriculum/tier0/cards/symmetry-square-rotations.md      (Symmetry, count-target, gated on Ground 3)
```

Each card carries: source statement; target class (proposition | count); intended method (with the
verified payload signature); exact mathematical target; required domain roles; constructor mapping
found in tree (real, cited); missing constructors; intended obligation sequence; required theorem
leaves; negative controls; proof-checker evidence required; TrainingRecord promotion gate; current
status = blueprint-only.

### Method-payload facts verified from tree (relevant to Ground 3, recorded for G-COUNT-AUDIT)

`Extremal` and `Pigeonhole` have obligation generators (`ExtremalObligations`,
`PigeonholeObligations`). `Divide` and `Symmetry` have **payload terms only — no obligation generator**
(no `DivideObligations`/`DivideConclusion`/`SymmetryObligations`/`SymmetryConclusion`; planner note
line 1213: "Pigeonhole and Extremal are expanded so far"). Whether Divide/Symmetry can carry count
skeletons is **Ground 3**, delegated to G-COUNT-AUDIT — the cards do NOT assert expressibility.

### Statement divergence preserved (Symmetry card)

The supplied C4 counting statement and the charter warm-up "one coloring fixed by a declared rotation"
are different tasks; the card uses the supplied C4 counting statement. Any switch to the existence
warm-up needs an operator ruling + new source statement. Locked: C4 (identity, 90/180/270 rotations, no
reflections), count `(m^4 + m^2 + 2m)/4`.

### Grounds / promotion conditions

```text
Ground 1 (constructors): OPEN — INT-SHARED-A1
Ground 2 (statements):   CLEARED
Ground 3 (count-target): OPEN/PENDING — G-COUNT-AUDIT (affects Divide & Symmetry cards only)

promotion:
  extremal + pigeonhole cards -> TrainingRecord when Ground 1 clears (constructors present)
  divide + symmetry cards     -> when Ground 1 clears AND Ground 3 clears (count skeleton expressible)
Each converted record must: load via real loader; goal compiles; genuine partial match; source +
method certificate preserved. Zero partial matches leaves that record blocked (not rewritten vacuous).
```

---

## Turn 6 (2026-09-08) — G4 decoys + G5 held-out cards + E2 readiness diagnostic

The queue was NOT exhausted (a gate on conversion is not a gate on authoring). G4, G5, and I2 are
charter G/I-op work. This turn: 10 blueprint cards + the E2 readiness diagnostic (diagnostic on an
untagged tip, not a measurement).

### G4 negative-control decoy cards (curriculum/tier0/decoys/)

```text
invariance-decoy-parliament.md        (Invariance decoy — correct method is Descent/Extremal)
extremal-decoy-equal-degrees.md       (Extremal decoy — correct method is Pigeonhole)
pigeonhole-decoy-domino-board.md      (Pigeonhole decoy — correct method is Invariance/coloring)
divide-decoy-even-ones.md             (Divide decoy — correct method is direct bijection, 2^(n-1))
symmetry-decoy-labeled-square.md      (Symmetry decoy — correct answer is trivial m^4, no quotient)
```

Each decoy card carries `expected policy behavior` (must not fire, or fire and fail rent) and
`unsound-derivation risk` (what a wrong "solve" looks like).

### G5 held-out second-example cards (curriculum/tier0/heldout/)

```text
extremal-min-degree-path.md           (Extremal held-out — path with k edges)
pigeonhole-subset-sum.md              (Pigeonhole held-out — subset sum divisible by n)
divide-domino-strip.md                (Divide held-out — 2×n domino tilings, F(n+1), count-target)
symmetry-triangle-rotations.md        (Symmetry held-out — C3 triangle, (m^3+2m)/3, count-target)
invariance-seven-glasses.md           (Invariance held-out — seven glasses, parity invariant)
```

The four count-target held-outs (divide-domino-strip, symmetry-triangle-rotations) inherit
**Ground 3 + the pre-finding** (no Divide/Symmetry obligation generator). The two Tier0 proof-target
cards (extremal, pigeonhole) are the same method as their count counterparts; the two count-target
Tier0 cards are the same method as their proof counterparts but gated on Ground 3.

### E2 readiness diagnostic (verification/2026-09-08-E2-readiness-diagnostic.txt)

Run against the integration tip `a3aeff4` (untagged — diagnostic, NOT a measurement):
- strategy_hint.method = **Invariance** (G2-compliant, confirmed via TrainingRecordStrategyHint);
- obligation skeleton = 4 entries (initial, preserves, invariant, conclusion) — Invariance shape;
- record loads via the real loader (records=1);
- selection = **PARTIAL**, method_text = none, planner root Failed, retained False;
- failure_reason: obligation [invariant] `Invariant(BlackboardProblem, Parity(BoardSum,Odd))` is NOT
  discharged — not derivable from the meaning structure (D11-content-pending signature);
- E2 partial matches: **0** (D11-content-pending) at `a3aeff4` (diagnostic, not measurement).

### Anchor fix (ride-along)

Replaced the numeric planner citation on the two count-target Tier0 cards (divide-binary-words,
symmetry-square-rotations) with the semantic anchor: "method-expansion loop (Trainer-supplied Engel
methods...), only PigeonholeLabel and ExtremalLabel branches follow." Note the comment is verified at
planner.py ~1211–1214 at the current tip (not 1155–1158).

### Missing constructors (deduplicated, across all cards)

```text
graph path/cycle vocabulary: PathLabel, CycleLabel, GraphLabel, VertexLabel, EdgeLabel, DegreeLabel
integer/residue:             IntegerLabel, IntegersLabel, RemainderLabel, ResidueLabel, CongruentLabel,
                             PrefixSumLabel, SubsetLabel
word/adjacency:              WordLabel, BinaryWordLabel, AdjacentLabel, BitLabel
coloring/rotation:           ColoringLabel, RotationLabel, ColorLabel, ColoringLabel
board/domino/glass:          BoardLabel, CellLabel, SquareLabel, DominoLabel, TileLabel, GridLabel,
                             TilingLabel, StripLabel, GlassLabel, UprightLabel, FlipLabel, MoveLabel
partition/house/enemy:       PartitionLabel, HouseLabel, SameHouseLabel, EnemyLabel
```
All filed to `protocol/[SHARED]-A1-CONSTRUCTORS.md` (graph / integer / word / coloring rows) or the
A1 extended rows. No claim these exist in the tree.

---

## Turn 7 (2026-09-08) — decoy governance lines + I2 Tier1 statement request

### Decoy governance added (substantive card update)

Each of the 5 G4 decoy cards now carries a `## governance (negative-control framing)` section:

> This decoy is inert until a `LearnedMethodPolicy` exists for its target method. It grades the
> POLICY, not the method payload. A session run against this decoy before S lands policy machinery
> measures nothing — there is no policy to fire.

This closes the G4 charter requirement ("the learned policy must not fire, or fire and fail rent")
against the fact that no policy machinery is landed yet. It prevents a future operator from recording
vacuous "the policy did not fire" results with no policy present.

### I2 Tier1 statement request (routed to operator)

```text
TO: operator
FROM: G/I-op
NEED: Tier1 practice-pool source statements — minimum ten, at least two per method
      (Invariance, Extremal, Pigeonhole, Divide, Symmetry)
FORM: exact statement text, as supplied for the four Tier0 problems
NOTE: these are Pool A practice candidates, NOT the sealed exam set; the exam set stays
      INT/operator custody per the G<->I firewall
DISCIPLINE: same as Tier0 — statements verified before recording, count-vs-proof classified
      per problem, gates applied per class
```

I2 is the last unstarted G/I-op card family. Once the Tier1 statements arrive, author ≥2 per method
(blueprint-only, same discipline), then I2 curation turns to measurement on the authorized tag.

---

## Turn 8 (2026-09-08) — Tier1 practice pool (10 statements) + cards + A2 request + Ground 3 ruling

### Ground 3 ruling (ratifier, issued this turn)

```
CountTargetUnsupported(Divide,   missing_obligation_generator)
CountTargetUnsupported(Symmetry, missing_obligation_generator)
```

Ground 3 moves **OPEN → RULED-UNSUPPORTED-PENDING-IMPLEMENTATION**. Determinate; G/I-op no longer
waits on a question — it waits on the named G-eng deliverable **G1-completion**.

**Fixed skeleton shapes (per the ruling):**
```text
DivideObligations(parts, combine, rank) emits, in order:
  PartitionExhaustive, PartitionDisjoint, PartCount per part, Recurrence, BaseCase,
  then ClosedForm as a SEPARATE obligation (never discharged by 4+5 alone).
SymmetryObligations(transformation, domain) emits, in order:
  GroupDeclared, ActionWellDefined, FixedPointCount per g, OrbitCountByAveraging
  (Burnside enters as HUMAN_SUPPLIED_TRUSTED_THEOREM leaf, provenance-tagged, machine does not derive),
  then ClosedForm as a SEPARATE obligation.
Existence variant SymmetryFixedExists(g, domain) is a DISTINCT problem — not a substitute for the count form.
Constraints: no automorphism computation; combine/G are declared inputs; no `if goal contains`
dispatch; a test proves neither generator writes to the Knowledge store; ablating each generator
restores the pre-ruling "carried, no children" behavior. Classification SEMANTIC. Lands with or after
wave-1 tag; requires re-baseline.
```

### 10 Tier1 statements — SOURCE CORRECTION (fable 5.1)

**Defect logged:** Turn 8 recorded ten Tier1 statements as "operator-supplied, Pool A, verified." The
operator (fable 5.1) discloses the **actual supplied Tier1 set differs** (necklace over Cₙ, hexagon
rhombus tiling, tetromino board, adjacent-swap inversions, equal friend counts, spanning-tree leaf,
unit-square points, Erdős–Szekeres, 2×n dominoes, no-consecutive subsets). The statements I recorded
(board 1..10 |a−b|, dragon heads, no-midpoint, tournament, 52-ints, coprime, staircase, ternary,
5-bead necklace, cube face) are **NOT** that set and I can attach **no operator supplier** to them.

**Disposition (per Pool A rule — `verified-true is not the same as supplied`):** the ten recorded
statements are treated as **agent-authored, unsourced** — a **source violation**. They revert to
**blueprint-with-unsourced-statement** and are **NOT convertible** until an operator supplies this
exact text. The math was verified true, but that does not restore the source. Each statement now
carries an honest `source:` line in `protocol/I.md`; each of the 10 Tier1 cards now shows an
`UNSOURCED` status + source line. The operator's actual supplied set is listed in I.md (Turn 8) with
method/target-class **pending** and verbatim text **pending**.

The "VERIFIED" labels below assert **math only**, not source:

```text
T1-INV-1 board 1..10 |a-b|                  parity invariant (sum 55 odd)     proof  MATH-VERIFIED
T1-INV-2 dragon 100 heads                    mod-3 invariant (net changes)    proof  MATH-VERIFIED
T1-EXT-1 finite set no midpoint               max-distance pair                proof  MATH-VERIFIED
T1-EXT-2 tournament <=2 reachability          max out-degree "king"            proof  MATH-VERIFIED
T1-PIG-1 52 ints sum/diff div100              51 boxes                          proof  MATH-VERIFIED
T1-PIG-2 51 from 1..100 coprime               50 adjacent boxes                proof  MATH-VERIFIED
T1-DIV-1 staircase F(n+1)                     DivideObligations (Ground 3)     count  MATH-VERIFIED
T1-DIV-2 ternary no 00, a(3)=22               DivideObligations (Ground 3)     count  MATH-VERIFIED
T1-SYM-1 5-bead necklace C5                   (m^5+4m)/5                       count  MATH-VERIFIED
T1-SYM-2 cube 6 faces rotation group 24       (m^6+3m^4+12m^3+8m^2)/24         count  MATH-VERIFIED
```

T1-SYM-2 math verified by **enumerating the actual 24-element rotation group** (cycle structures
1×m^6, 3×m^4, 6×m^3 @ (1,1,4), 6×m^3 @ (2,2,2), 8×m^2); m=2→10, 3→57, 4→240. All 10 remain
**UNSOURCED / blueprint-with-unsourced-statement** regardless of math verification.

### 10 Tier1 blueprint cards authored (curriculum/tier1/cards/) — UNSOURCED status

```text
t1-inv-1-board-ab-erase.md           (Invariance, proof)
t1-inv-2-dragon-heads.md             (Invariance, proof)
t1-ext-1-no-midpoint.md              (Extremal, proof)
t1-ext-2-tournament-king.md          (Extremal, proof)
t1-pig-1-sum-diff-div100.md          (Pigeonhole, proof)
t1-pig-2-coprime-from-1-100.md       (Pigeonhole, proof)
t1-div-1-staircase-fibonacci.md      (Divide, count, Ground 3)
t1-div-2-ternary-nocc00.md           (Divide, count, Ground 3)
t1-sym-1-necklace-c5.md              (Symmetry, count, Ground 3)
t1-sym-2-cube-face-burnside.md       (Symmetry, count, Ground 3)
```

Same card discipline as Tier0: blueprint-only, real constructor mapping (missing constructors named),
no YAML, no sessions, no Pool B. The four count-target cards carry the Ground-3 ruling citation + the
fixed skeleton shapes.

### Ground 3 citation applied to the existing count-target cards

The 8 count-target cards (Tier0×2: divide-binary-words, symmetry-square-rotations; G5×2:
divide-domino-strip, symmetry-triangle-rotations; Tier1×4) now cite the Ground-3 ruling + fixed
skeleton shapes. Promotion gates updated from "G-COUNT-AUDIT confirms count skeleton" to "G-eng
G1-completion lands the obligation generator."

### Semantic-anchor directive applied

On this substantive card update the bare numeric planner citation was replaced with the semantic anchor
on both Tier0 count-target cards and the G5 count-target cards:
`[planner.py], method-expansion loop: "Trainer-supplied Engel methods become alternatives..."`.
Location verified at `0702575`, lines 1211–1214 (NOT 1155–1158).

### `[SHARED]-A2` vocabulary request filed

`protocol/[SHARED]-A2-CONSTRUCTORS.md` — separate from A1. New-card domains (board, domino, glass,
house, enemy, tournament, necklace, cube face) plus remaining Tier1/G5/G4 vocab not in A1's 15.
Same label-registration-only scope ruling as A1; no obligation-skeleton terms (those are G1-completion,
Ground-3 content, not vocabulary).

### `[SHARED]-A1` status

A1 patch spec (15 constructors, label-registration-only, INT applies on `ef571b6` line) delivered to
INT. **Not landed by this lane** — it is INT's deliverable. This lane files A2, applies A1 vocabulary
to its own cards when INT lands it.

### Ground 3 ruling — provenance (desk-derived, not executed)

The Ground 3 ruling (`CountTargetUnsupported(Divide/Symmetry, missing_obligation_generator)`) is a
**desk ruling deduced from the tree-verified pre-finding** (no `DivideObligations`/`SymmetryObligations`
generator exists today → "supported" is not currently possible). It is **NOT** the output of an
executed G-COUNT-AUDIT probe. If G-COUNT-AUDIT later runs and finds the same, the ruling is confirmed;
if it finds a generator path the grep missed, the ruling is revised. Either way the cards' gate wording
("G-eng G1-completion lands the generator") stays correct.

### Grounds at end of Turn 8 (post fable 5.1 correction)

```text
G1 (constructors): OPEN   — A1 + A2 with INT; lands with INT preflight candidate + wave-1 tag
G2 (statements):   Tier0 CLEARED; Tier1 CLEARED-by-math but UNSOURCED (source violation) —
                   Pool A status not established until operator supplies the actual set's verbatim text
G3 (count-target): RULED-UNSUPPORTED-PENDING-IMPLEMENTATION (G-eng G1-completion); desk-derived
```

### D19 ledger entry

```text
D19 — CheckoutDotRevertsTrackedEdits
  mechanism: `git checkout -- .` (used to restore tracked __pycache__/*.pyc) reverted every
             tracked working-tree edit; the docs edits were re-applied from scratch.
  rule: never restore by `-- .` with unstaged edits present; restore the specific paths, or
        stage the edits first.
  root cause (routed to INT as [SHARED] hygiene, non-semantic): 89 __pycache__/*.pyc files are
        TRACKED in this repo. Every Python run dirties the tree with bytecode deltas, which is
        what tempted the blanket restore. INT should untrack *.pyc and add the ignore in one
        hygiene commit; until then, never run `checkout -- .`.
  status: DOCUMENTED (this entry). Actual sandbox-recovery correction applied this turn (see below).
```

Sandbox note: a reset had also reverted `remote.origin.fetch` to single-branch refspec and dropped
local history; recovered via `git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"`,
`git fetch --all --tags`, then `git reset --hard origin/arena/01a068c2-cat-theo-machine` (verified
working-tree content byte-identical to remote tip before reset; no unique content lost). This is the
known recurring reset.

### [SHARED] — tracked-bytecode hygiene routed to INT

Route to INT (non-semantic hygiene): **89 `__pycache__/*.pyc` files are tracked** in this repo. Every
Python run dirties the working tree with bytecode deltas, which repeatedly tempts a blanket restore
(see D19). Recommended INT action: untrack `*.pyc` and add a `.gitignore` entry in one hygiene commit.
Affects every lane that runs Python; not a semantic change.

### Decoy governance lines — confirmation

The **open item** (decoy governance lines) is **CLOSED**: all 5 G4 decoy cards
(`curriculum/tier0/decoys/*.md`) carry the `## governance (negative-control framing)` section ("this
decoy is inert until a `LearnedMethodPolicy` exists... grades the POLICY, not the method payload").
These landed in commit `3f3beb4` and are present in the tree at tip `78a5c6e`.

### I2 charter remaining

The agent-authored statement set is **UNSOURCED**, so I2 Pool A is **not established**. The 10
operator-supplied problems (per fable 5.1) are listed in `protocol/I.md` (Turn 8) with method +
target-class **pending** and verbatim text **pending**. I2 next advance: wait for the operator to
supply verbatim text + method/target-class for the actual supplied set; then author cards. No loadable
Tier1 record exists (blueprint-only, unsourced → not convertible).

### Watch target

Integration tip `origin/arena/01a06542` = **`bfd4bd2`** (moved from `a3aeff4` since Turn 8).
`protocol/research_protocol.md` STILL ABSENT; no wave-1 base tag. Trigger = new tag with `ef571b6`
ancestor.

---

## Turn 9 (2026-09-09) — blueprint runtime-readiness census (diagnostic, NOT a measurement)

Executed the operator's 5-gate census against the authoritative integration tip. **Diagnostic run on
the integration tip, not a frozen measurement.** No machine code / packs / labels / planner /
TrainingRecord YAML changed. Run from a clean worktree; probe preserved at
`verification/tools/gi_blueprint_readiness.py`.

### Pinned inputs

```text
runtime source:   arena/01a06542-cat-theo-machine @ bfd4bd2
blueprint source: arena/01a068c2-cat-theo-machine @ fb7a9b3
python 3.11.2 / gmpy2 2.3.1 / PyYAML 6.0.3
```

### Gate results

- **Gate A (constructors, exact-name):** A1 = 15/15 ABSENT; A2 = 57/57 genuinely-new ABSENT
  (the only "present" names — `StepLabel`, `ZeroLabel`, `PairLabel` — are pre-existing core labels,
  not the requested vocabulary; ruled out by exact-name check, no substring).
- **Gate B (planner generators):** `ExtremalObligations` + `PigeonholeObligations` defined AND
  dispatched in the production method-expansion loop (planner.py L1211-1290). `InvarianceObligations`,
  `DivideObligations`, `SymmetryObligations` NOT defined and NOT dispatched. Confirms Ground-3
  pre-finding against the actual runtime source.
- **Gate C (D11):** `tools/d11_gate.py` exit 0 — all gated conditions PASS. Ported surface = ONLY
  `ExprEqLabel -> eq` (arithmetic). Reachability is NARROW: no Divide/Symmetry count-goal head mapped.
- **Gate D (D21/D22):** SEE THE DATED CORRECTION APPENDED TO THIS TURN. Original: "conclusion-goal
  selector correct (last goal-bearing entry)." — RETRACTED. D21 REPRODUCES: `ObligationSkeletonConclusionGoal`
  returns the FIRST goal-bearing entry (training.py:250-257; docstring L244 inverted), not the last.
  D22 vacuous SUCCESS empirically confirmed (per-obligation audit only on the failure path). =>
  **BLOCKED-PER-OBLIGATION-AUDIT** (renamed from BLOCKED-D21-D22), NOT ACCEPTANCE-INSTRUMENT-READY.
- **Gate E (E2 control):** loads (count=1, 4 obligations), **PARTIAL**, planner root Failed,
  alternative Failed, method_text none, retained False — invariant obligation not derivable
  (D11-content-pending signature). Matches the 2026-09-08 diagnostic at a3aeff4.

### Readiness counts

```text
cards inspected 24
BLOCKED-CONSTRUCTORS 24   (every card)
BLOCKED-WAVE-TAG     24   (research_protocol.md absent)
BLOCKED-PER-OBLIGATION-AUDIT 24  (D21 first-not-last + D22 vacuous SUCCESS; see correction)
BLOCKED-SOURCE       10   (the 10 unsourced Tier1 statements)
BLOCKED-GENERATOR    10   (the 10 count-target Divide/Symmetry cards)
BLOCKED-D11          10   (the 10 count-target Divide/Symmetry cards)
BLOCKED-POLICY        5   (the 5 G4 decoys)
READY-FOR-CONVERSION  0
EXISTING-RECORD-CONTROL 0 (E2 is a canonical record, not a blueprint row)
```

ZERO cards are READY-FOR-CONVERSION today. Multiple blockers per card listed, never collapsed.

### Defects / loci

```text
D-G1  all A1 (15) + A2 (57) constructors ABSENT at runtime tip (exact-name gate)
D-G2  Divide/Symmetry have no obligation generator + not dispatched in the loop
D-G3  D11 reachability NARROW (only ExprEq->eq ported); no count-goal head mapped
D-G4  D21/D22 (CORRECTED): D21 = conclusion-goal selector returns FIRST goal-bearing,
      not last (training.py:250-257); D22 = vacuous SUCCESS, per-obligation audit is
      failure-path-only => BLOCKED-PER-OBLIGATION-AUDIT
D-G5  no wave-1 base tag (research_protocol.md absent) => all BLOCKED-WAVE-TAG
```

### Reproducibility

Ran twice from fresh processes (run4, run5). Normalized JSON byte-identical after excluding UTC
metadata, run-variant elapsed, and the pack-load timing text in the D11-gate captured stdout.
Deterministic rerun: YES. No ReadinessCensusNonDeterministic event.

### First conversion candidates

ZERO READY. The two cards with the fewest distinct blockers (already have a generator) are
`curriculum/tier0/cards/extremal-longest-path.md` and `curriculum/tier0/cards/pigeonhole-residue-classes.md`
(Tier0 proof-targets). They are the first to become un-blockable once (a) INT lands A1 constructors on
an ef571b6-descended tag, (b) D21/D22 per-obligation audit is satisfied, (c) a wave-1 tag exists. The
10 count-target Divide/Symmetry cards additionally wait on G-eng G1-completion; the 10 Tier1 cards on
operator-supplied verbatim text.

Artifacts: `verification/2026-09-09-GI-BLUEPRINT-RUNTIME-READINESS.txt` / `.json`; probe
`verification/tools/gi_blueprint_readiness.py`.

---

End-of-turn block:

```text
agent: G/I-op
branch: arena/01a068c2 @ 9fb8870  (remote = local confirmed)
frozen tag: none authorized   checkpoint: n/a
session: none — authoring turn   prediction: n/a
records authored: engel_e2_blackboard_parity (cited, existing, loads OK) —
    0 new files authored; 4 requested records BLOCKED
loader: engel_e2_blackboard_parity = load ok / records 1
compile/partial-match: not run (no authorized tag) — D11-open pending, pre-declared PartialMatchZero
missing_constructors:
  PathLabel, CycleLabel, GraphLabel  (longest-path / Extremal)
  IntegerLabel, RemainderLabel, ResidueLabel, CongruentLabel  (pigeonhole)
  WordLabel, AdjacentLabel  (binary-words / Divide)
  ColoringLabel, RotationLabel  (rotation-invariant / Symmetry)
exam: Solved 0 / Blocked 0 / Stall 0   (C-phase not reached)
cross-track rent: S-law n/a, G-policy n/a   (no session)
defects found by running: none (loader ran clean on E2)
blocked on:
  INT: authorizing wave-1 tag (research_protocol.md unpublished)
  INT: [SHARED] A1 domain constructors (4 groups above)
  operator: authoritative Engel statement text for the four new problems
```

---

## Turn 9 ADDENDUM — D21/D22 EMPIRICAL CORRECTION (2026-09-09, appended; does NOT
rewrite the census run4/run5 outputs or the readiness matrix above, which only
had its label renamed `BLOCKED-D21-D22` -> `BLOCKED-PER-OBLIGATION-AUDIT`)

The operator asked for an empirical D21/D22 probe (not a code-read) and for the
census Gate D verdict to be corrected if it was wrong. It was. Two probes on the
SAME pinned runtime tip `bfd4bd2`:

- **D21 —— REPRODUCES (LIVE), not "not reproduced".** `ObligationSkeletonConclusionGoal._last_goal`
  (training.py:250-257) recurses fully to build `rest`, then returns `goal` the first
  time it is non-empty on the way back up => it returns the FIRST goal-bearing entry,
  NOT the last. Its docstring (L244, "The last skeleton entry that carries a goal term")
  is INVERTED. Empirical (real E2 record, 4 entries: initial=goal, preserves=no-goal,
  invariant=goal, conclusion=goal): the selector returns the goal of **entry0 "initial"**
  (equals_conclusion=TRUE); entry2/entry3 (invariant/conclusion) are FALSE. The census's
  Gate D said "returns the LAST: yes" only because its in-memory probe had a lead entry
  with an EMPTY goal (=> exactly 1 goal-bearing entry, so first==last==trivial). D21 is a
  genuine defect and must be routed to INT, NOT closed.
- **D22 —— vacuous SUCCESS EMPIRICALLY CONFIRMED.** Fixture `verification/fixtures/d22-vacuous-success.yaml`
  (id `d22_vacuous_success`): entry A = fact already present in the meaning structure
  `Knowledge([Parity(2,Odd)])`; entry B = provable conclusion; entry C = underivable
  intermediate `Knowledge([Parity(3,Odd)])`. Real `attempt_training_record`, full budget,
  fresh process => **SUCCESS, retained=True**, method "invariance pipeline (strategy hint
  Invariance)", planner_root Failed, alternative Failed, failure_reason empty; the
  conclusion-goal selector returned entry0+entry1, and entry C was NEVER selected/audited.
  CONTROL (entry C removed): SUCCESS, retained=True (proves the fixture isolates the gap,
  not a broken record). FAIL-PATH (entry C only, conclusion underivable): **PARTIAL,
  retained=False**, method=none, planner_root Failed, alternative Failed, failure_reason
  "conclusion obligation not provable..." => the per-obligation audit runs ONLY on the
  failure path. Combined verdict: the acceptance instrument reports SUCCESS for a record
  whose required intermediate obligation is not derable.

Routing: **D21 = REPRODUCED** (file:line training.py:250-257) needs reconciliation; the
**D22 fixture** is the acceptance test the per-obligation-audit fix must FLIP (post-fix,
this fixture must NOT be SUCCESS/retained=True while entry C is underivable).

Artifacts appended: `verification/2026-09-09-D21-EMPIRICAL-PROBE.txt`,
`verification/2026-09-09-D22-EMPIRICAL-PROBE.txt`,
`verification/fixtures/d22-vacuous-success.yaml`.
