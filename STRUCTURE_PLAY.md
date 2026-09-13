# 12 September 2026 — STRUCTURE-PLAY-ENG: the algebra laboratory

## Purpose

This ticket builds the first bounded finite-operation laboratory: the machine
discovers unnamed operational structure by experiment, certifies what it can
re-derive, and only then may recognize that structure as a known abstraction.
Law profiles come first; their names come after.

The governing epistemic discipline, which the implementation never collapses:

```text
ObservedRegularity   — a tested instance or observation, nothing more
ConjecturedLaw       — an equation with supporting observations and
                       searched counterexamples; never proof
CertifiedLaw         — an equation with a method, findings, and a replay
                       record that re-derives the verdict independently
```

Only `CertifiedLaw` terms may support an abstract classification. A
conjecture never enters recognition, and a conjecture never enters a proof.

## What was added

### `structure_play.py` — the laboratory

- **Carriers.** The triangle transformation carrier (identity, two
  rotations, three axis reflections) with composition implementing the
  dihedral relations `s_t ∘ r_j = s_(t-j)`, `r_j ∘ s_t = s_(t+j)`,
  `s_u ∘ s_t = r_(u-t)` over machine nat arithmetic modulo three; the
  positionally renamed carrier with its transported table; and two decoy
  carriers (right projection on three elements; the twisted four-element
  right projection whose `α∘α∘α` binding breaks associativity).
- **Declared operations.** `(DeclaredOperation name kind elements table)`.
  The direct kind applies the triangle composition; the table kind reads a
  recorded table. Decoy and renamed carriers are declared as table
  operations so every question is asked through one uniform interface.
- **Experimentation.** `LaboratoryPlan` (a bounded plan of ordered pairs
  consumed one machine-nat predecessor at a time), `ApplyExperiments`,
  `ExperimentApplication`, `ClosureObservation`,
  `CommutativityObservation`, `IdentityCandidate`, `InverseCandidate`,
  `AssociativitySearchRecord`, `ObservedEquation`, `Counterexample`.
- **`DirectLawProbe`.** The generic laboratory questions, asked over the
  full bounded sweep of one declared operation: closure, associativity,
  identity, inverses, commutativity. Verdicts are `LawHolds`,
  `LawViolated` (with a concrete counterexample term), or `LawUnknown`
  (a prerequisite failed). Nothing presupposes group, monoid, or
  semigroup; the questions are generic.
- **Certification.** `CertificationAttempt` wraps probed findings into a
  `CertifiedLaw` carrying the `ExhaustiveFiniteCheck` method stamp and a
  `ReplayCheckExhaustive` record. `CheckReplay` re-derives the verdict
  from the record against the declared operation, independently of the
  original probe run.
- **`StructureSignature`.** The unnamed product of exploration: carrier
  tag, operation name, five certified slots, conjectured laws,
  counterexamples, and an evidence chain holding the five probe verdicts
  plus the declared operation itself, so every certificate in the
  signature can be replayed with no outside context.
- **Candidates.** `BuildStructureCandidate` (a declared abstract-name
  proposal that certifies nothing) and `WithholdStructureCandidate`.
  Slot-level lifecycle edges `WithSignatureSlotWithheld` and
  `WithCertificateRestored` disable and restore individual certificates.
- **Process model.** `LaboratoryCheckpoint` (immutable worker input),
  five worker roles (closure, identity, inverses, commutativity,
  associativity counterexample search) writing only private
  `WorkerJournal`s, append-only `MergeObservationLedgers`, and serial
  `AdmitProposal` (a conjecture enters the baseline only when an
  independent probe supports it; a counterexample proposal is recorded
  as a refutation and never as structure). `ExplorationRun` is the
  bounded entry point; budgets are machine nats and an over-budget run
  is refused with an empty ledger.

### `structure_recognizer.py` — the separate recognizer

- `RecognizerCatalogue`, strongest profile first: abelian group
  (closure, associativity, identity, inverses, commutativity), group,
  monoid, semigroup. Entries are law-label lists only; the recognizer
  never inspects carrier elements or operation names.
- `CertificationGate`: a requirement is met only when the matching
  signature slot carries a `CertifiedLaw` of exactly that law label whose
  replay record re-verifies against the signature's stored operation.
  Closed gates name their blocking requirement.
- `RecognizeStructure`: scans the catalogue strongest-first and reports
  the most specific structure whose gate opens, or withholds. With a
  certificate disabled, recognition degrades to the strongest structure
  the remaining certificates still support: the triangle
  signature with the identity certificate removed recognizes as a
  semigroup (the remaining certificates still support exactly that) and
  never as a group; restoring the certificate restores `AbstractGroup`.

### `labels.py`

Additive only: the laboratory and recognizer label singletons and their
`sync_from_namespace` entries. No existing label or behavior was changed.

### `validation/test5_structure_play.py` — scenario coverage

Twelve sections, all passing (`logs/structure_play_stage1_test5.log`):

1. Triangle operation declaration; complete 36-cell row-major table;
   identity and reflection-involution cells; noncommutativity witness.
2. Table construction checks (continues in section 2 of the log).
3. Bounded exploration run: `ExplorationComplete`, 31 merged ledger
   entries, positive closure observation, conjectures for closure,
   associativity, identity, and inverses proposed — and refuted
   commutativity correctly left unconjectured.
4. Serial admission: all four supported conjectures admitted against
   independent probes.
5. Unnamed signature: four group-relevant slots certified with verified
   replays; refuted commutativity left uncertified; counterexample slot
   carries the refutation evidence.
6. Recognition: `AbstractGroup` recognized from certificates alone; the
   abelian gate closed with commutativity named as the blocker.
7. Transfer: with identity and inverse certificates the machine predicts
   the held-out composition `(r1 after r2)` as the identity element taken
   from the certificate, confirmed against the operation; with the
   certificates removed the same request returns `TransferUnavailable`.
8. Nonassociative decoy: closure holds, associativity and identity
   violated, concrete counterexample recorded, the worker journal
   produces the refutation, serial admission rejects it as structure,
   recognition withheld with associativity named as the blocker.
9. Semigroup-without-identity decoy: closure and associativity
   certified, identity slot empty, recognized as `AbstractSemigroup`;
   the monoid gate closed with identity named as the blocker.
10. Renamed-carrier invariance: all five probe verdicts agree under the
    renaming bijection, the renamed table carrier recognizes as
    `AbstractGroup` (the same abstraction), its certificates replay
    against the renamed table, and noncommutativity survives renaming.
11. Certification lifecycle: removing the identity certificate removes
    group recognition (the gate blocks at identity) while the remaining
    certificates still support the semigroup entry; restoring
    the certificate restores `AbstractGroup`.
12. Budget guard: an over-budget run is refused with an empty ledger.

## Acceptance against the ticket

```text
1. Exploration produces an unnamed StructureSignature            yes (5)
2. Recognition only after certificates for every required axiom  yes (6)
3. The nonassociative decoy is rejected with a concrete
   counterexample                                                yes (8)
4. Certified consequences shorten a held-out task:
   the transfer shortcut predicts without touching the operation yes (7)
5. Removing the certification removes the shortcut               yes (7, 11)
6. Restoring the certification restores it                       yes (11)
7. Renaming carrier elements does not change the recognized
   abstraction                                                    yes (10)
```

## Non-goals (unchanged from the ticket)

Rings, fields, elliptic curves, joint-set rent accounting, automatic
host-function synthesis, infinite-carrier generalization, and finite-
generation claims are out of scope. Bounded play conjectures; only global
proofs or trusted theorem leaves may promote a conjecture.

## Noted limits

- The exploration probes are exhaustive over the bounded carrier, which
  is exactly what the `ExhaustiveFiniteCheck` method stamp licenses. No
  probe result generalizes past the carrier it swept.
- `FinitelyGenerated` remains uninferable from finite experimentation by
  construction; nothing in the signature carries such a claim.
- The pre-existing validation scripts `test1`–`test4` import the package
  under its original `hyge` name and expect the original checkout
  layout; their outcomes on this machine are identical before and after
  this change (test1's minimal planner run still ends `Failed`, test3
  still crashes in pack loading on master as well). Those are the
  runtime-baseline debts already tracked in the August plan, not
  regressions from this ticket.
