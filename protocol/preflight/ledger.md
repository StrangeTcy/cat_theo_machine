# Preflight ledger

Remote tip at INT hand-off: `d3de45a179cc76b6c157473a3ca8d684dcf91294`

Charters committed as text-only: `6002caf6ae3b6779d46aed59e3c149ec18f48375`

## 1. Swallowed exception

Mechanism: **open — locus missing**.

Named defect: `MissingLearnedMemoryCheckpointTest`

The class, the `except Exception` swallow, and the 109-predecessor repro are
not on this tip. See `protocol/preflight/exception-traceback.txt`.

No repair commit. No diagnostic edit remains in the tree.

## 2. Producer / consumer selection

`nosolutions` producer as specified for A1: **not in the tree**. Not constructed
under that name (A1 content is operator-sealed).

Host check `protocol/preflight/run_multirule_check.py` (venv, not conda):

```
producer_class MultiRule
consumer_class MultiRule
candidate_rule arithmetic_equation_is_symmetric
partial_match_on_x_plus_1_eq_x True
```

Both constructed rules compiled to `MultiRule`. Selection on `x + 1 = x`
(`ExprEqLabel(ExprAddLabel(x, 1), x)`) against
`arithmetic/arithmetic_equation_is_symmetric` returned a candidate match.
This is not the A1 `nosolutions` pair.

## 3. Decoy shape

See `protocol/preflight/decoy-shape.txt`.

**DECOY REDESIGN REQUIRED**

INT stopped. No decoy was designed here.

## 4. Two-shard suite

Not run. Failure set: **not collected**.

Reason: gate already blocked at step 3; CHARTER-v1 forbids proceeding past a
decoy mismatch. Full suite admission waits on a complete preflight.

## 5. Tag

No `preflight-<shortsha>` tag. Incomplete gate does not authorize a
measurement or Wave 1 base.
