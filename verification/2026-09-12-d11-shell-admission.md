# D11-SHELL admission — INT record

date: 2026-09-12 (Europe/Moscow)
integrator: INT session arena/01a09270 (sole active integrator)
verdict: ADMIT. Tag `live-ingress/d11-shell-1`.

## Source (verified exact SHAs)

```text
source branch:  arena/01a09396-cat-theo-machine (remote tip == evidence commit)
code commit:    95d248872cff4f4f65cbd635827cad9c6b83aa66  ("[SHARED] Recover D11 diagnostic isolation from surviving files")
evidence:       b31f63715a2f9d17bde4badade7c8ee1d31165db  ("[SHARED] Record D11 isolation recovery verification")
parent:         99ab2f02c29e03410319f98bd40f2b167aecea2e  ("[SHARED] D11 shell frontier characterization")
```

Parent chain verified: `95d2488~1 == 99ab2f0`, `b31f637~1 == 95d2488`,
`FETCH_HEAD == b31f637`. Admitted base `0d7e1b6` (`live-ingress/admission-1`)
is an ancestor of `99ab2f0` (merge-base `0d7e1b6`); the chain
`0d7e1b6..99ab2f0` is the single commit `99ab2f0`. Equivalence to the lost
`eedcd4f` is NOT established and is not claimed anywhere in this record.

## Scope (net 0d7e1b6..95d2488, reviewed in full)

Runtime (7 paths), characterization-only, no core.py, no testsuite.py:

- `labels.py` (+24): 4 labels (class + singleton + sync names):
  NosolutionsIntroduction, ForallImpliesDecomposition,
  NeedContradictionFromArbitrarySolution, NeedBinderSafeImplication.
- `persistence.py` (+4): the same 4 in SNAPSHOT_SYMBOL_NAMES. Fully
  registered in both tables, so the D1 pins (40/198) are undisturbed.
- `packs/shell-characterization.pack.yaml` (new): `surface:` mappings for
  the 4 labels + 2 `diagnostics:` records (nosolutions_introduction,
  forall_implies_decomposition). Zero proof rules.
- `packs.py`: `LoadedPack(diagnostic_rules=())` (defaulted, backward
  compatible); the loader compiles `diagnostics:` specs with the pack-local
  surface compiler but never builds Rule/MultiRule objects and never enters
  graph rules. A matching diagnostic cannot fire, replay, prove, or conclude.
- `runtime.py` (+10): `last_foreground_diagnostic` field; `prove()` matches
  diagnostic shells first and on a match records the instantiated
  requirement and returns EmptyList (no proof attempted).
- `main.py` (+1/+7): the new pack in PACK_PATHS; talk mode reports a matched
  diagnostic as "Foreground diagnostic: unsupported shell requires X. This
  capability report is not a theorem request; no proof is submitted."
- `tools/d11_gate.py` (+447/-34): version-2 gate (23 conditions, safety
  probe, live-ingress probe). Tool-only; not imported by the suite.

Docs in the imported commits: `verification/2026-09-12-d11-shell-phase2/`
(5 transcripts, part of 99ab2f0). Evidence commit `b31f637` (7 transcripts
under `verification/2026-09-12-d11-shell-isolation-recovery-95d2488/`) is
PRESERVED, not imported: the source branch stays on remote as published,
its SHAs are cited here, and no old evidence is relabeled.

Out of scope / still open before any F proof session (per programme relay):
LOGIC-CHECKER-ENG, TEACH-BINDING-ENG, TRAINING-ACCEPTANCE-ENG,
F-TOOLS-REPLAY-ENG, combined INT semantic tag. This tag is NOT F-proof-ready.

## Reconstruction

Session branch (docs-only since the tag) + cherry-picks, rehearsed first
in a detached scratch worktree, then replicated on the branch:

```text
tested (scratch, pre-reset):  0e4fc2a + f1d1cb4 (99ab2f0) + c3097a7 (95d2488)
integrated (rebuilt):         0e4fc2a + 9202d8a (99ab2f0) + 03778de (95d2488)
tree check:                   03778de^{tree} == 181bd2d9bb390cf7fc2b2cee6ffd63643f17fb48
                              (== pre-reset tested tree; see Rebuild note)
                              git diff 95d2488 03778de -- <7 runtime paths> -> EMPTY
tag:                          live-ingress/d11-shell-1 -> 03778de (annotated 34cdf11)
tree:              181bd2d9bb390cf7fc2b2cee6ffd63643f17fb48
```

Both cherry-picks applied cleanly (session-side changes since the tag are
DISTRIBUTION.md + 2 verification files; no code overlap).

Rebuild note (sandbox reset #4): the first publication attempt's local
objects (commits b93ff82/154a0d1/01689c8, tag object 25565e9, scratch
c3097a7/f1d1cb4, and all of /home/user/d11shell including the focused
rerun logs) were destroyed unpushed. INT re-cherry-picked the same
remote source SHAs (95d2488/99ab2f0, unchanged and re-verified) onto
0e4fc2a; the rebuilt import tree reproduces 181bd2d9 EXACTLY, so the
admitted product is byte-identical and all pre-reset measurements
transfer. Evidence files were restored from the surviving tree (blank
artifact transcripts re-verified byte-identical; only its commit header
changed, digest now eb7de5d4; shard logs untouched -- they carry no
local SHAs). The old local SHAs (b93ff82/154a0d1/01689c8/25565e9/c3097a7)
are retained in this note only as tombstones; every live citation uses
the rebuilt SHAs. Reset #4 also established that scratch OUTSIDE the
repo is not safe: /home/user/d11shell vanished with the sandbox, so
D10's "nothing survives" extends beyond running processes.

## Gates (all re-run by INT on the scratch candidate; nothing inferred)

```text
tools/d11_gate.py                        23/23 gated conditions passed, exit 0
tools/d11_gate.py --safety-probe         8/8 spoof cases unclosed
                                         (closed=False proof-candidates=0), exit 0
tools/d11_gate.py --live-ingress-probe  PASS (parsed == submitted == received;
                                         diagnostic-only, empty derivation)
python -m cat_theo_machine.ingress_tests PASS (parser/dispatcher/scope regressions)
py_compile (6 changed files)             PASS
```

Interpreter: /usr/bin/python (3.11.2), gmpy2 2.3.1, yaml 6.0.3 (user-site;
reinstalled after a sandbox reset wiped ~/.local). Post-rebuild, all five
gates were re-run on a confirmation worktree at 03778de (same tree
181bd2d9): 23/23, 8/8, PASS, PASS, PASS -- reproduced exactly.

## Shards (hardened detached runner, attempt 20260912-144714-1684)

```text
shard 0: 151 passed / 2 failed / 2 open (m1, m3)   elapsed 1757s
shard 1: 149 passed / 4 failed / 2 open (m2, m4)   elapsed 2254s
total:   300 passed / 6 failed / 4 open of 310
```

Failure set test-for-test identical to `live-ingress/admission-1`
(verified against verification/2026-09-12-int3-shard-{0,1}.log):

- shard 0: tree_insert_deep_pair_lookup_avoids_recursion_test,
  compare_search_modes_fill_warms_resident_pool_before_root_wave_test
- shard 1: heuristic_canonical_knowledge_agreement_test, curator_report_test,
  cold_e2_reaches_snapshot_save_test,
  compare_search_modes_finds_reusable_worker_snapshot_dir_test

310 registrations, no new tests, pins undisturbed. Full logs:
verification/2026-09-12-d11shell-shard-{0,1}.log. The runs executed
pre-reset against tree 181bd2d9; the rebuilt import reproduces that tree
exactly, so the result transfers without re-running the shards.

## Blank controls (Invariant 2, on the tag)

Detached worktree at the tag, talk mode, cold isolated HYGE_SNAPSHOT_DIR
per run. Run A (research triple) and Run B (ladder + why) transcripts are
BYTE-IDENTICAL to the admission-1 blanks; state-B holds
research_snapshot.json only (no workers spawned); stderr empty both runs.
The admission changes nothing on the research path or the ladder.
Silence baseline for the new tag:
verification/2026-09-12-BLANK-CONTROLS-D11-SHELL-1.txt (`eb7de5d4`;
header commit line updated to the rebuilt SHA, transcripts untouched).

## Judgment

The import is admitted on substance: exact-SHA source verified, runtime
scope reviewed line by line and genuinely characterization-only (diagnostic
records are data, never rules; the prove() short-circuit declines with a
report instead of stalling), all five lane gates re-run green by INT, both
shards identical to baseline, blank controls identical. The D11-SHELL
ancestry note in DISTRIBUTION §7 ("tag is ingress-only") is superseded by
this admission for the new tag. No authorization beyond the standing INT
remit was needed: every number above was measured here.
