# Preflight ledger

Per CHARTER-v1 §1. One entry per item. Every claim here cites an artifact in
this directory or under `verification/`.

Status: **item 1 surfaced and named; fix outstanding.** Items 2, 3, 4 not
started. No `preflight` commit and no tag yet.

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

**Outstanding, in order:** fix lands in a separate commit after `preflight`;
then the suite reruns clean. Attempts 2 and 3 exist in the ruling to
establish non-reproduction; the exception appeared on attempt 1, so the
"exception appears" branch is taken and they are not required for closure.

---

## Item 2 — A1 producer/consumer selection probe

Not started. Constructed per the restored ruling: goal
`(nosolutions positive-integers (unknowns x) (eq (plus x 1) x))`, marker
terms `(a1-producer-premise G)` and `(a1-consumer-result G)`, producer and
consumer compiled through the real rule compiler, both confirmed `MultiRule`,
producer placed in an isolated session-only rule pool, candidate selection
run against `G`. Artifact will be `protocol/preflight/a1-selection.txt`.
The goal must stay unclosed; this is a selection probe, not a theorem.

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
