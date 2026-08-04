# HYGE Project Assessment

## Executive summary

HYGE is an experimental symbolic theorem-proving and term-rewriting system implemented as a Python hypergraph machine. Its central idea is unusually consistent: almost every logical value, list, rule, derivation, index, search state, and cost is represented inside the same `Atom`/`Edge`/`Pair` object model. Knowledge is loaded from declarative YAML packs, proof search supports DFS/BFS/beam/A* variants, searches can be paused and resumed through JSON snapshots, and a local inspector exposes graph/search state.

The repository contains substantial engineering beyond a toy prover: Patricia-tree indexes, theorem and rewrite actions, derivation caching and schemata, search memoization, multiprocessing search comparisons, snapshot migration, an inspector, and a large in-kernel test suite. However, it is not yet packaged or hardened as a dependable library/application. The most important immediate issues are a likely snapshot serialization defect for ordinary `Char` objects, pack loading that does not advance the rule-count/depth budget, unenforced pack dependencies, missing dependency metadata/documentation, and extensive dependence on synchronized module globals.

## What the project is

### Core computational model

- `core.py` defines the primitive universe: mutable `Atom`, relational `Edge`, cons-cell-like `Pair`, identity singletons, and identity comparison.
- `labels.py` supplies singleton constructor/tag atoms used throughout the machine.
- `constructors.py` maintains a constructor registry and implements structural comparison/canonical construction.
- `machine.py` acts as a façade that re-exports the kernel, arithmetic, graph, proof, and search vocabulary.

A key design choice is that machine operations are represented as `Edge` subclasses and evaluated through `__call__`. This gives the code a uniform graph-machine semantics, but also creates a large number of short-lived Python objects.

### Stateful hypergraph runtime

- `context.py` stores machine state in a tagged tree-backed context.
- `graph.py` wraps that context as `Hypergraph`, exposing mutation methods for nodes, edges, rules, derivations, search attempts, jobs, and memo tables.
- `runtime.py` creates fresh runtimes, loads packs or snapshots, provides proof/test APIs, and produces inspector data.

The runtime actively synchronizes restored symbols and registries into module globals (`runtime.py:1563-1580`). This is central to snapshot identity and singleton semantics.

### Knowledge and proof layer

- `packs.py` parses safe YAML into machine terms, rules, multi-premise rules, derivation schemata, and examples.
- `knowledge.py` implements exact fact tries, head indexes, rule indexes, and matching memo structures.
- `proof.py` defines rules, theorem/rewrite actions, derivations, cost models, cached/schema proof replay, and the high-level proving flow.
- `matching.py` implements recursive rewriting and structural term equality.
- `schemata.py` stores and retrieves reusable derivation plans.

Eight bundled packs cover order/sign reasoning, square roots, distributivity, real closure, arithmetic, geometry ontology, trigonometry, and a geometry problem.

### Search subsystem

The `search/` package is a large subsystem split into:

- `model.py`: serialized machine representations for jobs, states, worker packets, metrics, and results.
- `patricia.py`: search-specific Patricia indexes and tree deltas.
- `engine.py`: resumable burst/step search and mode-specific frontier behavior.
- `runtime.py`: spawn-safe worker runtimes and resident worker executors.
- `compare.py`: parallel comparison of search modes.
- `serialization.py`: custom pickling for machine singletons and labels.
- `ui.py`: progress, pause/stop, and console input control.
- `api.py`: dispatch from heuristic mode to DFS/BFS/beam/A* or rewrite DFS.

Although the classes `SearchDFS` and `SearchRewriteDFS` are empty subclasses and `SearchAStar` has no methods of its own, this is intentional dispatch-by-mode: the shared step kernel reads the heuristic mode and applies different frontier policies (`search/engine.py:1549-1570`).

### Persistence and user entry points

- `persistence.py` captures graph roots and known singletons into a JSON object graph, restores it, migrates legacy tree roots, and uses spawned workers for large restores.
- `main.py` exposes `cold`, `warm`, `test`, and `inspect` modes.
- `inspector/` contains a static browser UI; the server binds only to `127.0.0.1`.
- `testsuite.py` is a large custom test collection installed into the hypergraph and run by the machine itself.
- `knowledge_selftest.py` is a smaller standalone smoke test.

## Main execution flow

1. `main.py` selects cold boot, warm boot, test, or inspector mode.
2. Cold boot creates a fresh `MachineRuntime`, loads the ordered pack list, runs theorem cases, and saves a snapshot.
3. Warm boot restores a snapshot and resumes proof work from restored machine state.
4. `MachineRuntime.prove()` invokes `proof.Prove` with graph state, ordered rules, and a heuristic.
5. The proof layer tries direct/cache/schema paths and ultimately dispatches to `M.Search`.
6. `search.api.Search` selects a search mode; `search.engine.Search` executes resumable bursts over machine-encoded jobs/states.
7. Completed plans are turned into derivations and cost records; paused jobs remain in graph context and are captured in snapshots.

## Validation status

- Targeted `py_compile` checks passed for 43 core, search, test, and probe Python files.
- The intended test entry point is `python main.py test` (or package-equivalent invocation); the lightweight smoke test is `knowledge_selftest.py`.
- Full test/runtime execution was **not verified** in this review because shell execution permission was denied after syntax checks.
- The repository currently contains no usable current snapshot: `snapshots/` has one v4 backup and three `.bad` files. Consequently, default inspector mode will fall back to packs, while explicit warm mode is likely to fail unless a valid snapshot is generated.
- `cold_debug_verify.log` is empty and provides no runtime evidence.

## Prioritized findings

### 1. High: ordinary `Char` objects appear to lose their symbol in JSON snapshots

**Evidence:**

- `Char` stores its semantic content in `symbol`, while inherited `value` remains `None` (`core.py:218-224`).
- `SnapshotCodec._record_for()` has special records only for pair and edge shapes; all other atoms are emitted with only a `value` field (`persistence.py:945-965`).
- The loader has explicit support for records containing `"symbol"` (`persistence.py:1053-1083`), but the writer never emits that key.
- Packs create many non-singleton `Char` atoms for variable names and explicit character terms (`packs.py:118-126`).

**Impact:** a saved rule variable like `Char("a")` can be restored as a plain `Atom` with no symbol. That can corrupt variable matching, pretty-printing, structural keys, and resumed searches. Existing snapshot tests cover generic `Edge` structure and jobs, but no explicit non-singleton `Char` round trip was found.

**Recommendation:** add a `Char` branch in `_record_for()` that writes `symbol` and `value`, then add direct tests for arbitrary `Char`, pack variable terms, a saved/restored loaded rule, and a resumed search using that rule.

### 2. High: pack-loaded rules do not increment `next_rule_index`

**Evidence:**

- `Hypergraph.add_rule()` increments the context rule index (`graph.py:130-140`).
- `PackLoader.load_pack_dict()` copies `graph.next_rule_index`, inserts every pack rule, then writes the unchanged value back (`packs.py:257-284`, `packs.py:324-330`).
- Fresh search depth is derived from `graph.next_rule_index`; if it is zero, the engine falls back to counting the rules (`search/engine.py:371-381`).

**Impact:** today this is masked by the fallback when the index remains zero. Once any rule is added through `add_rule()`, subsequent bulk-loaded pack rules will not be reflected, so the default search depth can become much smaller than the actual rule set. It also makes the field’s name and semantics unreliable.

**Recommendation:** increment the index for every loaded rule using the same operation as `Hypergraph.add_rule()`, or remove the cached counter and derive a clearly named search budget independently.

### 3. Medium-high: pack dependencies are metadata only

**Evidence:** `requires` is parsed and stored (`packs.py:215-221`) and displayed in summaries, but no code validates that required packs are already loaded. For example, `geometry` declares three dependencies and `trigonometry` declares `geometry-ontology`.

**Impact:** custom load orders can silently create incomplete or semantically invalid runtimes rather than fail clearly. The hard-coded order in `main.py` currently compensates for this.

**Recommendation:** validate requirements in `PackLoader`, reject missing dependencies, and optionally topologically sort a requested pack set with cycle detection.

### 4. Medium-high: the project is not reproducibly installable

**Evidence:** no `pyproject.toml`, `requirements*.txt`, setup configuration, README, license, or `.gitignore` was found. Runtime imports require at least `gmpy2` and YAML support (`gmprep.py`, `persistence.py`, `packs.py`).

**Impact:** a new environment cannot discover supported Python versions, install dependencies, run a documented command, or understand project status. This also contradicts any impression that the code is standard-library-only.

**Recommendation:** add `pyproject.toml`, lock or constrain dependencies, declare a console script, add a short architecture/run/test README, and document snapshot compatibility.

### 5. Medium: global namespace synchronization prevents runtime isolation

**Evidence:** `_sync_live_namespace()` updates `machine.__dict__` and synchronizes many modules (`runtime.py:1563-1580`); graph refresh and worker runtime construction also reset global constructor/index state (`graph.py:74-97`, `search/runtime.py:55-83`).

**Impact:** two runtimes in one process are not isolated. Interleaved use, threads, tests that retain old terms, or inspector/search concurrency can observe the wrong constructor registry or singleton set. This raises correctness risk and makes the system hard to embed.

**Recommendation:** introduce an explicit kernel/runtime environment object and pass it through operations. As a transitional guard, document single-active-runtime semantics and add assertions or a process-wide lock around activation.

### 6. Medium: recursion remains in core traversals

**Evidence:** recursive equality, rewriting, registry scans, schema lookup, and list operations remain in files such as `matching.py:19-35`, `matching.py:46-72`, `constructors.py:290-335`, and `graph.py:251-260`. Some newer snapshot/search paths are iterative, and the tests explicitly probe recursion limits in selected areas.

**Impact:** large terms, long lists, collision buckets, or legacy trees can still raise `RecursionError`. Recursive rewrite also reconstructs the entire pair tree and can become expensive.

**Recommendation:** convert foundational traversals (`TermEqual`, `Rewrite`, registry search, reverse/append, schema lookup) to explicit machine/Python work stacks and add deep-term regression tests.

### 7. Medium: high Python-level allocation and quadratic tuple growth

**Evidence:** identity uses a fresh UUID per atom (`core.py:51-67`); many builders repeatedly concatenate immutable tuples (for example `packs.py`, `runtime.py`, and persistence collection paths); most machine operations allocate additional `Edge`, input, and result structures.

**Impact:** proof search is allocation-heavy, and some ostensibly linear builders become quadratic. This likely contributes to the elaborate caching, worker, and progress infrastructure and will limit larger knowledge bases.

**Recommendation:** profile cold boot and representative searches, then replace tuple accumulation with lists/final conversion in host-side orchestration code. Keep immutable machine lists where they are semantically important, but avoid wrapping every internal predicate in a recorded `Edge` unless provenance is needed.

### 8. Medium-low: API and compatibility residue increases cognitive load

Examples include two `IsPair` implementations, a stale `IsPairCell` name in `core.__all__` (`core.py:293-337`), an entirely commented `_lazywrap.py`, large commented legacy blocks, wildcard imports throughout `search/`, and a minimal package `__init__.py` that describes the package as reconstructed. These do not necessarily break runtime behavior, but they make ownership and intended public API unclear.

**Recommendation:** define a narrow supported API, remove dead compatibility code after snapshot migration boundaries are set, replace wildcard imports with explicit dependencies, and split very large modules (`proof.py`, `testsuite.py`, `search/compare.py`) by responsibility.

### 9. Medium-low: destructive snapshot quarantine is automatic

`main.py` deletes an existing `.bad` snapshot before moving the current unreadable snapshot into its place (`main.py:195-210`). This can erase the previous failure artifact and complicate debugging.

**Recommendation:** retain timestamped/versioned quarantine files and include the parse/compatibility error in a small sidecar log.

### 10. Low/security note: local persistence pickle is acceptable only under a trust boundary

Worker result files are created inside program-controlled temporary directories and then loaded with `pickle`, while the public snapshot format is JSON. That is a reasonable local IPC design, but these temporary pickle files must never be treated as externally supplied input. The inspector is correctly bound to loopback (`main.py:717-726`).

## Strengths worth preserving

- A coherent “everything is a machine term” model rather than unrelated data representations.
- Declarative, safe YAML knowledge ingestion via `yaml.safe_load`.
- Persistent search jobs and resumable cursor state.
- Search-specific Patricia structures and memo/delta handling.
- Atomic JSON snapshot writes.
- Spawn-aware multiprocessing design for Windows.
- An unusually broad in-kernel test suite, including search packetization, worker serialization, paused-job round trips, and recursion probes.
- Loopback-only inspector serving and a clear separation between source packs and runtime snapshots.

## Recommended sequence

1. Fix and test arbitrary `Char` snapshot serialization.
2. Run the complete test mode and standalone self-test; establish a clean valid snapshot from a cold boot.
3. Correct `next_rule_index` during pack loading and add mixed `add_rule`/pack-load tests.
4. Enforce `requires` and test dependency ordering/failure cases.
5. Add packaging, dependency metadata, and minimal operational documentation.
6. Define and document the single-runtime constraint, then plan migration away from global synchronization.
7. Profile and iteratively remove recursion/quadratic host-side accumulation from hot paths.
8. Refactor the search/proof modules only after the behavioral suite is running reliably in CI.

## Overall assessment

HYGE is a serious research prototype with a distinctive internal model and significant functionality. Its strongest aspect is conceptual integrity across terms, rules, proofs, search, and persistence. Its weakest aspect is operational reliability: the environment is undocumented, current snapshots are bad, execution was not verified here, and persistence/global-state invariants are fragile. The best next move is not a broad rewrite; it is to make persistence and test execution trustworthy first, then improve isolation and performance behind the existing test corpus.
