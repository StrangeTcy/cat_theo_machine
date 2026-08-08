# Analysis v2 — Mode Comparison Architecture

**Date:** 2026-08-08  
**Branch:** `instrument-filter-applicability-timings`  
**Current HEAD:** `88dcd29` — "trying to make searchcomparison work properly and in parallel"

---

## 1. Current State

### What's Already Working

**Independent mode comparison is the default:**
- `_search_compare_enable_shared_root_fast_paths = false_value` by default
- Five modes (DFS, BFS, AStar, Beam, RewriteDFS) run independently
- Each mode gets its own fresh runtime and heuristic
- Fork-based parallelism works on Linux/Mac
- Sequential fallback works on Windows (spawn)

**Performance fixes completed this session:**
- `NatLess` replaced with `GMPLessText` for large-number comparisons (proof.py:1676)
- `PrettyRule` fixed to print rule IDs instead of full rule bodies (engine.py:1678)
- Multi-premise theorem application gated to reduce log spam (proof.py:1805)
- Added `_search_probe_disable_applicable_shards` flag to keep modes internally sequential

---

## 2. The Main Problem (Now Fixed)

**Before:** Each mode worker searched and found a plan, then the parent called `BuildDerivation` again on every successful mode's plan. This caused:
- Duplicate proof construction work
- Massive `DEBUG: build-derivation: plan=[apply ...]` log spam
- Parent rebuilding what children already computed

**After (this session):** 
- Worker builds derivation once inside `_SearchIndependentModeAttemptWorker` (runtime.py:547)
- Worker returns complete `SearchAttempt` through queue
- Parent receives attempt and never calls `_mode_attempt_from_plan` on it (compare.py:739)
- Sequential path also builds derivation inline in `_independent_mode_attempt` (compare.py:570)

**Key changes:**
1. `runtime.py:547-606` — Worker now builds `derivation`, `proof_cost`, `total_cost`, and `SearchAttempt` before putting result in queue
2. `compare.py:720-744` — Parallel path receives complete `attempt` from payload[2], skips replay
3. `compare.py:570-618` — Sequential path builds derivation inline using `mode_runtime.constructor_registry`

---

## 3. Architecture Summary

### Parallel Path (fork, Linux/Mac)
```
Parent:
  ├─ Launch 5 Process workers via multiprocessing.get_context("fork")
  ├─ Each worker gets: mode, start, goal, rules, heuristic, constructor_registry
  └─ Wait for results

Child Worker (per mode):
  ├─ Run SearchAPI → plan, search_cost
  ├─ Build derivation (if successful)
  ├─ Build proof_cost, total_cost
  ├─ Construct SearchAttempt
  └─ Put complete attempt in queue

Parent (receive):
  ├─ Get attempt from queue
  ├─ Never call BuildDerivation again
  └─ Rank attempts, pick best
```

### Sequential Path (spawn, Windows)
```
Parent (sequential loop):
  ├─ For each mode:
  │   ├─ Create fresh mode_runtime
  │   ├─ Run SearchAPI → plan, search_cost
  │   ├─ Build derivation inline (mode_runtime.constructor_registry)
  │   ├─ Build proof_cost, total_cost
  │   ├─ Construct SearchAttempt
  │   └─ Return attempt
  └─ Rank attempts, pick best
```

Both paths now build each derivation **exactly once** per successful mode.

---

## 4. What Was NOT Done

**No subprocess.Popen with file-based IPC:**
- Rejected: snapshot bootstrap (`boot_from_snapshot`)
- Rejected: hidden `search-comparison-worker` entrypoint in `main.py`
- Rejected: "failure artifact" files
- Kept: simple `multiprocessing.Process` with fork, queue-based IPC

**Why:** The existing fork approach works fine. Windows spawn limitation is acceptable (sequential fallback). File-based IPC adds unnecessary complexity.

---

## 5. Remaining Work

### Priority 1: Labels cleanup
- Add `HeuristicPerformanceLabel = HeuristicPerformanceLabel()` instantiation to labels.py
- Add to `SNAPSHOT_SYMBOL_NAMES`

### Priority 2: HeuristicPerformance record
- Define `HeuristicPerformance(attempt, elapsed_milliseconds, worker_pid, completion_reason)` in search/model.py
- Build in child worker
- Store in comparison summary

### Priority 3: Auto-save snapshot
- After each mode finishes, update snapshot without waiting for user "pause"
- Requires wiring snapshot save into comparison finalize

---

## 6. Key Decisions

**Registry isolation:** Each mode builds its derivation in its own `mode_runtime.constructor_registry` (sequential) or child's `runtime.constructor_registry` (parallel). This keeps modes independent.

**No shared-root path by default:** The old packet/broadcast comparison engine is still present but disabled. Independent comparison is the default.

**Queue protocol change:** Worker queue payload changed from `(mode, status, plan, search_cost, elapsed, pid, error_text)` to `(mode, status, attempt, elapsed, pid, error_text)`. Parent extracts `search_cost` via `SearchAttemptSearchCost(attempt)()`.

---

## 7. Acceptance Test

Run `python main.py cold debug`. Expected behavior:
- Five mode processes start (or sequential on Windows)
- Each mode searches and builds its own derivation once
- Parent logs show mode finishes with no subsequent `DEBUG: build-derivation: plan=[apply ...]` replay
- Best mode selected, comparison stored

**Log should show:**
```
SearchComparison: SearchDFS finished status=... elapsed=...
SearchComparison: SearchBFS finished status=... elapsed=...
...
```

**Log should NOT show (for each mode):**
```
DEBUG: build-derivation: plan=[apply ...]
DEBUG: apply-action: apply multi-premise theorem rule
DEBUG: apply-action: apply multi-premise theorem rule
...
```

---

## Summary

The core issue—parent-side derivation replay—is now fixed. Each mode builds its derivation once in its own process/runtime context. The parent receives completed attempts and ranks them without re-proving anything. The architecture uses simple fork-based multiprocessing with queue IPC, no file orchestration, and no hidden entrypoints.
