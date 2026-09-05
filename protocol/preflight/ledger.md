# Preflight ledger

Remote tip at INT hand-off: `d3de45a179cc76b6c157473a3ca8d684dcf91294`

Charters committed as text-only: `6002caf6ae3b6779d46aed59e3c149ec18f48375`

Engineering unblock: items 1–2 closed without operator wait. Item 3
decoupled to `protocol/F.md` (F-op sessions only).

## 1. Swallowed exception — CLOSED

`git log --all -S LearnedMemoryCheckpointTest` hits only the charter and
this ledger line (`6002caf`, `97595a0`). No class, no swallow, no
109-predecessor repro exists in this repo line.

Declaration: **this cut has no `LearnedMemoryCheckpointTest`. Step 1 is
inapplicable as written.**

See `protocol/preflight/exception-traceback.txt`.

## 2. Toy nosolutions producer / consumer — CLOSED

A1 sealed pair remains absent. Toy pair on
`ExprEq(ExprAdd(x, 1), x)`:

Host check `protocol/preflight/run_multirule_check.py`:

```
producer_class MultiRule
consumer_class MultiRule
toy_nosolutions_producer_partial_match True
toy_nosolutions_consumer_partial_match True
pack_rule arithmetic_equation_is_symmetric
pack_rule_partial_match True
item2_closed True
```

Both toy rules compile to `MultiRule`. Both are candidate partial matches
on `x + 1 = x`. Pack rule `arithmetic_equation_is_symmetric` also matches;
that is D11 surface, not the A1 pair.

## 3. Decoy shape — DECOUPLED

Moved to `protocol/F.md`. Gates F-op sessions only. Does not block
S/E/G/F-tools engineering. File still reads `DECOY REDESIGN REQUIRED`
for F-op. INT did not redesign the decoy.

## 4. Two-shard suite — RUN

Script: `protocol/preflight/run_two_shard_suite.py`
Log: `protocol/preflight/two-shard-suite.log`

Shard 0 (`TestShardConfigure` index 0 of 2): elapsed 28.83s.
Failure set:

- `converse_default_mode_test`

Shard 1 (`TestShardConfigure` index 1 of 2): crashed during
`install_default_tests` at `ConversePropositionTest.__init__`
(`testsuite.py:7448` / `core.py:120`):

- `AttributeError: 'Thingy' object has no attribute 'tail'`

Exact failure set for engineering baseline:

1. `converse_default_mode_test`
2. shard-1 install crash: `ConversePropositionTest` / `Thingy.tail`

## 5. Tag

Engineering base tag: `eng-base-0` (also `eng-base-0@<hash>`).
Not a measurement tag. F-op remains gated by `protocol/F.md`.
