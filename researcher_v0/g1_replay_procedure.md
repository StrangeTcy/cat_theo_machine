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
   exact ruleset.** Recompute the fingerprint of the ruleset actually walked
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
