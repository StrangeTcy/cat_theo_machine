# CL0 verification table

| Claim or assumption | Probe | Result | Effect |
|---|---|---|---|
| Current branch has the five-track protocol ledgers | `git ls-tree HEAD protocol` | Only `protocol/ODR-FINAL.md` | Remote ledgers remain CL0 inputs |
| Remote protocol maps S/E/F/G/I | `origin/arena/01a05cb0:protocol/README.md` | Verified | Track mapping accepted |
| Remote two-pipeline model exists | `origin/arena/01a05cb0:protocol/TWO-PIPELINE.md` | Verified | Two-pipeline model accepted |
| Charter fixes five G methods | `origin/arena/01a05cb0:protocol/CHARTER-v2.md` | Verified | G vocabulary is Invariance/Extremal/Pigeonhole/Divide/Symmetry |
| Current planner matches v2 method set | `grep planner.py` | Refuted: Bijection and DoubleCount present; Invariance class absent | G drift must be resolved |
| Current invariant substrate exists | import and symbol probe | Verified | G4 is the preliminary route |
| Current S2 relation-contract surface exists | symbol probe | Refuted | S2 blocked on current cut |
| Default environment can run baseline | `python -m cat_theo_machine.testsuite` | Refuted: missing gmpy2 | Environment bootstrap required |
| Core tests pass in dependency-complete probe environment | `python -m cat_theo_machine.testsuite` | Verified, exit 0 | Focused core baseline is available |
| Live SearchDFS baseline is green | `python -m cat_theo_machine.test_actual_searchdfs` | Refuted: after stale-ID triage it runs but fails with expanded=1 and 15 missing obligations | Repair/re-pin fixture/search contract before GO |
| Researcher-v0 is only a prose idea | remote tree and executable G1–G6 runners | Refuted: implementation and tests exist | Reuse/adapter work, not greenfield rewrite |
| Researcher-v0 G1–G6 tests pass | `run_g1_tests` through `run_g6_tests` on remote archive | Verified: 23/16/17/16/17/17 | Prototype is a viable G4 reference |
| Current cut already contains researcher-v0 | `git ls-tree HEAD researcher_v0` | Refuted | Prototype must be imported or adapted |

## CL0 decision

`RE-SCOPE: FOUNDATION_ONLY`

The invariant route is the preliminary route, but autonomous candidate work is not admitted until the operator environment is reproducible and the SearchDFS geometry-pack baseline is repaired or explicitly re-pinned.
