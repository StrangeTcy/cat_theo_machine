# Researcher-v0 — operational certificate-replay procedure (A2.1)

Status: **procedure only**. G1 implements no certificate and issues no
`CHECKED_UNREACHABLE`. This document states, step by step, what a later
checker MUST recompute before such a result may exist. It is written now
because A2.1 makes the procedure blocking for G1, and because
`researcher_v0/inspection.md` §3a described the *shape* of a replay without
making the order of checks explicit.

Verified context (unchanged from G0, base `8094c461`): `invariance.py`

- `IsInvariant` (`:1235`), `IsUnreachable` (`:1263`) read only an outer label;
- `ReachabilityPrune` (`:1276`) trusts `IsInvariant`, checks `PhiHolds(start)`
  only, and compares readings; it never checks `PhiHolds(goal)`;
- `PhiReading` (`:58`) returns `EmptyList` when the observer matches no fact,
  so a *missing* goal reading compares unequal to a present start reading and
  would mint an `Unreachable` term from a miss.

Consequently an archived certificate tag is never evidence. Every claim is
recomputed from rule content, in this order.

## Inputs to a replay

```text
observer phi                     -- the exact term of the observer
ruleset                          -- the exact chain of rule CONTENT terms
start, goal                      -- the exact state terms
expected ruleset digest          -- fingerprint of that ruleset (A2.2)
expected checker version         -- the version string of the replay code
```

## Steps (all of them, every time, in this order)

1. **Fingerprint the task's ruleset.** Compute the content digest over the
   task's exact rule terms. If it differs from the certificate's recorded
   digest → `SCOPE_MISMATCH`. Record it, prune nothing, claim nothing. No
   comparison of observers or readings happens on this path.
2. **Recompute preservation for every rule, over rule content.**
   For each rule term in the task ruleset run
   `invariance.Preserves(rule, phi, registry)` and require `IsPreserves` on
   every one. Never accept an archived `Invariant` tag as evidence, and never
   stop at the first success.
3. **Check that the recomputed result names the requested observer and the
   exact ruleset.** Recompute the fingerprint of the ruleset that was walked
   and compare it to step 1's digest; compare the observer term in the
   recomputed result to the requested `phi` with `Compare`. A mismatch is
   `UNSUPPORTED`, not a result.
4. **Read both sides, and require both readings present.**
   - `invariance.PhiHolds(start, phi)` must be truth;
   - `invariance.PhiHolds(goal, phi)` must be truth;
   - the readings must be non-missing: `PhiReading(start, phi)` and
     `PhiReading(goal, phi)` must not be `EmptyList`.

   A missing reading on either side ends the replay. This is the specific hole
   A2.1 identified: `ReachabilityPrune` never checks the goal side, and a miss
   there is indistinguishable from a different value.
5. **Compare the two readings.** `constructors.Compare(start_reading,
   goal_reading)` must be false. Equal readings → not unreachable, and not a
   refutation of the ruleset either: the observer simply does not separate the
   endpoints.
6. **Bind the certificate record** to all five of
   `(observer, start, goal, ruleset digest, checker version)` before the result
   is written. A record missing any of the five is malformed.
7. **Failure classification.** Malformed evidence, a timeout, a crash, an
   unsupported observer or an unsupported ruleset shape produce
   `OPEN_RESIDUAL`, `BUDGET_EXHAUSTED`, `EXECUTION_FAILURE` or `UNSUPPORTED`
   respectively — never `CHECKED_UNREACHABLE`.

## Named acceptance item deferred to the checker gates G3/G4 (folded under A2.1)

Scope note: this belongs to the *checker*, exercised in G3/G4, not to G2.
G2 is task generation only. G2 records this item under "Deferred to checker"
and writes no checker code; G1 records it and implements nothing.

Named test, to be written at the checker gates and not in G1 or G2:

```text
a missing observer reading must not compare equal to false_value, and must not
be treated as a value at all
```

Why it is named separately from step 4 above. `PhiReading` (`invariance.py:58`)
returns `EmptyList` when the observer matches no fact. `EmptyList` is a term,
not a verdict, and the substrate's predicates also answer with terms — so a
checker that compares readings without first asking "is a reading present"
can turn an absence into a comparison outcome. That is the same class of
defect the domain layer removed when a non-term reached a term slot, one level
up: at the certificate layer a non-verdict reaches a verdict position.

Required behaviour:

- a missing reading on either side is classified NOT CHECKED and ends the
  replay as `UNSUPPORTED` (the observer does not read this state) or
  `OPEN_RESIDUAL` — never as a comparison result;
- `Compare(EmptyList, false_value)` answering false is not a licence to
  conclude a difference: absence of a reading is not evidence of a different
  value, and it is not evidence of a false predicate either;
- no certificate is minted, and no prune event is recorded, on any path where
  a reading was missing.

Test shape for the checker gates (G3/G4): build a state that does not carry
the observed fact, compute the reading, and require the checker to report NOT
CHECKED together with the absence of a certificate record and the absence of a
prune event.

## Absolute rules

```text
bounded search exhaustion in an unbounded token world -> OPEN_RESIDUAL or
    BUDGET_EXHAUSTED, never an unreachability result;
a timeout is not a counterexample;
a crash is not a refutation;
a missing reading is not evidence of a different value;
a rule-order change is not a scope change (the digest sorts per-rule digests);
adding Add1, removing a rule, or changing a legality precondition IS a scope
    change, and old certificates must scope-mismatch before they may prune.
```

## What G1 did and did not do

```text
did     : built the domain, the fingerprint, the partition declaration, the
          transition applier, and the checker-shape tests that show
          Preserves succeeds on R_even and fails on the Add1 rules with
          readings present on both sides;
did not : prove any invariant, mint any certificate, run any search, emit any
          CHECKED_UNREACHABLE, or import any live path.
```

A preserved reading is a property of rule content. It is not a research
result, and G1 does not report it as one.

## Handed forward

The named acceptance item in the section above (a missing reading must not
compare equal to `false_value` and must not be treated as a value) is folded
under A2.1 and is a requirement of the **checker gates G3/G4**. G1 records it
and implements nothing. G2 records it under "Deferred to checker", writes no
checker code, and must not start the checker early.

Branch note for the operator: this document's G1 verdict is recorded against
commit `83e6003`, and the branch carries two documentation-only commits after
it (`fe1e480`, a wording fix in this file; `c0b3ebd`, which adds
`researcher_v0/CONSTRAINTS.md`). Neither touches executable code, the domain,
the fingerprint or the digests.
