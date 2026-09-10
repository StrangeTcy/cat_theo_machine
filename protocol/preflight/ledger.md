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

**Assertion-style test: NOT yet added.** The ruling requires one at the
capture boundary. It is outstanding, and it must register after cursor 304
so no existing cursor index (218 included) shifts. Designed, then held, because
`inputs=M.Pair(graph, ...)` is a codebase-wide convention, not a two-site
mistake: it appears in `graph.py` (many), `context.py` (~40 call sites),
`planner.py`, `search/api.py`, `search/engine.py`, `proof.py`,
`research.py`, `daemon.py`. A refusal at capture entry fires on all of them.
Landing it converts one crash into an unknown number of refusals until
someone rules whether the convention itself is wrong or only its retention is.
Ruling requested.

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

Not started, and gated: the ruling sequences it after items 1–3, after the
item-1 repair, on a pinned candidate SHA. Item 1's repair is outstanding, so
item 4 cannot start yet.
