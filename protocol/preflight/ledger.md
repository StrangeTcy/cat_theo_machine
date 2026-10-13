# SNAPSHOT-PREFLIGHT ledger — 2026-09-10

agent: this lane (Layer D engineer, branch `arena/01a05d5d-cat-theo-machine`)
source commit: `3c4382b439ca9eface4d88992b18779ac5f93ff4` (recorded from a
fresh `git ls-remote origin` at work start; sandbox had reset HEAD to the
branch base — recovered by `git reset --hard` onto the pushed tip with the
disk content already identical, ledgered here)
permitted write branch: `arena/01a05d5d-cat-theo-machine`

## Reproduction (charter §1.1, R8 pin)

Probe: swallow -> `raise` in `LearnedMemoryCheckpointTest` (testsuite.py),
live during every measurement, reverted before this commit. Repro driver
boots like the shard runner (`boot_from_packs(PACK_PATHS, _runtime_namespace())`)
and constructs the checkpoint test directly (its `__init__` IS the run).
Full transcript of all three contexts: `verification/2026-09-10-snapshot-preflight.txt`.

  solo (no registrations):            PASS, probe never fired
  109 (historical position):         PASS, probe never fired — exactly 109
                                     guarded sites accepted with the REAL
                                     acceptor (~6.6s/site cursor cost is the
                                     historical context itself), then the
                                     checkpoint test: 60.07s
  full (288 sites at this cut):      see RESULT line in the verification
                                     transcript; verdict appended below
                                     after the run completed.

## Named mechanism

The historical crash class at this boundary is the CODEC TYPE GAP on host
objects, not a size threshold. Measured directly (`boundary_probe2.py`):
`SnapshotCodec` capture of a host object WITHOUT machine identity (a bare
class, module, or plain instance) walks into the identity index and dies on
a raw `AttributeError: type object 'Edge' has no attribute 'id'` — an
unlabelled host crash. Inside `LearnedMemoryCheckpointTest` that crash lands
in the `except Exception: self.result = M.false_value` swallow: a boundary
violation became a label-less failure. That is the mechanism the preflight
was asked to surface.

## Repair (this commit)

`persistence.py`: the capture boundary now REFUSES BY NAME.
`_captured_object_id` and the red-black insertion both check identity first;
any object without one raises
`RuntimeError("Snapshot capture refused: host object without machine
identity: <name>")` at the violating object instead of an anonymous
AttributeError deep in the index. Refusal semantics are unchanged (capture
never accepted such objects); only the failure became a named machine-visible
fact at the tooling boundary. `__dict__`-bearing instances are still refused
explicitly rather than captured as empty shells (which could not restore).

Tests added to the default suite (shard-guarded, standard registration
pattern):
  snapshot_host_class_refusal_test — a leaked class object at the boundary
    must raise, never be captured silently.
  snapshot_restore_rebinds_constructor_class_test — capture of a class
    reference round-trips to the namespace symbol (rebound class), not a
    hollow instance.

## Negative-control results

  boundary_probe2 (pre-repair): raw AttributeError — the defect, shown live.
  boundary_probe2 (post-repair): RuntimeError with the object name — refusal
    by name; Edge-instance capture/restore unaffected (0.035s, marker
    self-consistent, restored twin marked).
  M2 journal driver after the repair: 27/27 checks ok (the rename-away
    audit + open recorder still see exactly the observations path — the
    added identity checks touch no new files).
  M1 comparison driver after the repair: 18/18 ok.
  Focused boundary family (LMC, dependency_graph checkpoint, save-timeout
    atomicity, 3 preserves tests, the 2 new refusals) registered and run via
    tools/agent_workers/focused_repro.py with the probe LIVE:
    "All the tests have passed." (8/8)

## Remaining failure / missing

  - The 109-era ORIGINAL crash (whatever it was at commit 109's parent) does
    NOT reproduce at this cut in solo or 109 context: the observations-side
    machinery no longer routes bare classes into the codec. No traceback to
    show; recorded as reproduced-silent with the probe live, per
    "a missing result is reported as missing".
  - A full-288-context run and both production shards with the repair are
    the INT admission measurements; this lane reports the focused results
    only.
  - No new labels minted; core.py untouched; no tag cut (engineers do not
    cut tags).

Remote tip at completion: recorded in the verification transcript footer.
