# W32 — Swarm unit-boot cost

**Infra · Phase 7 · Suite slot `test44` · Prereq W16 ✅ (independent of Phases 4–6)**

Read `delegation/README.md` first. Read DAG §4 W16, §6.3, §7.6 and §8 (W32). Do not
re-execute `W16-distributed-prover-swarm.md`.

## Why this worker exists

`test27` is 51/51 but speedup is **0.84×** (baseline 82 s vs swarm 98 s on 2 vCPU;
later 213 s vs a faster baseline). The proof of `engel_e2` lives in one branch, so
the critical path is one unit's *boot* plus search. Unit-boot is ~12–30 s. The
brief's ~180 s suite budget was not attainable at that cost. A restore defect
(pickle recursion on `all_rules`) was already fixed in §6.3; the remaining cost is
the boot itself, not the crash.

## Goal

Cut per-unit boot wall-clock enough that it is no longer the reason swarm is slower
than solo, **or** produce a precise account of what still costs 12–30 s and why it
cannot move (kernel `uuid4()` floor, pack load, snapshot decode).

1. Profile a unit boot (build / save / load separately, as the ingest probe does).
2. Fix host-layer codec / `search/distributed_engine.py` costs you can name.
   `core.py` is out of scope. Do not introduce a second serialisation of a machine
   term (§5 rule 7).
3. Re-run `test27` and report speedup; do not tune the problem to look faster.

## Done-definition

- `validation/test44_swarm_boot_cost.py` green: measures boot phases, asserts a
  bound you chose from the profile (or asserts the floor with evidence).
- `test27` 51/51, `test12` 10/10, `test25` 51/51 still green.
- Speedup reported, not tuned. Partial (measured floor, no win) is acceptable.

## Files

`persistence.py`, `search/distributed_engine.py`. Not `core.py`, not `networking/`
(that's W33).

## Non-goals

k-way scaling across many problems, WAN (W20, done), kill-phase accounting (W33).
