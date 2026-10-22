# C-INT integrated-7: rent hook wiring

Date: 2026-09-17
Branch: work/C-INT/eng-base-0/r1
Predecessor tag: cint-integrated-6 @ 84d0a09
Authorization: Fable 4.6 (Opus 4.6) accepted -6; rent next bounded slice.

## Verdict

Rent hook wired. 62/62 Programme-C tests pass (58 baseline carried from -6,
plus 4 new rent tests). `core.py`, `search/compare_executors.py`,
`search/compare_subprocess.py` remain byte-identical to eng-base-0
@ a52094888a30099150e6310b4b171ee2af97fe36. Live admission remains HOLD;
human-approval wiring is the next slice.

## Held-out benchmark convention

`benchmark_dir/benchmark.json`, schema_version=1:

```
{ "schema_version": 1,
  "timeout_seconds": <int, default 60>,
  "step_budget": <int, positive>,
  "max_total_ms": <int, positive>,
  "specs": [ { "name": "<id>", "left": <simple-term>,
               "right": <simple-term>, "start": <simple-term> } ] }
```

"Pass" means:
1. benchmark.json is present, readable, valid schema, positive budgets.
2. Isolated child boots the same pack set used by validity, applies
   BootstrapSafetyInvariants, InstallLaw-replays accepted laws,
   CompileRuleToLaw-installs every spec rule, and walks the resulting
   graph nodes/edges/invariants chains under the step budget.
3. Total wall-clock (boot is excluded; measured inside the child after
   successful boot) <= max_total_ms.

Evidence is recorded at `benchmark_dir/evidence/<safe_pid>_v<version>_<benchid_prefix>.json`,
keyed by `(proposal_id, accepted_state_version, benchmark_identity)`
where `benchmark_identity = blake2b(benchmark.json bytes, 32 bytes)`.
State-version change OR benchmark-content change invalidates prior
evidence; the hook re-runs the child.

## Reason atoms

| Atom            | Meaning                                                  | admit_next action          |
|-----------------|----------------------------------------------------------|----------------------------|
| F_LAUNCH_ERROR  | Missing/unreadable benchmark, child spawn/timeout/rc≠0, JSON error, encoding failure | Front intact, halt-and-report ("rent-launch-error") |
| F_RENT_FAIL     | Benchmark ran; spec rejected / step budget / time budget exceeded | Reject + pop ("rent failed") |
| ok (pass)       | Specs passed; evidence written                           | Advance to next gate       |

Rent is performance-only; failure never invalidates accepted laws.
No joint-set rent in this version.

## Subprocess isolation

Rent runs in an ISOLATED CHILD via
`python -m hyge_int_pkg.main rent-check <req.json> <resp.json>`
(mode added to main.py). Same structural-isolation property as
validity: the parent never imports graph/runtime for rent; the
coordinator's `M.AllConstructors` / Hypergraph are not mutated.
Request/response are JSON over temp files; response written
atomically (tmp+fsync+os.replace).

## Encoding surface fail-closed (carry-forward closed)

`programme_c/validity.py` docstring now explicitly documents the
representable term shapes (`Zero`/`Succ`/`Char`/`Pair`/`EmptyList`)
and law kinds (`rule`, `policy_entry`). Any accepted entry or
candidate lacking a decodable `proposal_encoding`/`law_encoding`
(missing key, unsupported shape, `CompileRuleToLaw` returns
`EmptyList`) is surfaced as `F_LAUNCH_ERROR` -- queue front held
intact, no pop, no false pass, no misclassification as
F_INVALID_CERT/F_RENT_FAIL. Parent-side serialization probe raises
and returns launch-error before spawning the child; child-side decode
errors also return launch-error in the response. A new test
`test_encoding_surface_fail_closed_launch_error` verifies this end-
to-end through the hook.

## C1: manifest-only accepted-set population (confirmation)

The accepted set is populated exclusively through successful
`admit_next → activate_front` sequences:

* `admit_next` is the sole site that appends to `self._accepted_proposals`
  (line "self._accepted_proposals.append(entry)") and increments
  `_accepted_state_version`. It is gated by `_persist()` which writes
  the manifest atomically.
* `enqueue_proposal` appends only to `self._proposal_queue`, never to
  accepted.
* `JoinAdmission.__init__` rehydrates accepted/queue/version from the
  manifest on startup; on a corrupt/wrong-schema manifest it raises
  `ManifestError` (strict_manifest=True path used in production).
* `deliver_child_result` mutates only `self.claims` (child result
  records); it does not touch the accepted-proposal list.
* Recovery: `activate_front` transitions a proposal from
  admitted/activating/activation-failed → activated. On the
  reconciliation path (recover-after-crash) it marks an existing
  entry activated via reconcile_fn — but that entry was originally
  admitted through admit_next and persisted in the manifest.
* There is no public `insert_accepted`, `append_accepted`, or
  manifest-write API that bypasses admit_next. Tests that manipulate
  `ja._proposal_queue[*]["proposal_encoding"]` after enqueue do so to
  inject test encodings; they never add to `_accepted_proposals`
  directly.

No manual recovery path inserts a new accepted entry; the only
"external" source is the manifest on disk, which is produced solely
by `_persist()` after successful admission.

## C2: bootstrap parity between child and coordinator (confirmation)

Both the coordinator's runtime and the validity/rent children boot
through the same `runtime.boot_from_packs(pack_paths, namespace,
debug=...)` entry point. The children pass an explicit pack list
`_child_pack_paths()` derived from the same `packs/` directory in the
package root. BootstrapSafetyInvariants is called identically on the
GraphVersion in every case (its three floor invariants have fixed
GMPRep bounds compiled into graph.py: BOOT_STORE_CAP=100000,
BOOT_DEPTH_CAP=50000, BOOT_PENDING_CAP=1000; ImpactPolicy is
deterministically constructed from graph-local constants, not from
external state). The child runs against the same installed pack
files; if any pack is missing or corrupted `boot_from_packs` raises
and the child returns launch-error (front held intact), so divergence
cannot silently produce different pass/fail outcomes. No pack version
fingerprint is pinned beyond file identity; the pack files are
committed in-tree and shipped with the package, so any pack change
requires a code change and a new baseline tag.

## New tests

* `test_missing_benchmark_dir_returns_launch_error` — absent benchmark
  → F_LAUNCH_ERROR, queue front intact.
* `test_benchmark_pass_advances` — valid benchmark → pass, entry
  admitted, evidence file written.
* `test_stale_evidence_revalidates_on_version_change` — version bump
  triggers re-run (fresh child invocation) rather than reusing stale
  evidence; pass still succeeds.
* `test_encoding_surface_fail_closed_launch_error` — entry without
  proposal_encoding surfaces as F_LAUNCH_ERROR, not F_RENT_FAIL, not
  pass.
* Existing rent-stub tests updated to (a) use the new
  benchmark.json convention, (b) attach a trivial identity
  proposal_encoding to queue entries so the subprocess can install
  the candidate, and (c) accept (entry, accepted, version) gate
  signature (previously only (entry)).

## Boundary

* Human-approval gate remains fail-closed denier (approval_callback=None
  → False → "awaiting human"); its wiring is authorized as the next
  slice AFTER rent, separately.
* No joint-set rent in this version.
* Live admission remains HOLD until human gate is wired and tested.
* L-S-5 item 3 (Programme L) remains held.

## Test log

```
Ran 62 tests in 529.663s
OK
```

Files unchanged vs base a5209488: core.py, search/compare_executors.py,
search/compare_subprocess.py.
