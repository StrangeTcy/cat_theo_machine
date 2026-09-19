# INV-0 inspection gate — 2026-09-19

## Provenance and commands

- Frozen BASE_SHA (first successful repository command `git rev-parse HEAD`):
  `428ecdc146e38de3481222bed7bddeb3c08e1b2d`.
- Session branch: `arena/01a0bb91-cat-theo-machine`. The session requires this
  branch; the proposed `work/INV-0/...` branch will not be created.
- `git fetch origin instrument-filter-applicability-timings` succeeded;
  `git rev-parse FETCH_HEAD` returned
  `742c806505338525527219a4a94dde9b47df86e0`.
- **Base deviation:** implementation remains on the session checkout, not the
  fetched reference. `git rev-list --left-right --count HEAD...FETCH_HEAD`
  returned `1 94`. Importing that history would entail unrelated file changes.
- An initial command mistakenly used `/home/user`, returned “not a git
  repository”, and changed nothing. All subsequent repository commands use
  `/home/user/cat_theo_machine`.
- Interpreter: `/usr/bin/python3`, Python 3.11.2, not conda.
  Dependency import initially failed for gmpy2. Installed the declared version
  with `/usr/bin/python3 -m pip install --break-system-packages gmpy2==2.3.0`.
  `PYTHONPATH=/home/user /usr/bin/python3 -c 'from cat_theo_machine import
  machine as M; from cat_theo_machine import proof as P;
  print(P.Rule(M.EmptyList,M.EmptyList))'` succeeded (60-second command timeout).

## Reusable interfaces and exact loci (BASE_SHA)

1. **Terms/rules.** `core.py:95` defines EmptyList; `core.py:98` defines Pair,
   whose head/tail slots hold atoms. `proof.py:155` Rule(pattern,replacement)
   and `proof.py:166` MultiRule(premises,replacement) store structural inputs.
   `proof.py:325` RulePattern and `proof.py:353` RuleReplacement expose them.
   `machine.py:250` Match returns Pair(flag,bindings); failed matches return
   Pair(false_value,EmptyList) at `machine.py:292-294`.
   `machine.py:315` Instantiate returns Pair(term,EmptyList).
   Variables have Pair(VarTag,Pair(name,EmptyList)) structure
   (`machine.py:255-267`). These express all four requested schemas directly.
2. **Execution evidence.** `proof.py:396` RewriteAction(rule,path),
   `proof.py:1814` Step(current,action,next,registry), `proof.py:1995`
   Derivation(steps,cost,registry), and `proof.py:1878` ProofCost exist.
   `proof.py:2333` RewriteAtPath and `proof.py:2368` BuildDerivation reconstruct
   applications. BuildDerivation is a producer, not an integrity verifier:
   its action replay at `proof.py:2505-2537` does not verify a supplied
   next-state or scope identity. New checker will rematch and reinstantiate;
   unsuccessful identity rewrites will not be confused with successful matches.
   Existing Step/Derivation require constructor registries; isolated records
   will carry checked transitions and paths without global registration.
3. **Lists/naturals.** `core.py:197` Zero; `math/peano.py:177` Succ,
   `math/peano.py:206` Count, `math/peano.py:320` NatEq,
   `math/peano.py:342` NatLess. Count counts positions (not unique tokens),
   but writes shared Zero.value (`math/peano.py:212`) and builds registry
   entries. Use Zero and structural SuccLabel terms locally rather than
   invoking Count, to avoid shared-state mutation. Count is not a new idea.
4. **Failures/budgets.** Match's false flag above is a checked mismatch.
   `labels.py:1138-1142` PendingLabel/FailedLabel and
   `labels.py:554` SearchFailureLabel exist; these are not exact equivalents
   of the requested four transition outcomes. `search/engine.py:287-304`
   checks elapsed host time; `search/compare_subprocess.py:481-516` records
   comparison timeout. Neither timeout nor failure to find is a refutation.
5. **Persistence.** Smallest existing object path:
   `persistence.py:1079` SnapshotCodec.capture_objects(roots),
   `persistence.py:1109` load_snapshot, `persistence.py:1208` load.
   Loader reuses singleton objects (`persistence.py:1125-1135`) and assigns
   their fields (`persistence.py:1148-1164`). Activation at
   `persistence.py:1215` is explicitly excluded. A restricted structural JSON
   codec is justified for canonical hashing and replay without singleton
   writes, dynamic imports, pickle, graph activation, or registry mutation.
6. **Search.** `search/engine.py:1591` SearchBFS(graph,start,goal,rules,
   heuristic,registry) is the existing BFS; it depends on graph/runtime
   machinery. Cheapest isolated equivalent is a FIFO of structural Pair
   states/paths, explicit 64-expansion budget, and checked root rewrites.
   The declared world is ROOT list rewriting, not arbitrary subterm rewriting.
7. **Existing invariants.** `invariance.py:1559` InvariantCandidate(phi,ruleset)
   exists, but lacks trace provenance/scope. `invariance.py:98` Preserves and
   `invariance.py:1198` Invariant are a different observer language;
   `invariance.py:1276` ReachabilityPrune trusts an invariant-shaped term and
   compares PhiReading. They are not the independent parity proof/scoped
   certificate consumer required here and will remain untouched.
8. **Test convention.** `validation/test1_planner_minimal.py:1-18` is an
   executable system-Python validation script. Its `hyge` package import
   assumes a different directory layout. New validation will use standard
   library unittest with the actual checkout package, runnable as a script.

## Search evidence for absent interfaces

Ran recursive ripgrep over **all tracked/worktree `*.py` files**:
`rg -n 'InvariantCandidate|InvariantCertificate|CheckReachabilityObstruction|TransitionAttempt|CheckedTransition|RejectedTransition|OpenTransition|ExecutionFailure|PreservedOn|BrokenOn|Mod2' --glob '*.py' .`.
Only existing InvariantCandidate/label hits occurred, cited above; the other
requested names are absent within that search scope. No claim is made about
unsearched historical commits or text archives.

Searched `proof.py`, `search/*.py`, `matching.py`, `persistence.py` for
`Replay|CheckDerivation|Verify|RewriteAction|SearchBFS` and
`def .*replay|def .*check|def .*serial|def .*deserial`. Found reconstruction
paths cited above, no exact scoped transition-integrity checker in that scope.

## Host semantics and trust boundary

- Existing Match uses Python branching and identity/structural comparisons
  (`machine.py:282-312`). Instantiate's constructed-node branch writes the
  global registry (`machine.py:333-345`); restrict this experiment to raw
  Pair/opaque atom templates so that branch is unreachable.
- Existing naturals use GMP host arithmetic (`math/peano.py:177-225`). New
  observable values and affine counts will be structural naturals. Host
  scalar control flow/work counters are explicit; SHA-256/JSON are boundary
  operations, not proof oracles. No `.apply`/`.eval` channel will be added.
- Records, substitutions, queues, observer grammar, proofs, and evidence
  lists use machine Pair terms, never Python containers in value slots.
  Host containers may be used only for serialization/reporting/tests.
- Canonical rule-set identity includes schema version, root-rewrite domain,
  and exact ordered rule structures; display labels are excluded. Variable
  spelling may affect identity, but not the structural proof/classification.
- Independent means checker reconstructs evidence without trusting producer
  outputs; it may share existing Match/Instantiate primitives. This is not
  an independently implemented theorem-prover kernel.

## Plan and gate decision

Add only `invariant_experiment.py`,
`validation/test_inv0_invariant_discovery.py`, this inspection,
`verification/inv0_experiment_report.md`, and dated experiment artifacts.
No existing-file edit is required. No core, Programme C/L, story input,
activation, admission, or live store change is needed. Replay can remain
purely local. The term world is representable and transition production is
separable from checking. **PASS: implementation may proceed after this
inspection record is committed.**
