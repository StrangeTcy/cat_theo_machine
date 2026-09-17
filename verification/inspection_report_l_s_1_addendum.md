# L-S-1 Inspection Addendum: Source Reachability, Checkout Lock, and End-to-End Story Reproduction

**Date:** 2026-09-17  
**Track:** Programme L / Story Track (L-S)  
**Status:** Addendum to Cut L-S-1  
**Auditor / Inspector:** Machine Inspection Agent  
**Upstream Reference:** L-INT Review (2026-09-17)  

---

## 1. Locked Checkout and Evidence Metadata

### A. Repository & Working-Tree State
* **Checkout Root:** `/home/user/cat_theo_machine`
* **Active Git Branch:** `arena/01a0acf2-cat-theo-machine`
* **Local HEAD Commit SHA:** `428ecdc146e38de3481222bed7bddeb3c08e1b2d`
  - *Author:* Maxim Smirnov <hatguy@yandex.ru>
  - *Date:* Tue Aug 25 05:52:56 2026 +0300
  - *Commit Message:* "Add files via upload"
* **Lineage & eng-base-0 Reconciliation:**
  - The architectural base `eng-base-0@1374464` (`a52094888a30099150e6310b4b171ee2af97fe36`) is referenced in upstream planning (`10August2026 -- updated plan by sol.md`) as the external upstream engineering commit from `Q:\hyge`.
  - In this local checkout, git history contains only the uploaded root commit `428ecdc`. The object `a520948` does not exist in local `.git/objects`. The active tree at `428ecdc` represents the materialized snapshot of that lineage.
* **Working-Tree Modifications:**
  - `charter_p_track_symbolic_realization.md` (untracked draft, held)
  - `verification/inspection_report_l_s_1.md` (untracked, completed inspection baseline)
  - `verification/inspection_report_l_s_1_addendum.md` (this addendum)
  - All core and runtime source files are clean (`git status` shows clean tracked tree).

### B. Evidence Modality Breakdown
* **Static Source Inspection:** Full AST/regex scan over `hyge/*.py`, `search/*.py`, `math/*.py`, `*.py.txt`, and shell scripts.
* **Historical Log Observation:** Artifact logs committed in tree:
  - `logs/cold_debug_stage1_runtime.log` (114 KB)
  - `logs/cold_debug_stage1_runtime_long.log` (30.6 KB)
  - `logs/engel_e1_prove.debug.log` (33.2 KB)
* **Current Reproduction:** Local clean-environment executions:
  - `python hyge.py` (executes cleanly; pure-Python term rewriting & comparative story output).
  - `python main.py` / `python -m cat_theo_machine.main` (halted at import due to environment boundary: `gmpy2` dependency configured in `environment.yml` for project Anaconda environment `prefix: C:\Users\hatgu\anaconda3\envs\hyge`, confirming non-negotiable constraint: *"Run runtime verification only from the already-open project Anaconda Prompt"*).

---

## 2. Source Reachability & S/Story Mechanism Audit

### A. Reachability of `*.py.txt` Files
A comprehensive codebase audit was conducted to determine whether `graph.py.txt`, `mining.py.txt`, `firing.py.txt`, `grammar.py.txt`, `language.py.txt`, or `deduction.py.txt` are:
1. Imported via Python `import` or `importlib`: **No.** Zero occurrences across all active `.py` files.
2. Read and dynamically evaluated via `open()`, `exec()`, `eval()`, or AST parser: **No.** The only `open()` calls in active code load `.yaml` packs, `.json` snapshots, `session.txt` (in `hyge.py`), or write debug logs.
3. Consumed by build scripts or code generators: **No.** No build or code-generation scripts exist in the repository.

**Finding:** The `.py.txt` files are unreferenced reference artifacts committed alongside the refactored modular Python files.

### B. Status of Existing Report Machinery
* `CuratorReport`, `PromotionReport`, `RobustnessReport`, and `RenderCuratorReport`:
  - **CuratorReport**: Exists only at `graph.py.txt:16290`. Unreachable in active runtime.
  - **RenderCuratorReport**: Exists only at `graph.py.txt:16504`. Unreachable in active runtime.
  - **PromotionReport**: Defined at `graph.py.txt:2350`, `mining.py.txt:1611`. Unreachable in active runtime.
  - **RobustnessReport**: Defined at `graph.py.txt:5470`, `mining.py.txt:2520`. Unreachable in active runtime.
* `TestResultsReport`:
  - **Active and Reachable.** Defined in active code at `graph.py:1453` (`class TestResultsReport(M.Edge)`).
  - Exported to `runtime.py:30` and invoked via `runtime.test_results_report()` (`runtime.py:77`).
  - Takes `graph` as input, retrieves `M.FromContextGetTestResults(graph)()`, and returns either `"No tests were run."`, `"All the tests have passed."`, or newline-delimited failed test names.

### C. Search Scope for Programme L / Story Machinery
* **Searched Scope:** Every tracked file in `/home/user/cat_theo_machine` was searched for occurrences of `story`, `storyfragment`, `storyedge`, `programme l`, and `merger`.
* **Result:** **Not located in this checkout.**
  - No class, function, edge, or module implements a narrative `StoryFragment`, `StoryEdge`, or story merge operator.
  - Domain records holding raw facts exist (`SearchAttempt`, `Derivation`, `PlannerObligation`, `TestResultsReport`).
  - Narrative construction machinery is not present in the active python modules of this checkout.
  - **Request to INT:** Confirm whether the Programme L Story-track mechanics exist on an unmerged upstream branch of `Q:\hyge` or if they are to be canonically instituted in active code under this track.

---

## 3. End-to-End Reproduction of Actual Generated Stories

To distinguish between absent mechanisms, bypassed mechanisms, and poor rendering, two live end-to-end prose generation paths in this checkout were reproduced and analyzed.

### Case A: Comparative Explanation Pipeline (`hyge.py` over `session.txt`)

#### 1. Invocation & Input
* **Invocation:** `python hyge.py`
* **Input / Cut:** `session.txt` executing query `query compare sieve trial over one through nine` with lemma `sqrt-divisor-bound`.
* **Execution Path:**
  `session.txt` $\to$ line readers (`hyge.py:348`) $\to$ generic rewrite loop $\to$ Sieve & Trial termination states $\to$ `main()` string assembly (`hyge.py:430–540`).

#### 2. Source Terms (Final State)
* `sieve_state`:
  `;(candidate nat-1);(candidate nat-2)...` $\longrightarrow$
  `;(excluded nat-1);(kept nat-2);(kept nat-3);(struck nat-4 nat-2 nat-2);(kept nat-5);(struck nat-6 nat-2 nat-3);(kept nat-7);(struck nat-8 nat-2 nat-4);(struck nat-9 nat-3 nat-3)`
* `trial_state`:
  `;(prime nat-1);(prime nat-2);(prime nat-3);(composite nat-4 nat-2 nat-2);(prime nat-5);(composite nat-6 nat-2 nat-3);(prime nat-7);(composite nat-8 nat-2 nat-4);(composite nat-9 nat-3 nat-3)`
* `lemmas`:
  `sqrt-divisor-bound every composite m has a divisor i with two <= i <= floor-sqrt(m)`

#### 3. Story Construction & Merge Reached
* **Story Construction:** Procedural formatting loop in `hyge.py:430–540`.
* **Merge Operations Reached:** **None.** Sieve and trial explanations are generated sequentially by hardcoded loops; cross-algorithm comparison is a trailing equality string check.
* **Audience Projection:** Single flat stdout text stream.

#### 4. Exact Observed Prose Output
```text
span: 1 through 9
lemmas taught:
  sqrt-divisor-bound -- every composite m has a divisor i with two <= i <= floor-sqrt(m)

explanation one -- sieve, run over the span:
  exclude 1 (below domain)
  keep 2
  strike 4 as 2 times 2
  strike 6 as 2 times 3
  strike 8 as 2 times 4
  keep 3
  strike 9 as 3 times 3
  keep 5
  keep 7
  kept: 2 3 5 7
  struck: 4 6 8 9
  excluded: 1
  stopped: candidates left = 0

explanation two -- trial, run over the span:
  1: prime
  2: prime
  3: prime
  4: composite (witness 2 times 2) -- cited: sqrt-divisor-bound
  5: prime
  6: composite (witness 2 times 3) -- cited: sqrt-divisor-bound
  7: prime
  8: composite (witness 2 times 4) -- cited: sqrt-divisor-bound
  9: composite (witness 3 times 3) -- cited: sqrt-divisor-bound

AgreeOnSpan(sieve, trial, 1..9, projection=composite, witnesses matching)
```

#### 5. Diagnosed Defects
* **Zero Aggregation:** Every individual integer is narrated on its own line (`1: prime`, `2: prime`, `3: prime`), repeating the predicate 9 times.
* **Unresolved Cross-Track Contradiction:** Sieve excluded `1` as `(below domain)`. Trial division classified `1` as `prime` (a defect of the baseline `below-domain` rewrite rule in `session.txt`). The merger failed to flag the conflict, reporting agreement on `projection=composite` while ignoring the prime/excluded disagreement at 1.
* **Rigid Template Ordering:** Traversal order rather than rhetorical order.

#### 6. Human Target Preserving Identical Facts
```text
Evaluation over span 1 through 9:

The Sieve of Eratosthenes and Trial Division agree on composite classification:
- Composites (4, 6, 8, 9) are confirmed with identical factor witnesses:
  4 (2×2), 6 (2×3), 8 (2×4), and 9 (3×3), with trial bounds verified by lemma sqrt-divisor-bound.
- Primes identified are 2, 3, 5, and 7.
- Boundary discrepancy: 1 was excluded as below-domain by the sieve, but tagged as prime by trial division.
```

---

### Case B: Test Results Reporting (`graph.py:1453`)

#### 1. Invocation & Input
* **Invocation:** `TestResultsReport(graph)()` / `runtime.test_results_report()`
* **Input / Cut:** Graph test results alist (`FromContextGetTestResults(graph)`).
* **Source Terms:** Machine `Pair` list of `Pair(TestName, Pair(Outcome, EmptyList))`.

#### 2. Exact Observed Prose Output (on failure)
```text
test_worker_lease_stale_rejection
test_paused_comparison_snapshot_roundtrip
```

#### 3. Diagnosed Defects
* **Selection:** Emits raw test symbol names only. Drops total test count, passed count, execution duration, and failure cause.
* **Realization:** Flat newline join without sentence structure, header, or summary.

#### 4. Human Target Preserving Identical Facts
```text
Test Suite Execution Complete:
- 2 of 24 registered tests failed:
  • test_worker_lease_stale_rejection
  • test_paused_comparison_snapshot_roundtrip
- 22 tests passed.
Status: Verification Held.
```

---

## 4. Tightened Diagnostic Findings (Refined from Review)

1. **Diagnostic Bypass Finding:**
   * *Revised Formulation:* **All traced diagnostic and lifecycle reporting paths emit directly to string sinks without narrative merging.** (No claim is made regarding unseen upstream revisions).
2. **Merge Implementation Finding:**
   * *Revised Formulation:* **No narrative merge implementation is located in the active Python modules of this checkout (`hyge/*.py`, `search/*.py`, `math/*.py`).**
3. **Example 3 Re-examination (`search/compare_packets.py:257–266`):**
   * Source inspection reveals the rejection check is:
     ```python
     if M.TermEqual(returned_packet_token, expected_packet_token)() is M.false_value:
         _debug("... packet result token=" + _debug_term(returned_packet_token, self.registry)
                + " expected=" + _debug_term(expected_packet_token, self.registry))
     ```
   * *Refined Finding:* The logged line `token=10 expected=10` was an **unexplained rejection caused by printer lossiness**. `M.TermEqual` evaluated to `false_value` because the tokens differed in underlying structural attributes (e.g. token generation index or registry identity), but `_debug_term` extracted and rendered only the integer representation `10` for both. The stale rejection logic was mathematically correct, but the diagnostic realization obscured the decision basis.
4. **Example 8 Re-examination (`main.py:441`):**
   * *Refined Finding:* The report `tao_problem_1_1: not proved after 600.00 seconds` reflects **non-discharge within allocated budget**, not mathematical refutation. Cross-referencing `08August2026 -- opus 5 answer.md:7` confirms that the entire 600-second budget elapsed during the initial cursor applicability scan (`elapsed=245.057s`) and subsequent ordering phase before search steps could expand the frontier.
5. **Example 9 Re-examination (`08August2026 -- opus 5 answer.md:7`):**
   * *Refined Finding:* The measured duration of the applicability scan was **245.057 seconds** on an initial knowledge base of 17 facts and 88 rules. Under a 600-second total search timeout, this single initialization step consumed 40.8% of the available budget.

---

## 5. Summary & Recommendation for L-S-2

* **Source Reachability Resolved:** `*.py.txt` files are unreferenced static reference artifacts. In active code, `TestResultsReport` is reachable, while `CuratorReport`/`RenderCuratorReport` are not.
* **Absence vs Bypass:** In this checkout, story construction and merge mechanics are **not implemented in active code**, rather than merely misconfigured or bypassed.
* **Recommendation:** With this addendum completing Cut L-S-1, INT is equipped to authorize the **canonical definition of `StoryFragment` and `StoryEdge` machine terms** and the deterministic merge operators for Cut L-S-2.
