# cint-integrated-5 — isolated check-only ActivateProposal validity gate (2026-09-16)

Implements the next bounded item authorized at cint-integrated-4 review.

## Design

`programme_c/validity.py` exposes `make_activate_proposal_validity_check()`
which returns a validity-callable `(entry, accepted_proposals, version) -> bool`:

  1. On each call it boots a FRESH isolated runtime via
     `runtime.boot_from_packs(PACK_PATHS, namespace)` which invokes
     `make_fresh_runtime` (new Hypergraph + constructor registry). State
     from prior checks never leaks across calls.
  2. A starting `GraphVersion(empty, empty, empty)` is built; any
     previously activated entries carried in `accepted_proposals` that
     expose a `proposal_entry` term are replayed via `InstallLaw` so
     ActivateProposal sees the actual accepted state.
  3. For the candidate entry:
       * if `entry["proposal_entry"]` is supplied it is used directly;
       * else if `entry["proposal_term"]` is supplied it is wrapped in a
         ProposalEntry with empty annotations;
       * else (`proposal_text` only, no constructor hook) the check
         returns False (fail-closed; NO free-text parser, NO structural
         fallback).
  4. A synthetic `Approved(proposal, "c-int-validity-check")` annotation
     is attached via `ChainAddMissing` (idempotent).
  5. `graph.ActivateProposal(graph_version, annotated_entry, proposal_store)`
     is invoked. The check returns True iff `M.Head(result)()` (i.e.
     installed_version) is not EmptyList. The refusal reason (second
     element of the pair) is ignored beyond that — any refusal (Reason
     Unapproved / ReasonSafety / ReasonUncountersigned) yields False.
  6. The runtime is discarded (del'd) in a finally block. No durable
     state is mutated, no activation_id is committed, no external side
     effect occurs. There is NO reconciliation surface for this check
     because check-only discards its runtime — this satisfies the
     forward requirement from cint-integrated-4 review: a pure check
     that discards its heap cannot leave ambiguous state.

`programme_c/admission_hooks.py` gains `make_live_activate_proposal_check()`
which returns (check, BootError). Pack files are verified to exist at
factory time; missing packs raise BootError so callers can HALT and
report rather than silently substituting a structural check.

## Tests (programme_c/tests/test_int_gates.LiveActivateProposalValidityTests)

  * test_well_formed_proposal_passes_isolated_activate_proposal —
    constructs a Zero->Zero rewrite rule, compiles via CompileRuleToLaw,
    boots fresh runtime, ActivateProposal accepts (installed_version !=
    EmptyList).
  * test_empty_proposal_fails_closed — proposal wrapping M.EmptyList
    rejected.
  * test_text_only_entry_fails_no_structural_fallback — text-only entry
    rejected; no parser is invoked; no fallback.
  * test_isolated_runtime_discarded_no_host_mutation — two back-to-back
    checks produce the same True result, confirming no host-state
    mutation across calls and no reconciliation surface.

These run in addition to the existing 52 tests. Total 56/56 pass.

## No-reconciliation-surface confirmation

Because validity check-only (a) never invokes activation_fn, (b) never
persists anything, and (c) discards its Hypergraph/registry after the
call, there is no commit and therefore nothing to reconcile. The
`activation_id` mechanism only applies to `activate_front`, which is
invoked AFTER validity passes and the admission is persisted; validity
runs inside admit_next prior to any state-changing commit.

## Unchanged files

`git diff --name-only a5209488… -- core.py search/compare_executors.py
search/compare_subprocess.py` returns empty.

## Out of scope for this slice

  * Rent and human-approval hooks untouched (still test-only).
  * No free-text proposal parser; future slices may add one but it must
    feed into a real Law/Proposal term, not a structural check.
  * Live admission remains HOLD until rent + human gates are wired and
    their evidence bound to (proposal, accepted_state, benchmark).

