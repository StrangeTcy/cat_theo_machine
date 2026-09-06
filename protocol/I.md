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
