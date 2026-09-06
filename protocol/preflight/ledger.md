# Preflight ledger

Remote tip at hand-off: 12d2d46519fd7a45ae283bff60c277ac309d8150

## step 1 — swallowed exception

```text
status: blocked
mechanism: open (test absent)
named defect: LearnedMemoryCheckpointTestMissing
locus: testsuite.py has no LearnedMemoryCheckpointTest;
       research.py is absent on this tree
traceback: protocol/preflight/exception-traceback.txt (none produced)
```

The charter names a class and a 109-predecessor `_register_test` repro.
Neither is on this cut. Step 1 is not skipped; it is blocked. No swap,
no re-raise, no revert.

## step 2 — producer/consumer pair

```text
status: not run
reason: blocked at step 1
```

## step 3 — decoy shape

```text
status: not run
reason: blocked at step 1
file: protocol/preflight/decoy-shape.txt not written
```

## step 4 — two-shard suite

```text
status: not run
reason: blocked at step 1
failure set: unrecorded
```

## step 5 — commit/tag

```text
commit: this ledger (preflight record, not a complete preflight)
tag: none — charter forbids a preflight tag until all four items are recorded
wave 1 base tag: none
```

Wave 1 engineers do not branch. INT does not write track features.
