# C-INT integrated-5 qualification correction (Q1/Q2/Q3)

Date: 2026-09-17
Branch: work/C-INT/eng-base-0/r1
Predecessor tag: cint-integrated-5 @ 2705a39d
Review: Fable 5.1 conditionally accepted -5; closes Q1/Q2/Q3 in one
corrective slice before rent/human wiring opens.

## Verdict

Q1 / Q2 / Q3 closed. 58/58 Programme-C tests pass (56 baseline + 2 new
Q2/Q3 additions; previous in-process validity tests re-pointed at the
subprocess dispatcher). Files `core.py`, `search/compare_executors.py`,
`search/compare_subprocess.py` remain byte-identical to eng-base-0
@ a52094888a30099150e6310b4b171ee2af97fe36.

## Q1 — host-global mutation eliminated (subprocess isolation)

The validity check now runs in a spawned child process:

* Parent side: `programme_c/validity.py::run_validity_check_subprocess`
  writes a JSON request to a temp file, invokes
  `python -m hyge_int_pkg.main validity-check <req> <resp>`, and reads
  a JSON response. PYTHONPATH is set to the package parent;
  HYGE_SEARCH_WORKER_* gate env vars are stripped; response is written
  atomically (tmp+fsync+os.replace).
* Child side: `run_validity_child(req_path, resp_path)` boots an
  isolated runtime from the same pack set used by the C-A spawn
  pattern, applies `BootstrapSafetyInvariants`, InstallLaw-replays
  accepted entries decoded from a small `proposal_encoding` /
  `law_encoding` JSON surface, constructs a copy of the candidate
  proposal entry with a synthetic `Approved(...M.Char("c-int-validity-check"))`
  annotation attached in-child, calls `G.ActivateProposal`, and
  writes `{status, passed, reason, detail}` back.
* `main.py` registers `validity-check` as a mode so `python -m`
  dispatch does not require new entry points.
* `make_live_activate_proposal_check()` now returns a single
  `(entry, accepted, version) -> (ok, reason_atom)` callable. Parent
  never imports `graph`/`runtime` for validity; the coordinator's
  `M.AllConstructors` / Hypergraph are untouched (structural
  isolation, not capture-and-assert).

Reason atoms emitted:

| Atom             | Meaning                                                                 |
|------------------|-------------------------------------------------------------------------|
| ok               | ActivateProposal installed the candidate; validity passes.             |
| invalid-cert     | ActivateProposal refused (ReasonUnapproved/ReasonSafety/ReasonUncountersigned) or candidate undecodable; fail closed (reject + pop). |
| launch-error     | Child failed to spawn / timed out / returned rc != 0 / invalid JSON; F_LAUNCH_ERROR returned, queue front intact (halt-and-report). |

`make_validity_check` accepts either plain-bool or `(bool, reason)`
returning validators via try/except indexing (no `isinstance`).

## Q2 — launch error holds front intact

* `JoinAdmission._run_gate` was extended to decode `(bool, reason)`
  returns from any gate, falling back to the legacy bool contract.
* `JoinAdmission.admit_next` distinguishes F_LAUNCH_ERROR (no pop, no
  state mutation, returns `(False, pid, "validity-launch-error")`)
  from F_INVALID_CERT (pop, `rejected-validity`,
  `(False, pid, "validity failed")`). accepted_state_version is NOT
  mutated on either failure path.
* New test `test_launch_error_holds_queue_front` injects a nonexistent
  package_root (child cannot boot), asserts the hook returns
  (False, F_LAUNCH_ERROR), the queue length remains 1, the front
  proposal_id is preserved, and its state stays "queued" (NOT
  rejected-validity).

## Q3 — real ActivateProposal gating + state dependence pair

`_child_law_from_encoding` now supports two law shapes:

* `{"kind":"rule","left":...,"right":...}` — single-premise rewrite
  rule (Char identity, zero/Succ, Pair nesting all decodable).
* `{"kind":"policy_entry","class_name":..., "gate":...}` — wraps a
  `PolicyEntry(class_name, gate)` term as a trivial identity Rule so
  `CompileRuleToLaw` encodes it into a Law whose RHS contains the
  `PolicyEntryLabel` node. `ClassifyProposal` scans RHS subterms for
  that label and classifies the proposal as `policy_change`.

New tests:

* `test_q3_well_formed_policy_change_loosening_refused` (Q3(i)): a
  structurally valid `PolicyEntry("install_law","auto")` proposal is
  refused against empty accepted state. Bootstrap effective policy has
  `install_law = human`; the proposal loosens human->auto;
  ActivateProposal's Step 37 requires a structurally distinct
  Countersigned annotation which the synthetic Approved does not
  provide; the refusal atom is ReasonUncountersigned. Hook returns
  (False, F_INVALID_CERT).
* `test_q3_state_dependence_pair` (Q3(ii)): the SAME
  `PolicyEntry("install_law","auto")` proposal is (a) REFUSED against
  empty accepted state (as above) and (b) ACCEPTED when an accepted
  entry with the identical `PolicyEntry("install_law","auto")` law is
  InstallLaw-replayed first. After replay the effective policy already
  has install_law=auto; the proposal is an identity change, not a
  loosening, so the countersign requirement does not apply. This
  confirms InstallLaw replay shapes ActivateProposal's decision, not
  just shape checking.

## In-band confirmations

* Synthetic Approved annotation: attached inside the child only, to
  a freshly-decoded ProposalEntry copy. The parent never imports
  machine or graph for validity, never mutates the queue entry dict,
  and never places an Approved annotation on any object that survives
  the child process. The child's runtime is discarded after writing
  the response.
* InstallLaw replay vs live ActivateProposal: ActivateProposal is the
  full gate (CheckSafety floor; ProposalEntryIsApproved; policy_change
  countersign check) and ends with InstallLaw as its final write
  path. Check-only replay reboots BootstrapSafetyInvariants (the three
  floor invariants) and calls InstallLaw directly on each accepted
  entry. For entries that previously passed ActivateProposal,
  InstallLaw rebuilds the same installed-graph state (nodes/edges and
  effective policy); the countersign/safety checks were discharged at
  the time of original admission and are not re-evaluated for replay,
  which is sound because replay is check-only against the same
  snapshot and the child's state is discarded.

## Boundary confirmation

* `make_rent_check` and `make_human_check` remain fail-closed deniers.
* Live admission stays HOLD until rent + human gates are wired with
  evidence bound to `(proposal, accepted_state, held-out benchmark)`
  in a later cut. This commit closes Q1-Q3 only.
* L-S-5 item 3 (Programme L story engine into JoinAdmission) remains
  held.

## Test log

```
Ran 58 tests in 346.484s
OK
```

Test discovery: `python -m unittest discover -s programme_c/tests`.
Files unchanged vs base a5209488: core.py, search/compare_executors.py,
search/compare_subprocess.py.
