# Programme C — Agent Spawn Charter

**Base tag name:** `eng-base-0@1374464`
**Annotated tag object:** `a52094888a30099150e6310b4b171ee2af97fe36` (not a commit — corrected 2026-09-19; see protocol/C-INT-8A.md)
**Peeled base commit:** `137446435362a9727c2f7c181c663adab9d4c357`
**Current C-INT parent:** `cint-integrated-7^{}` = `65103a048eeea282a448213ccc23ce74cf023c35`
**Base tag (legacy shorthand):** `eng-base-0@1374464` → tag object `a52094888a30099150e6310b4b171ee2af97fe36`.
**Integration branch (8A):** `work/C-INT/eng-base-0/r2` (authorized); this checkout `arena/01a0bbdd-cat-theo-machine` tracks the same parent content.

The earlier (incorrect) mapping `eng-base-0 → 428ecdc` is recorded here as a
superseded artifact; the authorized frozen base is `a520948`. The `eng-base-0`
local tag was not moved. See the r2 reconciled C-INT report in
`programme_c/tests/artifacts/2026-09-16/` for full provenance.

Three worker branches (C-A `6dc74cc` / `ca-bounded-pool-2`,
C-B `259cba8` / `cb-interface-2`,
C-C `8528206` / `cc-join-admission-2`)
have been merged into this INT worktree. All three report `ready for integration`.

Next bounded item (per opus 4.7 acceptance):
1. Wrap C-A dispatch around the existing `search-worker` subprocess entry
   point (`python -m <pkg>.main search-worker ...` in `main.py:1292`), stamping
   every result envelope with K_SNAPSHOT_ID / K_OBLIGATION / K_ASSUMPTION_HASH /
   K_TASK_ID / K_ATTEMPT_ID, preserving readiness-ack, isolated cwd, budget,
   cancellation. No replacement of `_fill_parallel_workers`/`_spawn_parallel_executor`.
2. Wire C-C admission gates to existing validity/rent/human hooks in
   `search.compare_console` / `search.compare_packets`, publishing admitted
   state to an on-disk manifest before `admit_next` returns.

No core.py edits. No Experiment 4. No conda Python. No FLT explanation.
Programme L untouched. Joint-set rent deferred.
