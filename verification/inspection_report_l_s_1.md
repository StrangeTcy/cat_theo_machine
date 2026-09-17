# L-S-1 Inspection Report: Call-Path Inventory, Bypass Loci, and Defect Matrix

**Date:** 2026-09-17  
**Track:** Programme L / Story Track (L-S)  
**Status:** Cut L-S-1 Completed (Inspection Only — No Interface Modification)  
**Engineering Base:** `eng-base-0@1374464`  
**Auditor / Inspector:** Machine Inspection Agent  

---

## 1. Executive Summary & Scope

Per the L-INT architectural disposition of 2026-09-17, this inspection establishes the empirical baseline for the Programme L Story Track (`L-S`). 

The machine holds rich structured terms (`Derivation`, `SearchAttempt`, `PlannerObligation`, `ContextSearchHistory`, `Hypergraph` context). However, prose and status reporting currently bypass story compilation, resulting in direct, uncurated string dumping from workers and execution loops into `stdout`.

In strict adherence to the L-S-1 charter:
- **Zero code interfaces have been added or replaced** in this turn.
- A complete call-path inventory from machine terms to string sinks has been traced.
- Every bypass locus where `INT`, `E`, `G`, or `F-tools` circumvents narrative merging is identified.
- An inventory of existing story and report terms is established.
- A defect matrix classifying the last ten bad machine outputs across the seven failure axes has been constructed.
- A definitive determination regarding the extension of existing story terms is rendered.

---

## 2. Call-Path Inventory: Machine Terms to String Sinks

Every execution path that transforms machine terms (`Atom`, `Pair`, `Edge`, `Hypergraph`) into strings terminates in one of six sinks:

```text
[Machine Source Terms]
   ├── (A) Hypergraph / Knowledge / Terms ──> PrettyTerm / GMPRepText ──> String Sink 1 (prettyprinting.py)
   ├── (B) Plan / Actions / Derivations ────> PrettyAction / PrettyPlan ─> String Sink 2 (proof.py)
   ├── (C) SearchState / Jobs / Workers ───> Scheduler & Focus Text ────> String Sink 3 (compare_semantics.py)
   ├── (D) Agenda / Benchmark Results ──────> Formatted f-strings ───────> String Sink 4 (main.py CLI)
   ├── (E) Console & Stop Controls ────────> Interactive Prompts ───────> String Sink 5 (compare_console.py)
   └── (F) Report Terms (Legacy/Txt) ──────> RenderCuratorReport ───────> String Sink 6 (graph.py.txt)
```

### Sink 1: Term & Knowledge Textualization (`prettyprinting.py`)
- **Entry Points:** `M.PrettyTerm(x, registry)()`, `PrettyPair`, `PrettyValue`, `GMPRepText`.
- **Call Path:** `term` $\to$ `_show(x)` $\to$ recursive `Pair` traversal $\to$ `_geometry_tag_text(tag)` or `_nat_value(x)`.
- **Characteristics:**
  - Hardcoded tag lookup maps (`prettyprinting.py:355–397`).
  - Dynamic class name inspection debt (`label.__class__.__name__` at `prettyprinting.py:417–426`).
  - Emits flat strings directly; lacks rhetorical relations or aggregation.

### Sink 2: Proof Action & Derivation Printing (`proof.py`)
- **Entry Points:** `PrettyAction`, `PrettyPlanItem`, `PrettyPlanChain`, `DebugTerm`, `_debug`.
- **Call Path:** Derivation plan list $\to$ `PrettyPlanChain._walk(plan)` $\to$ `PrettyAction(item)` $\to$ string concatenation (`"apply " + ...`, `"rewrite ... at ..."`).
- **Output Channel:** Direct write to `sys.stdout.write("DEBUG: " + message + "\n")` via `_debug` (`proof.py:116–127`).
- **Characteristics:** Uncurated step-by-step trace; no narrative coalescence.

### Sink 3: Search Telemetry & Worker Semantics (`search/compare_semantics.py`)
- **Entry Points:** `_state_scheduler_text`, `_active_worker_focus_text`, `_job_focus_text`.
- **Call Path:** `SearchState` / `SearchJob` $\to$ field extraction via `SearchJobFrontierSize`, `SearchJobExpanded`, etc. $\to$ string concatenation (`+ " phase=" + ... + " status=" + ...`).
- **Characteristics:** Dumps 12 raw key-value counters into a single monolithic string per mode/packet.

### Sink 4: Top-Level Agenda & Lifecycle Reporting (`main.py`)
- **Entry Points:** `_run_theorem_cases`, `_print_table`, `cold`, `warm`, `test`.
- **Call Path:** Benchmark / agenda execution loops $\to$ `print(f"{label}: proved in {elapsed} seconds")` or `print(f"{label}: not proved after {elapsed} seconds")`.
- **Characteristics:** Binary outcome reporting; suppresses intermediate blockers, failure loci, and proof cost metrics.

### Sink 5: Interactive Console & Progress UI (`search/compare_console.py`, `search/ui.py`)
- **Entry Points:** `_SearchProgressTicker.start`, `_ComparisonConsoleMixin._comparison_read_action`.
- **Call Path:** Timer events $\to$ `_debug("trying " + self.mode_text + " now")`, `print("Type 'pause', 'stop'...")`.
- **Characteristics:** Ad-hoc console control messages without structured provenance.

### Sink 6: Machine-Native Report Rendering (`graph.py.txt`)
- **Entry Points:** `RenderCuratorReport` (`graph.py.txt:16504–16554`).
- **Call Path:** `report` term $\to$ machine loop iterating over class rows $\to$ string assembly with `GMPSuccText` $\to$ returns text term.
- **Characteristics:** Pure machine loop without host Python collections; demonstrates native string rendering precedent, but confined to curator proposals rather than general runtime storytelling.

---

## 3. Track Bypass Inventory: Where INT / E / G / F-Tools Bypass Story Merging

In the current codebase, **100% of track outputs bypass the Story Track (`S`)**:

| Track | Primary Source Files | Current Execution Path | Current String Sink | Story Merge Bypassed? |
|---|---|---|---|---|
| **INT** | `main.py`, `runtime.py` | `main._run_theorem_cases`, `runtime.boot_from_packs` | `print()`, `_debug_log()` directly to stdout | **YES (100%)** |
| **E** | `search/compare_executors.py`, `search/compare_packets.py` | `_SearchIndependentModeAttemptWorker`, resident lease loops | `_debug()` directly with worker PID & packet tokens | **YES (100%)** |
| **G** | `proof.py`, `planner.py` | `prove()`, `BuildDerivation()`, `PlannerStep()` | `_debug()` with AST dumps and rule attempts | **YES (100%)** |
| **F-tools** | `audit_pack_check.py`, `testsuite.py` | Standalone assertion loops, pack loaders | `print(f"All tests passed...")` directly | **YES (100%)** |

**Mechanism of Bypass:**
Each track formats its own internal facts locally using primitive string addition (`+`) or Python f-strings, immediately passing the result to `print()` or `_debug()`. No track emits an intermediate machine term to a shared narrative bus or story compiler.

---

## 4. Inventory of Existing Story Terms and Merge Mechanics

A comprehensive audit of active Python files (`hyge/*.py`, `search/*.py`) reveals:

1. **Active Python Universe:**
   - **No `Story` or `StoryFragment` term exists.** 
   - Historical records exist in `context.py`: `search_history` (`Ctx.ContextSearchHistory`) storing a machine `Pair` list of `SearchAttempt` records.
   - Proof records exist in `proof.py`: `Derivation(start, end, plan, cost)`.
   - Goal records exist in `planner.py`: `PlannerProblem`, `PlannerObligation`, `PlannerDependency`, `PlannerJob`.
2. **Archived / Reference Universe (`graph.py.txt`):**
   - Contains formal report terms: `CuratorReport`, `PromotionReport`, `RobustnessReport`, `TestResultsReport`.
   - Contains `RenderCuratorReport`: an `M.Edge` that processes an alist report term into plain text.
3. **Merge Mechanics:**
   - No narrative merge operators exist anywhere in the active codebase. 
   - The only "merging" in active code is graph/tree merging in `search/compare_trees.py` (`_merge_generated_trees` for search branches) and alist substitution in `matching.py`.

---

## 5. Defect Matrix: Analysis of 10 Representative Bad Outputs

The following matrix categorizes 10 concrete outputs from actual repository logs (`logs/cold_debug_stage1_runtime.log`, `logs/cold_debug_stage1_runtime_long.log`, `logs/engel_e1_prove.debug.log`, and `main.py` runs):

| # | Concrete Output Locus | Defect Taxonomy Axis | Concrete Defect Description |
|---|---|---|---|
| **1** | `logs/cold_debug_stage1_runtime.log:520`<br>`DEBUG: search-bfs-stage: trying theorem; current=Knowledge([...7 unreduced facts...])` | **Selection + Realization** | Dumps 7 unreduced AST terms on every step; prints raw internal constructor names; misses actual rule applicability state. |
| **2** | `logs/cold_debug_stage1_runtime.log:480`<br>`DEBUG: search-compare: SearchBeam worker pid=1846 elapsed=126.6s completed packet status=running frontier=2 expanded=0 generated=1 peak=2 total=0` | **Structuring + Wrong Audience Cut** | Low-level engineering telemetry surfaced as uncurated stream; zero aggregation across parallel mode workers. |
| **3** | `logs/cold_debug_stage1_runtime.log:471`<br>`DEBUG: search-compare: ignoring stale SearchBFS packet result token=10 expected=10` | **Unsupported Claim** | Asserts staleness while displaying identical token numbers (`10 == 10`), concealing the true causal reason for rejection. |
| **4** | `logs/engel_e1_prove.debug.log:340`<br>`DEBUG: prove: no derivation found \n EMPTY True \n UNREACH False \n ISDER False` | **Missing Blocker + Selection** | Emits bare host boolean literals; fails to identify which obligation failed, why search terminated, or what to do next. |
| **5** | `main.py:1042-1047`<br>`loaded snapshot roots: \n constructor_registry = <hyge.core.Pair object at 0x7f...>` | **Realization + Wrong Audience Cut** | Surfaces raw Python object memory addresses instead of semantic machine state counts or snapshot version validity. |
| **6** | `logs/cold_debug_stage1_runtime.log:600`<br>`DEBUG: search-compare: SearchBFS packetized frontier into 1 batches; 0 frontier states remain...` | **Aggregation + Realization** | Emitted redundantly per mode; grammatically unaggregated ("1 batches"); fails to synthesize overall frontier readiness. |
| **7** | `logs/engel_e1_prove.debug.log:12-28`<br>`DEBUG: prove-stage: replacement did not match goal` *(repeated 15 times consecutively)* | **Aggregation + Structuring** | 15 consecutive identical lines for `IsReal`, `Positive`, `NonNegative`, etc. No coalescing into a single summary of failed candidate heads. |
| **8** | `main.py:441`<br>`tao_problem_1_1: not proved after 600.00 seconds` | **Missing Blocker + Wrong Audience Cut** | High-level binary failure label completely hides the fact that timeout occurred during initial cursor build, not in search. |
| **9** | `08August2026 -- opus 5 answer.md:7`<br>`DEBUG: search-dfs-stage: cursor build: applicability scan complete; elapsed=245.057s applicable-rules=38` | **Structuring + Salience Inversion** | Critical system bottleneck (4-minute applicability scan stall) buried as low-salience debug chatter rather than elevated as primary blocker. |
| **10** | `logs/cold_debug_stage1_runtime.log:475`<br>`DEBUG: search-compare: resident executor 6 pid=1857 finished SearchDFS packet and returned status=running...` | **Structuring + Wrong Audience Cut** | Asynchronous interleaved process chatter completely prevents reading the logical progression of the search attempt. |

---

## 6. Determination: Extension Point for Story Terms

1. **No Collision**: There is no active `Story` or `StoryFragment` term in the codebase. Defining `StoryFragment` and `StoryEdge` does not conflict with any existing type.
2. **Native Extension**: The proposed `StoryFragment` must be implemented as an explicit machine term (`M.Edge` or tagged `Pair` structure) whose fields are strictly machine-native atoms (`Atom`, `Pair`, `EmptyList`).
3. **Extension Point**:
   - The story track `S` belongs in a dedicated module `hyge/story.py` (or `search/story.py` if scoped to search comparisons), exposing:
     - `StoryFragment` term constructor and field accessors.
     - `StoryEdge` typed dependency constructor (`supports`, `causes`, `contrasts`, `supersedes`, `elaborates`).
     - Deterministic merge operators (`coalesce_repeated_status`, `promote_blockers`, `cause_chain`, `contrast`, `elide_redundant_ids`, `section_by_decision`).
     - Projection operators for the 4 cuts (`operator`, `engineer`, `review`, `machine`).
   - The existing sinks in `prettyprinting.py`, `proof.py`, `search/compare_semantics.py`, and `main.py` will not write directly to `stdout`; instead, they will emit fragments into the cut's story collector.

---

## 7. Exit State & Next Step

Cut **L-S-1 (Inspection Only)** is complete and fully documented. 

Per the architectural disposition:
- No interfaces have been altered before inspection.
- The path for **Cut L-S-2 through L-S-5** (defining the canonical story term, routing track facts, implementing merge operators, adding the 4 cuts, and installing provenance-based back-checks) is now unblocked and ready for execution.
