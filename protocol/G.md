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
objects; that fetch leaves only `FETCH_HEAD` updated. Recovery ritual (same sub-mode F-tools recorded
in its runbook):

```text
git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
git fetch --all --tags
# then reconcile: git reset --hard origin/arena/01a068c2-cat-theo-machine
#   only after confirming HEAD is an ancestor (fast-forward) — never a force-push
```

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
