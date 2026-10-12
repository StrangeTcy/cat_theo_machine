# W16 — Distributed heuristic search & partitioned prover swarm

**Swarm · Phase 3 · Suite slot `test27` · Prereqs: W2 ⬜ (open — do not start until it lands) · W13 ✅ (done)**

Read `delegation/README.md` first — shared invariants, environment facts and pitfalls are
binding here.

**Sequencing:** W2 (`delegation/W02-rpc-mtls-mesh.md`) is not implemented. `networking/` and
`mesh.py` do not exist yet. You may start on the *partitioning policy and its verification*
against the existing file+subprocess transport, but the mesh-backed half of this brief must
wait for W2 to report green. Coordinate rather than duplicating W2's transport work.

## What already exists

- `run_search_worker_mode(worker_mode, result_path, timeout_seconds)` in `main.py` — one
  worker, one search mode, result snapshot out. Modes are resolved by
  `_search_worker_mode_label` / `_search_worker_mode_heuristic`.
- `search/compare_subprocess.py` — spawns those workers with `subprocess.Popen` and a
  `<result_path>.manifest.json` sidecar. This is a working partitioned-execution harness
  already: `search/compare.py`, `compare_executors.py`, `compare_state.py`,
  `compare_packets.py`, `compare_rules.py`, `compare_nat.py`, `compare_trees.py`,
  `compare_semantics.py`, `compare_attempts.py`, `compare_console.py`.
- `search/engine.py`, `search/api.py`, `search/modes.py`, `search/model.py`,
  `search/patricia.py`, `search/serialization.py`, `search/runtime.py`,
  `search/chain_utils.py`, `search/heuristics` (top-level `heuristics.py`).
- `planner.py` — multi-pass backward planner with goal decomposition and witness synthesis,
  verified by `test15_multi_pass_planner.py`. **This is your partitioning substrate**: a
  decomposed goal is a natural work unit.
- `persistence.py` — snapshot codec with `HYGE_SEARCH_WORKER_RESUME_DERIVATION=1` resume from a
  snapshot; hypergraph `nodes`/`edges` now persist, so a worker's discovered state survives.
- `snapshots/search_compare/` held committed comparison runs in earlier lineages; those were
  excluded as generated artifacts. Keep yours out of git too.

`search/distributed_engine.py` **does not exist** — the DAG names it as your deliverable.

## Goal

1. **Frontier partitioning**: split a search frontier into disjoint work units with a
   deterministic, reproducible partition function (hash of the frontier node's canonical form
   is a reasonable basis). Disjointness must be *proved in the suite*, not assumed: no unit
   explored twice, none dropped.
2. **Work-stealing**: idle workers steal from busy peers. Stolen work must produce results
   identical to locally-run work — same derivation, same receipt. If W2's mesh is available,
   steal over it; until then, steal over the file/manifest transport and keep the policy
   transport-independent.
3. **Determinism and monotonicity**: the merged result must be independent of worker count and
   scheduling order. Two runs with 1 worker and 4 workers must yield the same proof (or the
   same failure). Version handling lives in `graph.py`; snapshot versions must be monotonic
   across merges — this is the seam W17 depends on, so keep it clean.
4. **Termination and failure accounting**: a worker that dies mid-unit must not lose the unit;
   the swarm either re-dispatches or reports the loss explicitly.

## Done-definition

- `search/distributed_engine.py` runs a partitioned search over a real problem from the
  existing packs, with 2–4 subprocess workers, and produces the **same** derivation as the
  single-process baseline. The suite asserts equality of the result, not merely success.
- Partition disjointness and coverage asserted directly.
- A worker-kill test showing no work is silently lost.
- Speedup reported honestly. On 2 vCPU with ~3.8 GiB RAM, four workers will *not* give 4×;
  report the measured number and the memory high-water mark. A negative or flat speedup is a
  legitimate finding — record it rather than tuning until it looks good.
- Machine purity: partition keys and frontier state are machine terms; no Python `dict` of
  machine values in runtime paths (§5.2). Plain Python for scheduling bookkeeping is fine —
  keep the boundary explicit.

## Files

- New: `search/distributed_engine.py`, `validation/test27_distributed_prover_swarm.py`.
- Extend: `search/compare_subprocess.py` (reuse its spawn/manifest idiom), `main.py` (a swarm
  CLI mode), `planner.py` (only if work units need a decomposition hook).
- Do not edit `core.py`. Do not weaken `checker_b.py` or the promotion ledger.
- Keep run artifacts out of git.

## Verification

`PYTHONPATH=/home/user .venv/bin/python -u validation/test27_distributed_prover_swarm.py`
green, plus all existing suites green (19 at the time of writing, plus whatever W2 and others
have added by then — check `validation/` for the current highest slot and report the total).
Highest regression risk: `test15` (planner), `test12` (persistence cold resume), `test1`/`test4`
(planner lifecycle). Bind any sockets to port 0. Keep the suite under ~180 s: subprocess
suites are the slowest thing in this repo.

## Non-goals

Consensus and ledger sync (W17's brief), the RPC/mTLS transport itself (W2's brief — consume
it, do not reimplement it), new search heuristics, and `core.py` edits.
