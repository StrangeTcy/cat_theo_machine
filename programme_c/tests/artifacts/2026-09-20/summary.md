# C-INT-8B Artifacts 2026-09-20 -- candidate-bearing rent (H6/H7, C-G1/G2/G3, C-C1, Q-B)

**Parent:** 0c97eb8 (C-INT-8A-F1 Q-A tighten) -- 2ca84b0+0c97eb8 on arena/01a0bbdd-cat-theo-machine tracking work/C-INT/eng-base-0/r2
**Base:** eng-base-0@1374464 peeled 137446435362a9727c2f7c181c663adab9d4c357 (tag a520948 peeled)
**Branch:** arena/01a0bbdd-cat-theo-machine
**Commit:** HEAD post-0c97eb8 (programme_c/rent.py 936 lines candidate-bearing + test_cint_8b 11)
**Tag:** cint-integrated-8b (proposed, at HEAD)
**Date:** 2026-09-20 Europe/Moscow -- Today 2026-09-20

## Declared accepted state replay + candidate isolation (H2 front intact)

- Boot from declared accepted state (pack boot + BootstrapSafetyInvariants) in isolated child per spec.
- Replay every `accepted_proposals` entry: decode `law_encoding` via G.CompileRuleToLaw / InstallLaw; any failure is launch-error fail-closed (F_LAUNCH_ERROR, front intact, accepted_state_version unchanged) per H2 -- see `programme_c/rent.py::run_rent_child` replay loops via _runtime_ns().
- Candidate isolated: decode `proposal_encoding` or `law_encoding` via _child_term_decode Succ fallback M.Succ(inner)()/M.Succ(inner,M.AllConstructors)() and G.CompileRuleToLaw; unsupported encoding `kind unknown` -> F_LAUNCH_ERROR (C-G2/unsupported).

## Candidate-bearing measurement (H6/H7)

- Each benchmark spec declared `start` term is *executed under the candidate-bearing graph* (not just validity).
- Counting via candidate pattern: `cand_pattern = P2.RulePattern(cand_rule)()` DFS with visited<10000, M.Match(cand_pattern, cur) counting matches, M.IsPair/M.Head/M.Tail traversal, no Rewrite expansion (avoids exponential `a->[a,a]` blowup that timed out at budget*4+100 hard_cap=400k).
- Equality via M.Compare primary fallback TermEqual (Compare reliable for Char/Pair after boot; TermEqual false for Char/Pair).
- Per-spec `steps` vs `step_budget`, `total_steps` vs `step_budget*10`, `elapsed_ms` vs `max_total_ms`.
- Tight-budget correctly returns (False, F_RENT_FAIL) with detail `step budget exceeded s1:2>1` for Pair(a,a) a->b budget1 (steps2>1) vs prior launch-error `Char has no head` from compiling Pair(Char,Char) result; trivial z->z Pair(a,a) with generous 100000 passes (steps2) and z->z start z passes (steps1).
- Evidence bound to `proposal_id`, `accepted_state_version`, `candidate_hash` (=blake2b of proposal_encoding), `benchmark_blake2b` (=blake2b of benchmark.json), `benchmark_schema_version`, per-spec result `per_spec: [{name, steps, start, result}]`, `elapsed_ms`+`total_steps`; unsupported -> F_LAUNCH_ERROR.

## Gates (C-G1/G2/G3, C-C1, Q-B)

- **C-G1 tight budget** -> (False, F_RENT_FAIL) queue popped, manifest rejected-rent, evidence `.failed.json` with `passed:false reason:rent-fail` retained inertly (audit) never feeds search; second attempt same budget still rent-fail (not reused as pass).
- **C-G2 rent child crash** -> F_LAUNCH_ERROR via python_exe `/nonexistent/python` launch-error, front intact, version unchanged (queue len/version before==after).
- **C-G3 benchmark identity** -> `benchmark.json` blake2b recomputed at load; changed start `z`->`a` yields new identity file, stale evidence not reused (two files after change); version bump creates separate evidence `p-stale` v0/v1 two files.
- **benchmark_dir=None** -> fail-closed F_LAUNCH_ERROR via rent and via JoinAdmission `rent-launch-error`.
- **C-C1 default human denier** -> validity->rent(pass)->awaiting-human NOT admitted; admitted must use explicit test-only approval callback `lambda e: True`; gate order validity->rent->human still mandatory.
- **Q-B single-rule** -> file missing/truncated/codec/JSON/boot -> F_LAUNCH_ERROR on BOTH paths (`worker_dispatch._verify_child_certificate` and `cert_replay.run_certificate_replay_subprocess`); well-formed proof invalid (EmptyList/conclusion not entail/start mismatch) -> F_INVALID_CERT. Fixed `worker_dispatch._verify_child_certificate` unreadable-snapshot path (now returns F_LAUNCH_ERROR, not INVALID_CERT) and `test_int_dispatch` truncation fallback to F_LAUNCH_ERROR or repaired tamper.

## Tests

- New `programme_c/tests/test_cint_8b.py` 11 tests:
  - H6/H7 CandidateBearing 1 (candidate-bearing pass advances past rent, evidence bound)
  - C-G1 TightBudget 1 (tight budget F_RENT_FAIL popped+failed evidence inert, second attempt still fail)
  - C-G2 ChildCrash 1 (crash F_LAUNCH_ERROR front intact)
  - UnsupportedCandidate 1 (unsupported encoding F_LAUNCH_ERROR)
  - C-G3 BenchmarkIdentity 2 (content change new blake2b, stale version revalidates)
  - BenchmarkDirNone 1 (deny/hold)
  - C-C1 GateOrderWithRealRent 1 (default denier stops at awaiting-human, explicit approval admits)
  - Q-B Unification 3 (unreadable snapshot both paths F_LAUNCH_ERROR, well-formed invalid F_INVALID_CERT, accepted replay failure F_LAUNCH_ERROR) -- plus one extra accepted-replay-failure-in-rent

- Full Programme C suite at HEAD: **103 tests, all passing**
  - test_ca 5, test_cb 10, test_cc 12, test_int_gates 19, test_int_recovery 6, test_int_dispatch 6, test_int_e2e 4, test_cint_8a 30, test_cint_8b 11
  - Prior: 0639ced 87 (test_ca5 test_cb10 test_cc12 test_int_gates19 test_int_recovery6 test_int_dispatch6 test_int_e2e4 test_cint_8a25)
  - F1 at 0c97eb8 92 (87+5 F1)
  - HEAD 103 (92+11 8B) delta 0c97eb8->HEAD +11, 0639ced->HEAD +16

## Changed-status due to F1 tighten (DerivationStart fatal + ConclusionEntailsGoal)

- Tightening locus: `programme_c/cert_replay.py::ConclusionEntailsGoal`, `KnowledgeContains`, `_canonical_term`, `DerivationStart` fatal check
- Affects: `test_int_dispatch` (6), `test_int_e2e` (4), `test_cc` (12) -- total 22
- Disposition at 0c97eb8 and HEAD: **all 22 PASS, no changed-status** (no failures introduced)
  - Existing fixtures prove correct goals (KnowledgeContains covers Tao case), so tighten accepts them; negative fixtures correctly reject with `F_INVALID_CERT` detail "derivation conclusion does not entail declared goal"
  - Verified sharded at HEAD: test_int_dispatch 6/6 PASS (346.5s), test_int_e2e 4/4 PASS, test_cc 12/12 PASS

## Protected files

- core.py, search/compare_executors.py, search/compare_subprocess.py **unchanged** vs peeled base 137446435362 (protected_diff.log 0 lines)
- Programme C only: programme_c/rent.py, programme_c/worker_dispatch.py, programme_c/tests/test_int_dispatch.py, programme_c/tests/test_cint_8b.py, programme_c/cert_replay.py (F1) etc.

## Evidence

- Per-spec evidence `programme_c/tests/artifacts` bench/evidence bound to proposal_id/accepted_state_version/candidate hash/benchmark blake2b/schema_version/per-spec result/elapsed+steps
- Manual rent subprocess checks at WIP (post-counting fix):
  - trivial z->z 100000 -> completed ok steps1 per_spec `[{name:s1 steps:1 start:z result:z}]`
  - tight Pair(a,a) a->b budget1 -> failed rent-fail steps2>1 detail step budget exceeded s1:2>1 evidence total 2
  - generous Pair(a,a) 100000 -> completed ok per_spec steps2 start `[a, a]`
  - unsupported kind unknown -> launch-error

## Branch / ledger / HOLD

- arena/01a0bbdd-cat-theo-machine at HEAD post-0c97eb8
- work/C-INT/eng-base-0/r2 linear ledger 65103a0..0639ced plus F1 (2ca84b0) plus 8B HEAD
- Tag cint-integrated-8a at 0639ced (not moved); proposed tag cint-integrated-8b at HEAD
- HOLD retained: no human wiring, Programme C only, no core.py edits, no tag moves, no force-push, own checkout

## Next

Push HEAD to origin arena/01a0bbdd-cat-theo-machine, tag cint-integrated-8b via gh, keep HOLD.
