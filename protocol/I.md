# G/I-op session ledger — Track I (IMO problems as the exam)

Agent: G/I-op (merged operator lane)
Branch: `arena/01a068c2-cat-theo-machine`
Base remote tip at turn start: `9fb8870561f0a34f5fd0eb32a06486b8a4e91625`

---

## Turn 1 — Pool split + statement-availability finding

### Pool discipline (per brief)

```text
Pool A (author):  Tier0 Engel TrainingRecords + Tier1 PRACTICE formalizations.
                  Used for curriculum sessions. Never held out. Lives in the repo.
Pool B (sealed):  the EXAM. Authored by the human operator outside the repo.
                  Only its SHA-256 lands in protocol/I.md. Problems handed to me
                  one at a time at I3 time, strategy_hint empty. Never seen whole.
```

This file (protocol/I.md) records only Pool A authoring and pool discipline. The pool B SHA-256 placeholder is reserved; I never author pool B.

### Statement-availability finding (A1)

The brief names five Engel problems. For **E2 (blackboard parity)** the authoritative statement and the loadable record already exist in the tree. For the **four others** (`CHARTER-v2.md` §3 G2):

```text
longest-path-gives-cycle            (Extremal)
n+1 integers, two congruent mod n   (Pigeonhole)
binary words, no adjacent ones      (Divide)
one rotation-invariant coloring     (Symmetry)
```

the tree contains only the **nicknames** — there is **no authoritative Engel problem text** for any of the four in any file I can find (`grep` across `packs/`, `.md`, `.py`; the only Engel packs are blackboard/coins/means; the only "Problem E*n*" references are E3/E4/E7). I will **not** fabricate the problem wording. The four records are blocked on the operator supplying the exact statements (or a source they come from).

### Missing domain constructors (separate from statement text)

Even given the statements, the four records cannot be stated faithfully in machine terms — the domain constructors are absent (measured against the built namespace): `Path`/`Cycle`/`Graph`, `Integer`/`Remainder`/`Residue`/`Congruent`, `Word`/`Adjacent`, `Coloring`/`Rotation`. Filed as `[SHARED]` request `protocol/[SHARED]-A1-CONSTRUCTORS.md`. The E7 observable-constructor request is cited (already filed in `SHARED-CONSTRUCTORS-E7.md` on `01a066cf`), not re-requested.

### Tier0 / Tier1 authoring status

- **Tier0 (Engel warm-ups, never held out):** E2 exists, loads OK (cite). Four others: BLOCKED (statement + constructors).
- **Tier1 (easy IMO/shortlist reformulations, ≥2 per method):** not yet started — the four Tier0/Engel fixtures for the methods are not authorable yet, so there is no method-anchored example set to build ≥2 per method from. Started once Tier0 method fixtures are unblocked.

---

## Turn 3 — Ground 2 CLEARED (authoritative statement text supplied)

**Ground 1 (A1 domain constructors):** STILL OPEN — constructors absent at integration tip `b812db9` (re-grepped `Path/Cycle/Graph/Integer/Remainder/Residue/Congruent/Word/Adjacent/Coloring/Rotation`, all absent). Pending INT landing `[SHARED]-A1-CONSTRUCTORS.md` (label registration only, per the scope ruling).

**Ground 2 (authoritative statements):** **CLEARED** this turn. The operator supplied the exact statement text for all four Tier0 problems. Recorded verbatim below, each annotated with the verified math content (curated, not fabricated) and the method assignment.

### Supplied statement text (verbatim, Ground 2)

**1. Longest Path (Extremal)**
> In a finite graph G = (V, E), every vertex has degree at least 2. Prove that there exists a cycle.

Verified: TRUE. A finite graph with min degree ≥ 2 always contains a cycle (a maximal simple path's
endpoint has ≥ 2 neighbors, all on the path, so a back-edge closes a cycle). Method = `Extremal`.
Proof-target (not a count).

**2. n+1 Integers (Pigeonhole)**
> Prove that among any n+1 integers, there exist two whose difference is divisible by n.

Verified: TRUE. n+1 integers fall into n residue classes mod n, so two share a residue; their
difference is ≡ 0 mod n. Method = `Pigeonhole`. Proof-target.

**3. Binary Words (Divide)**
> Find the number of binary words of length n that do not contain two adjacent ones.

Verified: the count is the Fibonacci number F(n+2) (a_1=2, a_2=3, a_n=a_{n-1}+a_{n-2}). Method =
`Divide` (recurrence / divide-conquer). NOTE: **count-target**, not a proof-target — the "goal" is a
closed-form/recurrence count, not a reachable state. Design consideration for authoring.

**4. Vertex Coloring (Symmetry)**
> Find the number of distinct colorings of the vertices of a square using m colors, where colorings
> are considered distinct only if they cannot be transformed into one another by rotation.

Verified: "up to rotation" is the cyclic group C4 (not dihedral D4). Burnside over C4 gives
(m⁴ + m² + 2m)/4. m=2→6, m=3→24, m=4→70, m=5→165. Method = `Symmetry`. NOTE: **count-target**,
and the group is C4 (rotation only, no reflection).

### Ground status

```text
Ground 1 (constructors): OPEN   — INT lands [SHARED]-A1-CONSTRUCTORS.md (label registration only)
Ground 2 (statements):   CLEARED — text recorded above, verified-correct, method-assigned
=> lane STILL PARKED: DO NOT author until BOTH clear (standing double-gate rule, protocol/G.md)
```

### Method-target-shape note (for authoring)

Problems 3 and 4 are **counting** questions; problems 1 and 2 are **proving** questions. A
count-target record's obligation skeleton differs from a proof-target record's (no goal-state
reachability; the "goal" is a formula/count). This must be reflected when Ground 1 clears and the
records are authored — do not force a prove-target skeleton onto a count problem.

---

## Turn 4 — Ground 3 recorded as an explicit gate

The reviewer elevated count-vs-proof to a **third ground** (problems 3 & 4 only), recorded in
`protocol/G.md`. Authoring map:

```text
problems 1, 2: author when Ground 1 clears       (constructors + statements)
problems 3, 4: author when Ground 1 clears AND count-target skeleton confirmed expressible
               (constructors + statements + count-target expressibility)
```

- If G1's method payloads only emit proof-reachability skeletons, that is a `[SHARED]` finding routed
  to **G-eng**, not something G/I-op forces by writing a prove-skeleton onto a count problem.
- Coloring count is locked to **C4** (rotation only): `(m^4 + m^2 + 2m)/4`. The dihedral count
  `(m^4 + 2m^3 + 3m^2 + 2m)/8` is a different problem requiring a restated statement — not a
  correction to apply during authoring.

---

## Turn 5 (2026-09-08) — Agent 3: four source-pinned record blueprints

### Tier0 blueprint cards (curriculum/tier0/cards/)

```text
extremal-longest-path.md          (Extremal, proof-target)
pigeonhole-residue-classes.md     (Pigeonhole, proof-target)
divide-binary-words.md            (Divide, count-target)
symmetry-square-rotations.md      (Symmetry, count-target)
```

All four are **blueprint-only, not training input**. No loadable TrainingRecord YAML authored; no
session run; no Pool B touched.

### Promotable record count

```text
currently loadable Tier0: 1 (engel_e2_blackboard_parity — cited, loads OK)
blueprint cards:          4 (Extremal, Pigeonhole, Divide, Symmetry)
Tier1 practice:           not started (awaits Tier0 method fixtures + count-shape resolution)
```

### Ground status (unchanged, recorded here for the join rule)

```text
Ground 1 (constructors): OPEN — INT-SHARED-A1
Ground 2 (statements):   CLEARED
Ground 3 (count-target): OPEN/PENDING — G-COUNT-AUDIT (Divide + Symmetry cards only)
```

---

## Turn 6 (2026-09-08) — G4 decoys + G5 held-out: pool assignment

All ten cards written this turn are **Pool A** (curriculum, never held out); **none are Pool B /
exam**. Pool B (the sealed exam) remains untouched.

```text
Pool A G4 decoys (5):  invariance-decoy-parliament, extremal-decoy-equal-degrees,
                       pigeonhole-decoy-domino-board, divide-decoy-even-ones,
                       symmetry-decoy-labeled-square
Pool A G5 held-out (5): extremal-min-degree-path, pigeonhole-subset-sum,
                       divide-domino-strip, symmetry-triangle-rotations,
                       invariance-seven-glasses
exam (Pool B):          none — untouched
```

The four held-out cards that are **count-targets** (divide-domino-strip, symmetry-triangle-rotations)
inherit Ground 3 + the pre-finding; the held-out proof-targets (extremal-min-degree-path,
pigeonhole-subset-sum, invariance-seven-glasses) are gated only on Ground 1.

### Join / conversion rule (from the parallel-unblock plan)

```text
1. INT reviews + merges the A1 vocabulary patch into a semantic candidate.
2. INT runs both complete shards and cuts a new immutable tag.
3. G/I-op converts extremal + pigeonhole cards first.
4. divide + symmetry convert only when G-COUNT-AUDIT clears their count-target shapes.
5. Each converted record: loads via real loader; goal compiles; genuine partial match;
   source + method certificate preserved.
6. Zero partial matches leaves that record blocked (never rewritten into a vacuous shape).
```

---

End-of-turn block:

```text
agent: G/I-op
branch: arena/01a068c2 @ 9fb8870  (remote = local confirmed)
frozen tag: none authorized   checkpoint: n/a
session: none — authoring turn
Pool A authored this turn: 0 new (E2 cited/existing; 4 blocked)
Pool B: untouched; SHA-256 placeholder reserved in protocol/I.md
missing_constructors: Path/Cycle/Graph, Integer/Remainder/Residue/Congruent,
    Word/Adjacent, Coloring/Rotation  (→ [SHARED]-A1-CONSTRUCTORS.md)
excluded FLT-shaped problems: none encountered this turn
defects found by running: none
blocked on:
  operator: authoritative Engel statement text for the four Tier0 problems
  INT: [SHARED] A1 domain constructors
  INT: wave-1 tag (research_protocol.md unpublished)
```
