# W18 — Kernel: `NatValueIndex` lookup cost makes every arithmetic sweep quadratic

**Infra (kernel) · Phase 0 · Suite slot `test30` · Prereqs: none · Owner: coordinator sign-off
required — this touches `trees.py`, which is kernel**

> **Status: landed 2026-10-15** on `arena/500df21f` (`5d07bf8`), integrated the same day with a
> purity cleanup of the layout probe (`596d40b`). Per-call cost is flat at ~0.04–0.07 s from 50 to
> 900 interned nats; `test30` 18/18; full gate 30/30. See DAG §6.7 (the fix) and §6.8 (the
> integration). The measurements below are the *before* picture and stay as the record.

Read `delegation/README.md` first. Invariant 2 applies in full: `trees.py` is kernel, so
the fix may use no Python native on a machine value, and `core.py` stays untouched. This
brief exists because the W6 remainder measured the cost and had to design around it
(`validation/test26_flt_descent.py` keeps its bounds small for exactly this reason, and
says so in its source).

## The measurement (2026-10-14, fresh `make_fresh_runtime()`, 2 vCPU, no profiler unless stated)

| situation | `NatFromRep` cost |
| :--- | :--- |
| fresh runtime, 50 new values around 1000 | ~0.2 s per call |
| the same 50 values again (index hits) | ~75 ms per call |
| after ~200 more nats interned, new values | ~0.6 s per call |
| 300 nats interned, hit / miss+insert (under cProfile, ~2–3× overhead) | 0.14 s / 2.9 s |

Every `math/arithmetic` edge (`Add`, `Multiply`, `Modulo`, `Gcd`) returns its result
through `NatFromRep`, so this is the cost of one arithmetic operation, and it grows
linearly with the number of distinct nats the process has interned. A sweep of `n`
operations therefore costs `Θ(n²)`. Concretely: `test22` spends most of its ~215 s here;
`test26`'s 109 additions + 136 products + a few dozen others take ~85 s; the W15 tutor's
counterexample sweeps are bounded at 12 for the same reason.

## Where the time goes (`cProfile`, 20 hits + 20 misses at 300 entries)

`math/peano.py:NatFromRep._from_value` → `trees.TreeLookup(NatValueIndex, key)`:

1. **`TreeLookup._lookup_tree` falls back to a linear scan on a miss.** When
   `TreePatriciaLookup` returns `EmptyList` it calls `_lookup_entries(TreeEntries(tree)(),
   exact_key)`, which walks *every* entry and recomputes `ExactKey(entry_key, registry)` for
   each before a `TreeTermEqual`. 27.4 s of the 61.5 s profile, in 20 calls — i.e. the
   whole index is scanned once per miss, and for `NatFromRep` a miss is the normal case
   (every new value). This is the quadratic term.
2. **`TreePatriciaLookup` itself is ~0.37 s per call at 300 entries** (15 s / 40 calls):
   `_find_choice` scans a branch's choices with `TreePatriciaTokenEqual`, and bucketed
   leaves are scanned entry by entry with `TreeTermEqual`. Each of those comparisons is a
   chain of kernel edges.
3. **`TreeInsert`** (via `_nat_value_index_store`) is ~0.7 s per new value at 300 entries.
4. **Constant factor, out of scope:** every kernel object allocation calls `uuid4()`
   (`core.py: make_id`) — 8.5 M calls, 35 s of the 61.5 s profile. `core.py` is off-limits
   by §5; this is the floor under everything and is recorded, not attacked, here.

`_is_bucketed_root` was suspected first (it walks the tree) and measured at 9 ms per
lookup — negligible. Do not spend time there.

## Goal

Make a `NatFromRep` miss cost `O(key length)` plus the insert, independent of the number
of entries, without changing what `TreeLookup` returns for any key.

## Done-definition

1. `validation/test30_nat_index_lookup_cost.py`: on a fresh runtime, intern 50 new values,
   then 300 more, then 50 more; the third batch's per-call time must be within a small
   constant (say 1.5×) of the first batch's, and every value must round-trip through
   `NatRepOf`. Also: hits for the first batch still return the *same* node (identity), and
   two distinct values never alias.
2. The whole gate green, in particular `test12` (persistence: the index and the
   constructor registry are restored by spawned shard workers — the tree *layout* may be
   part of what a snapshot pins; check `snapshots/` is unchanged by a boot), `test13`
   (playground), `test18`, `test22`, `test26` (which should get faster; report the before
   and after wall clocks), `test3`.
3. `trees.py` still has zero forbidden constructs (`grep` for `isinstance|hasattr|type(|
   __class__` must find nothing new).

## Fix sketch (verify before trusting)

- The fallback in `_lookup_tree` exists for roots that are *not* bucketed (legacy or mixed
  trees). If `_is_bucketed_root` is true and the Patricia lookup misses, the key is absent;
  return `EmptyList` without scanning. Check `TreeInsert` keeps the root bucketed so this
  shortcut is always taken for `NatValueIndex`.
- Inside `TreePatriciaLookup`, the bucket scan compares with `TreeTermEqual` after an
  `IdentityCompare`; for digit-list keys the exact key is interned through `_interned_key`,
  so the identity hit should be the common path — measure whether the structural compare
  is ever needed for `NatValueIndex` keys and, if not, why the interning misses.
- `_lookup_entries` is also what `_interned_key` falls back to through `TreeKeyStore`;
  check that path too.

## Non-goals

`core.py` (the uuid cost), changing the key encoding (`NatValueKey` is a decimal digit
list; changing it changes snapshots), or caching on the host side with a dict — that
would be a forbidden construct in kernel code and a second source of truth beside the tree.

## Report back

Per `delegation/README.md` “Reporting back”, plus the before/after table above re-measured
on the same machine, and the wall clocks of `test22` and `test26` before and after.
