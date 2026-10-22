# CL0 verification table

| Claim or assumption | Probe | Result | Effect |
|---|---|---|---|
| Current branch has the five-track protocol ledgers | `git ls-tree HEAD protocol` | Only `protocol/ODR-FINAL.md` | Remote ledgers remain CL0 inputs |
| Remote protocol maps S/E/F/G/I | `origin/arena/01a05cb0:protocol/README.md` | Verified | Track mapping accepted |
| Remote two-pipeline model exists | `origin/arena/01a05cb0:protocol/TWO-PIPELINE.md` | Verified | Two-pipeline model accepted |
| Charter fixes five G methods | `origin/arena/01a05cb0:protocol/CHARTER-v2.md` | Verified | G vocabulary is Invariance/Extremal/Pigeonhole/Divide/Symmetry |
| Current planner matches v2 method set | `verification/odr-cl0/test_method_registry.py` plus `planner.py` registry | Policy now explicit: Bijection/DoubleCount are legacy-blocked; Invariance payload remains absent | G-eng must implement/test Invariance before G/I curriculum |
| Current invariant substrate exists | import and symbol probe | Verified | G4 is the preliminary route |
| Current S2 relation-contract surface exists | symbol probe | Refuted | S2 blocked on current cut |
| Default environment can run baseline | `python -m cat_theo_machine.testsuite` | Refuted: missing gmpy2 | Environment bootstrap required |
| Core tests pass in dependency-complete probe environment | `python -m cat_theo_machine.testsuite` | Verified, exit 0 | Focused core baseline is available |
| Live SearchDFS baseline is green | `python -m cat_theo_machine.test_actual_searchdfs` | Refuted: after stale-ID triage it runs but exposes an invalid shared-start fixture; expected failure is quarantined with root cause | Repair fixture semantics or replace with fifteen explicit per-example runs before GO |
| Researcher-v0 is only a prose idea | remote tree and executable G1–G6 runners | Refuted: implementation and tests exist | Reuse/adapter work, not greenfield rewrite |
| Researcher-v0 G1–G6 tests pass | `run_g1_tests` through `run_g6_tests` on remote archive | Verified: 23/16/17/16/17/17 | Prototype is a viable G4 reference |
| Selected-rule matcher diagnostics explain SearchDFS root | direct `JoinPremises` probe against `tao_problem_1_1_triangle` start | Verified: only side-alpha rule has bindings | Fixture uses the wrong shared start; no invariant-pruning diagnosis |
| Independent per-example SearchDFS probe passes all runnable cases | `searchdfs_independent.py` | Verified: 12 runnable successes, 3 angle blocks, no failures or timeouts | Goal-directed matcher now uses the explicitly manifested `distinct_is_symmetric` route; angle fixtures remain explicitly blocked |
| G legacy-method policy is enforced | `verification/odr-cl0/test_method_registry.py` | Verified: registry pass | Bijection/DoubleCount remain constructible but blocked |
| Current cut already contains researcher-v0 | `git ls-tree HEAD researcher_v0` | Refuted | Prototype must be imported or adapted |

## CL0 decision

`RE-SCOPE: FOUNDATION_ONLY`

The invariant route is the preliminary route, but autonomous candidate work is not admitted until the operator environment is reproducible and the SearchDFS geometry-pack baseline is repaired or explicitly re-pinned.
