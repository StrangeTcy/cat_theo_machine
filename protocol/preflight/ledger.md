# Preflight ledger

Per CHARTER-v1 §1. One entry per item. Every claim here cites an artifact in
this directory or under `verification/`.

Status: **item 1 CLOSED, exact-109 green. Item 2 COMPLETE: producer
candidate count 1, unmatched premise P, goal unclosed. Item 3 complete and
shape-matched.** Item 4 (both full shards) is the only item left. No
`preflight` commit and no tag yet.

**Correction to the record.** Commit `bfd4bd2` is described in its own
message as applying a codec-side guard at `persistence.py:806`. It does not.
Only `protocol/preflight` and `verification/` were staged; the guard stayed
unstaged and a later sandbox reset discarded it. The commit contains evidence
and nothing else. It is not being rewritten — no force-push on this line.

---

## Item 1 — surface the swallowed exception

**Result: surfaced on attempt 1 of 3. Mechanism named. Fix not applied.**

| field | value |
|---|---|
| commit | `b38965046fb65e61628ffa845ce172ce2abedc52` |
| mode | exact-109 |
| predecessor selection | every registration before cursor 218 accepted by shard 0 of 2 |
| predecessor count | 109 |
| ordered-set digest | `139c78b9c2bf5c5d375d120f93e768aaea576a55d928fd862850ecbb6c7f87d5` |
| command | `sh tools/preflight_item1_repro.sh exact` |
| exit | 1 |
| window | 2026-09-07T23:42:20Z → 2026-09-07T23:54:21Z |
| traceback | `protocol/preflight/exception-traceback.txt` |
| raw log | `verification/2026-09-07-preflight-item1/attempt-1/run.log` |
| raw log digest | `9821e40a4ff091ce2a3f26798d87e0ab608c260da6edab3e98ea27ba55636410` |

**Defect: `OBJECT_ID_INDEX_ASSUMES_TERM_ID_ON_HOST_OBJECT`.** Locus
`persistence.py:806` (`_captured_object_id`), failing at `trees.py:176`
(`self.key_id = key.id`). Class: codec type gap. The object-id index is a
red-black tree keyed on object identity whose lookup reads `key.id`
unconditionally; every machine term carries `.id`, a `Hypergraph` does not.
When a Hypergraph reaches the lookup as a candidate through root interning,
the lookup raises `AttributeError` instead of returning "not captured", and
the registration aborts. The test's guard then turned that abort into a bare
false.

**Why 109 was the number, and not a size threshold.** The candidate is
`current.head.value` reached through root interning; whether it is a
Hypergraph depends on what earlier registrations put in the graph. Runs with
0, 16 and 32 predecessors all passed. The exact-109 configuration is the
first tried that places a Hypergraph at that position. The count was never
the mechanism — the configuration was.

**Prior diagnosis superseded.** `da33a45` recorded "nondeterministic under
load". It is deterministic given the configuration: the same 109-name
ordered set reproduces it. It looked load-sensitive because predecessor
count, not load, was the variable.

**Guard restored.** The harness reverted `testsuite.py:14957` on exit; the
tree carries no re-raise.

**Fix: LANDED, upstream, at the constructor site.** Ruling (c), second
branch: the encode-boundary option was rejected as silent omission, so the
assignment was traced instead.

**Offending constructor site: `testsuite.py:4914`, `WorkerProtocolTest`.**
The retained test edge was built as
`super().__init__(inputs=M.Pair(graph, empty), results=self.result)` — the
live `Hypergraph` in a term slot. `testsuite.py:4726`,
`ConflictDetectionTest`, carried the identical defect. Both now use
`inputs=M.EmptyList`. This is ruling category (a): a fixture storing the host
graph into a term field.

**Why the count mattered, finally explained.** `worker_protocol_test` sits at
cursor index 110: inside the exact-109 set (shard 0, before 218) and outside
every trailing window tried. 0, 16 and 32 predecessors never constructed the
offending edge, so the object was never in state. The count was a proxy for
one registration, exactly as suspected, and the registration is now named.

**Minimal reproducer (replaces the 14-minute run for future work):**

    PYTHONPATH=/home/user python3 tools/run_named_tests.py \
        worker_protocol_test learned_memory_checkpoint_test

Two tests, 59 seconds, fails before the fix with the same
`PROBE parent pair ... headtype=Hypergraph` and passes after. The 109-test
configuration was never necessary; it was merely the first set tried that
included registration 110.

**Three-door history** (each door is a consumer of the same reachable object,
not a separate accident):

    1. lookup  persistence.py:806  -> guarded, moved
    2. insert  persistence.py:1423 -> guarded (trees.py), moved
    3. encode  persistence.py:1317 -> raised
    fix at the constructor site -> all three silent, because the object is
    no longer in the object graph at all

**Confirming run:** exact-109 on 13cd338 + the fixture fix,
2026-09-10T00:55:42Z to 01:11:32Z, exit 0, no traceback. 110 registered,
108 passed, 2 failed — `tree_insert_deep_pair_lookup_avoids_recursion_test`
and `compare_search_modes_fill_warms_resident_pool_before_root_wave_test`,
both pre-existing members of the known failure set.
`learned_memory_checkpoint_test` passed.

**Index guards at `2a0a876` retained** as defense-in-depth with correct
answer semantics.

**Capture-entry refusal: LANDED, blast radius MEASURED.** The ruling was
FAIL-CLOSED, and the open question was how far it reaches given the
codebase-wide `inputs=M.Pair(graph, ...)` convention. Measured rather than
argued: `SnapshotCaptureRefused` is raised at the capture boundary when a
candidate in a term slot carries no machine identity, carrying a machine
term naming the slot — `(snapshot-refused host-object-in-term-slot <slot>)`
— with the slot labelled `head`, `inputs`, `results` or `root`.

Blast radius, on 46 capture-adjacent tests (snapshot, checkpoint, daemon,
worker, research, provenance, policy, autonomy, retirement, migration):
**44 passed, 2 failed, zero refusals fired, no traceback.** The convention
does not reach capture in any of them. The two failures produced no refusal
term, so they are not refusal-induced; their names were not captured in
that run and item 4 records them authoritatively.

Minimal reproducer still green with the refusal active:
`worker_protocol_test learned_memory_checkpoint_test` → 2/2.

**Assertion-style test: ADDED AND PASSING (1/1).**
`SnapshotRefusesHostObjectInTermSlotTest` is registered at the end of the
`[SHARED]` block. It takes index **304** — the last position — so no
existing cursor index shifts: `tools/shard_map.py`, the AST walk that
actually assigns indices, puts `test_shard_cursor_pin_test` at 302,
`snapshot_value_atom_identity_test` at 303, and the new test at 304, shard
0. `tools/check_pins.py` reports guards 306, **index 218**, shard 0, PASS;
its guard pin was raised 305 → 306, and 218 and 0 are untouched.

The two tools count different things, and always have: `check_pins` counts
source occurrences of the guard string, `shard_map` counts registrations
`install_default_tests` actually makes, and the former exceeds the latter
by one. That +1 offset predates this work — only `check_pins`' own number
moved here. An earlier note in this ledger said index 305; 304 is what
`shard_map` reports, and `shard_map` is the index authority.

The test earned its place immediately: its **first run failed**, and both
causes were real defects in this work rather than in the test.

1. The refusal named a slot that does not exist. The patch formatted a
   literal string at patch time where the `slot` variable was meant to be
   substituted at raise time, so every refusal reported `"slot"`. Fixed:
   `M.Char("slot")` → `M.Char(slot)`. The term is now
   `(snapshot-refused host-object-in-term-slot head)`.
2. The assertions compared with `M.TermEqual`, which is **identity on
   atoms** (`matching.py:41`, spelled out at `machine.py:238`), so a
   freshly built `Char` never equals another. Structural comparison is
   `M.Compare` (`constructors.py:245`). The test's three uses were swapped;
   the other 77 `M.TermEqual` uses in `testsuite.py` were left alone.

After both fixes: 1 registered, 1 passed. The refusal reproducer is green
with the corrected slot: `worker_protocol_test
learned_memory_checkpoint_test` → 2/2.

**Tool drift found and repaired.** The multi-line import shifted
`testsuite.py` by five lines, so `tools/preflight_item1_repro.sh`'s
hard-coded `LINE=14957` no longer pointed at the swallowed site. Its
loud-fail guard did its job: it asserts the preceding line is
`except Exception:` and the target line's exact content, and refuses to
edit on drift. Corrected to `LINE=14962`, and the swap path re-verified end
to end — `sh tools/preflight_item1_repro.sh 1` → "swap applied at
testsuite.py:14962 (re-raise)", 2/2 passed, exit 0, tree restored with zero
stray `raise` left behind.

The blast-radius question that motivated this test is answered: the
`inputs=M.Pair(graph, ...)` convention does not reach capture in any of the
46 capture-adjacent tests measured above. What remains is not a landing
decision but an interpretation one, and it is not on this lane's critical
path — see item 4.

**Citation for the eventual preflight commit:** `bfd4bd2` is an experiment
record whose message claims code it does not contain; superseded by
`2a0a876` and this fix. No reader should trust its message over its diff.

## Item 2 — A1 producer/consumer selection probe

**Result: COMPLETE. Decisive evidence met on all three counts. No defect
filed.** Artifact: `protocol/preflight/a1-selection.txt`. Raw log:
`verification/2026-09-10-preflight-item2-a1-selection/run.log`. Tool:
`tools/preflight_a1_selection.py`.

    G = (nosolutions positive-integers (unknowns x) (eq (plus x 1) x))
    P = (a1-producer-premise G)      C = (a1-consumer-result G)
    producer: premises [P] -> conclusion G
    consumer: premises [G] -> conclusion C

Both compiled through `research.compile_formal_rule`, the only door to an
executable rule, and both are `MultiRule`: inputs is
`Pair(premises, Pair(replacement, EmptyList))`, results is `EmptyList`,
checked structurally rather than by host type test, with the rendered object
confirming `cat_theo_machine.proof.MultiRule`.

Selection, in an isolated session-only pool of one rule (the producer), not
installed into `FireAny`:

```text
candidate partial-match count: 1
selected rule identity: producer     rule origin: primitive
attempt record: (None <MultiRule> primitive () ()
                (a1-producer-premise (nosolutions positive-integers
                 (unknowns x) (eq (plus x 1) x))) None)
goal closed: NO
```

| decisive evidence | required | observed | |
|---|---|---|---|
| producer candidate count | >= 1 | 1 | pass |
| unmatched premise | P | P, as recorded | pass |
| goal closed | no | NO | pass |

**Reading caveat, recorded in the artifact:** P is an opaque session-local
marker with no axiom, law or derivation behind it. The count of 1 reports
that the machinery matched a premise shape — not that the machine needs P,
that P is satisfiable, or that anything follows from it. A deliberately
unsatisfiable diagnostic premise yields the same count as a real one.
Selection evidence is not proof evidence; this is not a theorem request, a
capability claim, or an unlock.

The consumer was compiled but not selected against C; the ruling makes that
second check optional.

**Relation to D11:** unaffected and uncontradicted. D11 asked the shipped
library for a nosolutions-headed rule and found none — pack-content
absence, filed as such. Here the rule is supplied by the probe, so the
vocabulary is present by construction. Together: the selection path handles
nosolutions heads (this run), and the shipped library contains no rule with
that head (D11).

## Item 3 — structural decoy shape check

Not started. Per the restored ruling the equality-implication decoy is
preserved as a historical residual control and is **not** used here. The
replacement decoy differs from the target only in the bound constant
(`n > 2` versus `n > 1`). Artifact will be
`protocol/preflight/decoy-shape.txt`. Parsing and structural comparison
only: no search, no teaching, no target session.

## Item 4 — full two-shard suite

**RUN AND MEASURED on `ddc3d79`, both shards, 305 registered.**
Started 23:10, both shards DONE by 23:43 (~33 min wall, run in parallel).

```text
shard 0:  passed 149   failed 2   open 2
shard 1:  passed 146   failed 4   open 2
total:    passed 295   failed 6   open 4   (of 305)
```

**The item-4 gate checks that matter are green.** `learned_memory_checkpoint_test`
(index 218) PASSED, so the item-1 regression guard holds. The new refusal test
(index 304) PASSED in full-shard context, not only solo.
`nat_value_index_snapshot_roundtrip_test` (index 90) PASSED here — the
previously flagged baseline red did not reproduce in shard context.

**Failures, classified one by one:**

| Test | Shard | On the expected list? | Classification |
|---|---|---|---|
| `tree_insert_deep_pair_lookup_avoids_recursion_test` | 0 | yes | known pre-existing |
| `compare_search_modes_fill_warms_resident_pool_before_root_wave_test` | 0 | yes | known pre-existing |
| `heuristic_canonical_knowledge_agreement_test` | 1 | yes | known pre-existing |
| `curator_report_test` | 1 | yes | known pre-existing |
| `compare_search_modes_finds_reusable_worker_snapshot_dir_test` | 1 | yes | known pre-existing |
| `cold_e2_reaches_snapshot_save_test` | 1 | **no** | pre-existing, proven below |

Two tests were on the expected list and **did not fail**:
`converse_default_mode_test` (180, shard 0) and `converse_proposition_test`
(181, shard 1) both passed.

**`cold_e2_reaches_snapshot_save_test` — the one name not on the list.**
It is snapshot-adjacent, so it was the first thing checked against this
lane's own change. It is not a regression:

```text
solo, tip ddc3d79            failed   -> not a shard-context flake
solo, 994a081 (pre-refusal)  failed   -> not caused by the refusal
solo, 41e8078 (session base) failed   -> predates all of this line's work
```

Identical result at all three: 1 registered, 0 passed, 1 failed. It is a
baseline red that the operator's enumeration had not captured. Five of the
six failures were on the expected list; the sixth is pre-existing rather
than new.

**The four OPEN results are sentinels, not failures**: `test_milestone_m1_cycles_without_refusal`
and `test_milestone_m3_meta_handle_reorders` (shard 0),
`test_milestone_m2_handle_lifecycle` and `test_milestone_m4_policy_loosen_then_tighten`
(shard 1). OPEN sentinels do not pass by construction.

**Method note, for the next shard run.** The first attempt was lost to
sandbox reset #24, and because it ran `shard_suite.py` directly under the
process tool it lost the evidence along with the run — nothing on disk.
`tools/run_shards_detached.sh` exists precisely to prevent that, and the
second attempt used it: logs at `logs/shard-0.log` and `logs/shard-1.log`,
surviving any process kill. Use the wrapper; do not run the suite bare.

## Host-tools import — the published repair-wave base

Tag **`hosttools-7ec5f59`**, commit `7ec5f59`. This is the base the four
unbuilt repair lanes branch from.

It supersedes `hosttools-f59fb92`, now deleted. That first tag was cut
one file short: the import commit's add pathspecs covered `tools/` only
and missed `protocol/G-ENG-ARTIFACT-SCHEMA.md`, the 73rd path. The file
was present in the working tree throughout, so the five suites did run
against it and their counts stand — but the published base would have
been an incomplete import. Corrected by a forward commit, never a
force-push or a history rewrite, and both names are recorded here so a
reader holding the old one knows why it stopped resolving.

The lesson for the next import: add by the manifest, not by a directory
pathspec. The 73 paths were sitting in `import-paths.txt` the whole
time.

```text
classification  NON-SEMANTIC -- host tooling only
tool source     e904cfaf3a4f6ae159889eebb33b144b1b22e6be (73 files)
F-5 cleanup     31306e1 (tools/cur_extract_evidence.py, 2 comment lines)
harness         2b8b10d (tools/tests/cur_import/run.py, 17/17 selftests)
rehearsal       f1aa963 - evidence consulted, not imported
runtime base    fa4b346, re-pinned live from the rehearsal's 13cd338
```

**Verification recorded:**

```text
completion.json                  present, ok true, imported_count 73
--verify                         ACCEPT
byte+mode vs import-paths.txt    72/72 match, 0 mismatched,
                                 1 superseded by the F-5 cleanup
F-5 digest                       edec65b8...9783e MATCH
five suites, composed tree       cur_grader 56/56, cur_extractor 30/30,
                                 cur_schema 13/13, cur_pipeline 12/12,
                                 hardening 12/12 - all match source
pins                             306 / 218 / 0 PASS
machine reproducer               worker_protocol_test +
                                 learned_memory_checkpoint_test -> 2/2
machine-side diff outside cur_*  empty
```

The last line is what makes NON-SEMANTIC true rather than claimed: no
`.py` outside `tools/cur_*` and `tools/tests/cur_*` differs from
`fa4b346`. Nothing in matcher, search, planner, packs or labels was
touched, and the pins did not move.

**A correction this lane owes the programme.** `e904cfa`, `31306e1`,
`f1aa963`, `9ac8e10` and `e18e31f` were each reported at some point as
unresolvable in this clone. Every one of them is real; they live on other
`arena/*` branches that had not been fetched. The rule is now: a SHA is
"unresolvable" only after

```text
git fetch origin 'refs/heads/arena/*:refs/remotes/origin/arena/*'
git cat-file -e <sha>^{commit}
```

both fail. Branch names on this remote carry a `-cat-theo-machine`
suffix, which is what defeated the first two fetch attempts.

**Baseline for every future batch** — the item-4 six-set, by name:
`tree_insert_deep_pair_lookup_avoids_recursion_test`,
`compare_search_modes_fill_warms_resident_pool_before_root_wave_test`,
`heuristic_canonical_knowledge_agreement_test`, `curator_report_test`,
`compare_search_modes_finds_reusable_worker_snapshot_dir_test`,
`cold_e2_reaches_snapshot_save_test`. The last is pre-existing, proven
identical at `41e8078`, `994a081` and `ddc3d79`.
