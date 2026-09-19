# INV-0 — checked invariant-discovery experiment

**Date:** 2026-09-19. **Result:** G0–G7 pass in the isolated laboratory on the
session base. **34/34 validation tests pass.** This is not validation on the
requested remote base; see the explicit provenance deviation below.

## Provenance

| Item | Exact value |
|---|---|
| Agent | INV-0 |
| Branch | `arena/01a0bb91-cat-theo-machine` |
| Frozen BASE_SHA | `428ecdc146e38de3481222bed7bddeb3c08e1b2d` |
| Fetched requested reference | `origin/instrument-filter-applicability-timings` |
| Fetched SHA | `742c806505338525527219a4a94dde9b47df86e0` |
| Inspection-only commit | `01b8bcb` (committed before implementation) |
| Pushed implementation/test/artifact commit | `4001d45d778ac9dfbbe9f1859c7f11fd2be0f94b` |
| Interpreter | `/usr/bin/python3`, Python 3.11.2, GCC 12.2.0 |
| Dependency | system-Python `gmpy2==2.3.0` |
| Main command timeout | 180 seconds |
| Each fresh-process replay timeout | 30 seconds |

The Arena session is fixed to the branch above. The requested `work/INV-0/...`
branch was not created. The requested reference was fetched, **not merged or
used as the implementation base**; it diverged by 1/94 commits from the initial
checkout. This limits the result to the recorded BASE_SHA. The report-only
commit containing this document follows the pushed implementation commit;
`git log -1 --format=%H -- verification/inv0_experiment_report.md` identifies it.

## Inspection and reusable interfaces

The preimplementation gate is recorded in
[inspection_inv0.md](inspection_inv0.md). Reusable interfaces:

- `Rule`, `MultiRule`, accessors: `proof.py:155`, `proof.py:166`,
  `proof.py:325`, `proof.py:353`.
- `Match` and `Instantiate`: `machine.py:250`, `machine.py:315`.
- Structural lists/Zero: `core.py:95`, `core.py:98`, `core.py:203`.
- Existing naturals/counting: `math/peano.py:177`, `math/peano.py:206`,
  `math/peano.py:320`, `math/peano.py:342`.
- Existing evidence/reconstruction: `proof.py:396`, `proof.py:1814`,
  `proof.py:1878`, `proof.py:1995`, `proof.py:2333`, `proof.py:2365`.
- Existing smallest object snapshot path: `persistence.py:1079` and
  `persistence.py:1109`. Its shared-singleton field writes at
  `persistence.py:1125-1164` make it unsuitable for the stricter replay boundary.
- Existing BFS: `search/engine.py:1591`; existing candidate and pruning terms:
  `invariance.py:1559`, `invariance.py:1276`.

`Count` writes shared Zero.value (`math/peano.py:212`), and Step/Derivation
require registries (`proof.py:1814`, `proof.py:1995`). They were therefore not
called. The isolated equivalents retain raw structural naturals, checked
paths, and explicit work counters without registering new constructors.

**Absence/search evidence:** recursive search over `*.py` in this checkout for
`InvariantCertificate|CheckReachabilityObstruction|TransitionAttempt|CheckedTransition|RejectedTransition|OpenTransition|ExecutionFailure|PreservedOn|BrokenOn|Mod2`
returned no preimplementation definitions. Including `InvariantCandidate` in
that search did find the older term at `invariance.py:1559`, not the required
trace-scoped certificate. Inspection records the narrower replay/checker
search scope and patterns as well; these are not claims about all history.

## Implementation and trust boundaries

| Component | Implementation locus | What is checked |
|---|---|---|
| Structural records | `invariant_experiment.py:34-42`, `:114-152`, `:356` | Pair-only semantic fields; attempt includes ID, state, rule ID, scope, bindings, assumptions, obligations, budget |
| Rule schemas/identity | `invariant_experiment.py:296-353` | Exact ordered rule structures + domain + schema version; display labels excluded |
| Producer | `invariant_experiment.py:366` | Produces only a proposal, mismatch, open obligation, or execution failure |
| Independent transition checker | `invariant_experiment.py:386` | Recomputes scope and ID; rematches, compares bindings, reinstantiates, validates domain and after-state, reconstructs certificate |
| Restricted persistence | `invariant_experiment.py:234-292` | JSON tree codec; no object activation/pickle/import instructions; variable identity restored at codec boundary |
| Laboratory corpus | `invariant_experiment.py:453` | 5 deterministic lists, lengths 0–4; 15 attempts; successful transitions checked then replayed |
| Observer grammar/miner | `invariant_experiment.py:469-549` | Every supplied observer applied to checked traces; retained witnesses replayed before reuse; timeouts unresolved |
| General proof | `invariant_experiment.py:552-627` | Typed affine prefix lengths and symbolic-tail cancellation; unsupported shapes never pass |
| Scoped certificate | `invariant_experiment.py:637-679` | Content hash, exact scope, domain, assumptions, dependencies, all recomputed per-rule proofs; retained witness rechecked |
| Reachability obstruction | `invariant_experiment.py:682` | Certificate replay and unequal defined observations required; equal observations return Unknown |
| Explicitly assisted BFS | `invariant_experiment.py:695` | FIFO, checked root rewrites, expansion budget; invariant consulted only when supplied |
| Checked path replay | `invariant_experiment.py:735` | Step replay, adjacency, and exact start/goal |

`CheckedTransition` nests its `TransitionAttempt`: before-state, rule ID,
substitution, scope, assumptions, obligations and budget are not duplicated.
It adds the checked after-state and a transition certificate
(`invariant_experiment.py:425-429`). Candidate/certificate support IDs are
provenance, not proof premises (`invariant_experiment.py:586-627`, `:646-649`).

Tokens are opaque named atoms in the codec's `token/` namespace; observer
semantics do not inspect their names (`invariant_experiment.py:189-208`).
Repeated identical tokens still occupy separate list positions, tested at
`validation/test_inv0_invariant_discovery.py:281`. This is **root rewriting of
finite lists**, not arbitrary subterm or graph rewriting.

Host decisions are explicit: Python control flow, structural shape/type
checks, identity comparison, host scalar work/budget counters, and SHA-256/
JSON at the serialization boundary. Semantic lists, substitutions, queues,
proofs and values remain Pair terms. This is not a claim that the host
interpreter itself has been formalized. Producer and checker share the
existing Match/Instantiate primitives, but the checker does not call the
producer or trust its reported output (`invariant_experiment.py:386-436`).

## Exact theorem and justification

For every finite opaque-token list and every admissible **root** match:

```text
Step_R_even(s,s') => Mod2(Length(s)) = Mod2(Length(s'))
```

The structural checker derives a prefix numeral plus a symbolic tail length.
Each Pair contributes one position; token variables contribute no additional
list positions. Bound token/list sorts are checked and the same symbolic tail
must occur on both sides (`invariant_experiment.py:552-584`). Thus it derives:

| Schema (display only) | Before | After | Delta |
|---|---:|---:|---:|
| AddPair | n | n + 2 | +2 |
| RemovePair | n + 2 | n | −2 |
| SwapPair | n + 2 | n + 2 | 0 |

Signed deltas are structural pairs `(after_prefix, before_prefix)`, not trusted
producer integers (`invariant_experiment.py:609-610`). Structural parity of
both prefixes must agree (`invariant_experiment.py:606-612`). The proof has no
training-data parameter; agreement on samples alone is rejected as a
certificate (`validation/test_inv0_invariant_discovery.py:153`).

Reflexivity preserves the observer; each checked step preserves it; induction
on finite path length therefore preserves it under reflexive-transitive
closure. Unequal endpoint values obstruct reachability. Same-parity endpoints
supply **no** positive reachability conclusion
(`invariant_experiment.py:682-692`).

Under R_plus the old exact scope differs. A new structural check derives
AddOne's odd delta and retains an actually checked empty-to-singleton witness
(`invariant_experiment.py:613-623`). The original certificate remains valid
historical evidence for R_even
(`validation/test_inv0_invariant_discovery.py:194-210`).

## Deterministic utility, separate from correctness

Source data: `inv0_artifacts/2026-09-19/performance_comparison.json:1`.

| Task | Baseline status | Baseline expansions | Assisted status | Assisted expansions |
|---|---|---:|---|---:|
| 0 → 5 | BudgetExhausted | 64 | CheckedUnreachable | 0 |
| 2 → 7 | BudgetExhausted | 64 | CheckedUnreachable | 0 |
| 4 → 9 | BudgetExhausted | 64 | CheckedUnreachable | 0 |
| 0 → 4, R_even | — | — | CheckedReachable, 2-step path | 2 |
| 0 → 1, R_plus | — | — | ScopeMismatch then CheckedReachable, 1-step path | 2 |

The extension control expands 2 states because FIFO visits the earlier
AddPair child before popping the AddOne goal. The resulting path is still one
step. The baseline's budget expiry is never labeled unreachable
(`invariant_experiment.py:720-721`).

| Overhead/size metric | Count |
|---|---:|
| Training states / attempts / checked traces | 5 / 15 / 11 |
| Retained non-applicable attempts | 4 |
| Observer candidates | 2 (Length refuted; parity proposed) |
| Retained counterexamples, R_even / including extension | 1 / 2 |
| Initial observer evaluations | 44 |
| Re-mining evaluations / reused counterexamples | 24 / 1 |
| Schema proof/checker structural-node units | 73 |
| Full-corpus transition replay node units | 391 |
| Training success checks, including replay | 782 node units |
| Mining replay overhead | 22 replays, 782 node units |
| Certificate replay, schema + retained witness | 94 node units |
| Certificate serialized bytes, including newline | 5,730 |
| Serialized term artifacts, excluding performance JSON/logs | 75,709 bytes |

One expansion pops a non-goal state and tries every rule. Structural-node work
is the explicitly counted rule/input/output tree size (`invariant_experiment.py:439`),
not CPU instructions. Hashing, allocation, Match internals, and queue/seen
scanning are not included; they are real overhead and are not claimed free.
Certificate replay precedes pruning, so **zero expansions does not mean zero
work**. No wall-clock speedup claim is made.

## Commands and tests

Working directory `/home/user/cat_theo_machine` unless specified:

```sh
git rev-parse HEAD
git fetch origin instrument-filter-applicability-timings
git rev-parse FETCH_HEAD
git rev-list --left-right --count HEAD...FETCH_HEAD
/usr/bin/python3 --version
/usr/bin/python3 -m pip install --break-system-packages gmpy2==2.3.0

# 180-second tool timeout; child process timeout=30 seconds
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B \
  validation/test_inv0_invariant_discovery.py --artifacts \
  > /home/user/inv0_tests.log 2>&1
cp /home/user/inv0_tests.log \
  verification/inv0_artifacts/2026-09-19/test_results.log

git diff --check
git diff 428ecdc146e38de3481222bed7bddeb3c08e1b2d -- \
  core.py invariance.py runtime.py knowledge.py planner.py
git push origin arena/01a0bb91-cat-theo-machine
```

To replay saved evidence manually (cwd `/home/user`, 30-second timeout):

```sh
/usr/bin/python3 -B -m cat_theo_machine.invariant_experiment replay \
  cat_theo_machine/verification/inv0_artifacts/2026-09-19/checked_transition.json
/usr/bin/python3 -B -m cat_theo_machine.invariant_experiment certificate \
  cat_theo_machine/verification/inv0_artifacts/2026-09-19/parity_certificate.json
# Expected nonzero exit and ScopeMismatch:
/usr/bin/python3 -B -m cat_theo_machine.invariant_experiment certificate \
  cat_theo_machine/verification/inv0_artifacts/2026-09-19/parity_certificate.json --plus
```

**34 passed / 34 total** in the experiment suite; final recorded unittest
elapsed time 32.242 seconds, informational only
(`inv0_artifacts/2026-09-19/test_results.log:1-39`). The full legacy application
suite was not run; this result makes no claim about it. Validation includes
all 23 requested test names plus fresh certificate replay, semantic tampering
after rehash, malformed evidence, actual checker exceptions, saved witness
reuse, repeated opaque tokens, binding identity round trips, direct rule
structure mutation, and retained-counterexample reuse
(`validation/test_inv0_invariant_discovery.py:65-355`).

## Grading gates

| Gate | Grade | Evidence |
|---|---|---|
| G0 source discipline | PASS | Inspection-only commit `01b8bcb`; `inv0_artifacts/2026-09-19/source_discipline.log:1-22`; all original source files unchanged |
| G1 transition integrity | PASS | `validation/test_inv0_invariant_discovery.py:65-96`, `:341`; fresh processes reject all four tamper cases, including rehashed attempts |
| G2 candidate generation | PASS | `validation/test_inv0_invariant_discovery.py:98-137`, `:310-330`; timeout/crash unresolved, alpha-renaming stable, witnesses rechecked |
| G3 general proof | PASS | `validation/test_inv0_invariant_discovery.py:139-174`, `:291-297`; three structural proofs, unsupported shapes and forged certificates rejected |
| G4 checked consequence | PASS | `validation/test_inv0_invariant_discovery.py:176-192`; odd holdouts pruned with zero expansions, equal parity Unknown, reachable checked control |
| G5 scope discipline | PASS | `validation/test_inv0_invariant_discovery.py:194-218`, `:332-339`; R_plus mismatch/refutation, checked one-step odd path, historical certificate intact |
| G6 inertness | PASS | `validation/test_inv0_invariant_discovery.py:220-256`; explicit opt-in only, constructor-registry fingerprint and Zero.value unchanged |
| G7 measured utility | PASS | `validation/test_inv0_invariant_discovery.py:258-265`; deterministic counters and costs above, correctness independent of timing |

The source scan for `ActivateProposal|admit_next|activate_front|\.apply\(|\.eval\(|make_fresh_runtime|story|Experiment.?4`
was limited to the new implementation and validation modules and returned no
matches. A separate scan of the implementation for `AddPair|RemovePair|SwapPair|AddOne`
found only display construction at `invariant_experiment.py:320-324`, not
semantic dispatch. These searches are recorded in
`inv0_artifacts/2026-09-19/source_discipline.log:8-17`.

## Failures, classifications, and limits

- No unresolved mandatory gate in this implementation run. The base/branch
  deviation remains explicit; requested-base validation is outstanding.
- Initial inspection command ran outside the repository: command-location
  error, no repository mutation (`inspection_inv0.md:17-19`).
- Initial system dependency probe lacked gmpy2: environment failure, resolved
  by the system-Python installation recorded above.
- First development smoke run hit recursive encoding of a 10,000-cell unary
  budget. Fixed by compact numeral serialization (`invariant_experiment.py:244-245`,
  `:268-269`) and the local 512-unit default (`invariant_experiment.py:356`).
  It was not treated as a counterexample or invariant refutation.
- Deliberate mismatches, malformed/tampered evidence, timeouts, crashes, and
  unsupported rule shapes are distinct cases, not hidden successes:
  `validation/test_inv0_invariant_discovery.py:161`, `:267`, `:310`, `:349`.
- Supported schema language is intentionally small: typed prefixes, one
  cancellable symbolic tail, Length and Length mod Two. Repeated LHS
  variables, ill-sorted/unbound RHS variables, and nested lists are unsupported
  (`invariant_experiment.py:552-584`).
- In-memory inputs are assumed finite and acyclic. JSON encodes finite trees;
  this is not a hostile cyclic-object sandbox or a general resource-secure
  proof service. Hashes are content IDs, not signatures.
- The training corpus contains one alternating A/B list at each length 0–4,
  not every token assignment. Only the structural schema proof, not the
  corpus, establishes the universal result.

## Changed files and dated artifacts

Only new experiment files relative to BASE_SHA:

- `invariant_experiment.py`
- `validation/test_inv0_invariant_discovery.py`
- `verification/inspection_inv0.md`
- `verification/inv0_experiment_report.md`
- `verification/inv0_artifacts/2026-09-19/`:
  `training_transitions.json`, `checked_transition.json`,
  `rejected_length_candidate.json`, `parity_candidate.json`,
  `parity_certificate.json`, `observer_observations.json`,
  `r_even_rules.json`, `r_plus_rules.json`, `r_plus_counterexample.json`,
  `mining_reuse.json`, `mining_timeout.json`, `injected_outcomes.json`,
  `tampered_after_state.json`, `tampered_rule.json`,
  `tampered_substitution.json`, `tampered_rule_set.json`,
  `reachable_even_path.json`, `reachable_r_plus_path.json`,
  `transition_replay.log`, `tamper_rejections.log`,
  `r_even_reachability.log`, `r_plus_scope_invalidation.log`,
  `performance_comparison.json`, `test_results.log`, `source_discipline.log`.

`core.py`, all existing live knowledge/admission stores, and Programme C/L
story code are unchanged: the cumulative diff adds only the files listed
above. No activation or new accepted mathematical law is part of this result.

## Permitted conclusion

Given a supplied observer grammar containing Length and Length mod 2, the
Machine used checked transition traces to reject Length preservation,
proposed parity preservation, independently proved it for an exact rule-set
version, and used the scoped certificate to reject fresh unreachable goals.
It withheld the guarantee after a rule-set extension broke preservation.

This is a bounded checked abstraction/reuse cycle—not invention of parity,
proof from examples, self-modification, general graph rewriting, admission of
a live law, or general self-improvement.

```text
agent: INV-0
branch: arena/01a0bb91-cat-theo-machine
base SHA: 428ecdc146e38de3481222bed7bddeb3c08e1b2d
pushed commit: 4001d45d778ac9dfbbe9f1859c7f11fd2be0f94b (implementation/tests/artifacts)
inspection: committed first; interfaces and searched absences recorded above
implemented:
  transition terms; separate producer/checker; laboratory trace corpus
  observer miner; general preservation checker; scoped invariant certificate
  reachability obstruction; rule-set invalidation
exact theorem:
  Step_R_even(s,s') => Mod2(Length(s)) = Mod2(Length(s'))
tests:
  34 passed / 34 total
  PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B validation/test_inv0_invariant_discovery.py --artifacts
  system Python 3.11.2
  artifacts: verification/inv0_artifacts/2026-09-19/
grading:
  G0 source discipline: PASS
  G1 transition integrity: PASS
  G2 candidate generation: PASS
  G3 general proof: PASS
  G4 checked consequence: PASS
  G5 scope discipline: PASS
  G6 inertness: PASS
  G7 measured utility: PASS
failures:
  no remaining gate failures on session base
  requested reference fetched but not used as base; not validated there
unchanged:
  core.py; live knowledge/admission stores; Programme C and Programme L story code
ready for review: YES (on the documented session base)
next bounded item:
  independent review of the affine checker and requested-base compatibility,
  before expanding the fragment or considering any separate admission proposal
```
