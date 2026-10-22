# INT report: live-proof-ingress rehearse-import

Date: 2026-09-12. Session branch: arena/01a09270-cat-theo-machine.
Role: INT. Candidate lane: arena/01a091e2-cat-theo-machine.

## STEP 1 — PIN

Fetched explicitly:

- origin arena/01a091e2-cat-theo-machine (evidence tip)
- origin arena/01a00f6b-cat-theo-machine (session fork base)
- origin master
- all origin arena/* refs plus tags (overlap survey)

SHA resolution, all three resolve:

- runtime source 033491542b2b4769bca3261e7df9982bd6084873, commit, tree cd64d7ded38bd0343340c20dc0d7489eec42ee77
- evidence 155e444efcd58fc5c02161673636e8c9faed1fc7, commit, tree b0e533b5a6e0ebed26ffaea0ccf8e8d01323b314
- evidence 90765947ccf477c73ce91b123eaca1a30fda9108, commit, tree 9f0b7941d11c479f678e6ea2855c1064af948a2a

Authoritative base for this session:

- ref arena/01a00f6b-cat-theo-machine @ 41e80785d4de090337a9dfc08439f2fcb45915dc
- tree 5ea629c0fab7d6a659d38490c9ae4eed2f3af544
- HEAD at session start equaled this SHA with a clean tree.

Descendant INT line noted for overlap purposes (not checked out, read by object
inspection only):

- ref arena/01a06542-cat-theo-machine @ 55b773de6a6f5fd07d1ad63a068b7b324b2e6d30
- ef571b688bcfb581bd3e65ec28a18f438ca32595 is an ancestor of that tip.
- 41e8078 is an ancestor of that tip. The source stack and this session share
  the same fork base.

Source ancestry (dependency order, cumulative candidate):

1. 41bcbf4f9fac4ee7b5ae5ab117724f0040a3e7df ingress parser, dispatch, submission, diagnostics, regressions
2. a5c4efdf27c2beff1aeb5fc8462ab115f47f8c6a daemon package routing, isolated live state
3. 1e8aab6d59fd2e7903f7c030fdf4fc870a94c3c0 worker goal transport, isolated comparison result directory
4. 033491542b2b4769bca3261e7df9982bd6084873 quantified normalization boundary, real worker-receipt verification

Changed production paths base..0334915:

- main.py (live dispatch, foreground submission, daemon routing, isolated state, worker receipt path)
- proof_ingress.py (new: natural proof-request envelope parsing)
- ingress_tests.py (new: regression suite)
- ingress_receipts.py (new: worker receipt verification)
- heuristics.py (forall normalization boundary)
- runtime.py (last_foreground_goal audit slot)
- search/compare_subprocess.py (wire transport, isolated result root)
- verification/live-proof-ingress.cmd, .inputs.txt, .sh (fixture)

Runtime-unchanged check 0334915..90765947:

- Only verification/ paths change (before/after/tests/live-transcript/manual
  inputs+transcript, defect ledger, 45 receipt wire files).
- Zero production-path delta. Verified by name-only inspection.

## STEP 2 — INSPECT OVERLAPS

Method: base..0334915 path inventory compared against base..55b773d (INT tip)
by object inspection. No INT-line checkout, no merge.

Findings:

1. heuristics.py — source adds a forall guard in HeuristicCanonicalTerm.
   INT tip leaves heuristics.py identical to base. No overlap. Clean.
2. runtime.py — source adds last_foreground_goal. INT tip leaves runtime.py
   identical to base. No overlap. Clean.
3. search/compare_subprocess.py — source switches manifest text to wire
   transport and honors HYGE_SNAPSHOT_DIR for the result root. INT tip leaves
   this file identical to base (its search-side change is confined to
   search/engine.py research-attempt recording). No overlap. Clean.
4. proof_ingress.py, ingress_tests.py, ingress_receipts.py — new files on the
   source side, absent on the INT tip. No file overlap. Clean.
5. main.py — shared file, heavy descendant divergence (+1564 on INT tip,
   +90 on source). Hunk-level review:
   - _search_worker_problem_from_manifest: INT tip identical to base; source
     replaces cases[0] fallback with refusal plus wire-request path. No
     content overlap. Clean.
   - SNAPSHOT_DIR line: INT tip identical to base; source adds
     HYGE_SNAPSHOT_DIR override with the old path as default. Clean.
   - run_live_mode daemon routing: base spawns "hyge.main"; INT tip spawns
     hardcoded "cat_theo_machine.main" (changed on the research/live-display
     lane); source spawns __package__ + ".main" plus isolated-state guard and
     owner-checked marker removal. Shared behavior, three spellings.
     For a future onto-INT-line import this hunk needs a named review:
     owners source lane (01a091e2) and research/live-display lane (7fd3d07
     line). On this session base the source hunk applies without conflict.
     Returned for review, not resolved silently.
   - run_talk_mode _respond dispatch: INT tip adds the research live protocol
     (research commands take precedence, ~1500 lines). Source inserts the
     ingress check at the top of _respond, ahead of all other dispatch.
     Onto-INT-line order needs an explicit precedence decision (ingress
     check vs _handle_research_command). Owners: source lane and
     research-protocol lane (01a059a2 merge line). Returned for review.
     On this session base the source hunk applies without conflict.
6. D11 shell work (INT tip commits e0853a9, 768ea6f, plus scope/ruling notes)
   touches packs.py, packs/*.yaml, tools/d11_gate.py, protocol/*, logs/*.
   No file overlap with the source path set. No conflict.
7. F1/D12 checkpoint and audit-header work (INT tip persistence.py +623,
   checkpoint paths): source does not touch persistence.py. Shared behavior
   note: source HYGE_SNAPSHOT_DIR override changes where talk/daemon/search
   state lives; default preserves the old path. Owners: source lane and
   persistence/F1 lane. Compatibility observed green here (isolated runs
   pass, shared-state hashes unchanged in the fixture). No blocking conflict.
8. Layer-D / workers: INT tip worker-side deltas are engine-level research
   recording; source deltas are subprocess transport + manifest refusal.
   No file overlap. No conflict.
9. Current parser and research-goal parser: INT tip adds research.py (4021
   lines) with its own grammar; source adds proof_ingress.py with a separate
   quantified-request grammar. No file overlap. Integration note carried
   forward from the lane ledger: after any onto-INT-line import, re-verify
   the ingress route against the INT research-mode grammar. Passing the
   live tests here does not establish that integration.

Overlap verdict for this session base: no textual conflicts; all four
runtime commits cherry-picked cleanly. Two named hunks (daemon routing
spelling, dispatch precedence) are returned for review before any
onto-INT-line import.

## STEP 3 — PRE-IMPORT BASELINE

Base: pristine archive of 41e8078 with archived snapshots moved aside and a
fresh empty snapshots directory (lane evidence method). Package copied to a
valid module name for the probe. Original checkout snapshots untouched.

- A valid positive-domain request:
  output: "I do not know the word: that for all n > a^n + b^n = c^n no
  solutions in positive integers", exit 0. No parsed goal, no submission.
- B natural-domain request:
  output: "I do not know the word: ... no solutions in natural numbers",
  exit 0. No clarification, no submission.
- C malformed quantified request (missing bound variable):
  output: "I do not know the word: ...", exit 0. No submission.
- D formal query "add ( two , two )": output "four", exit 0.

Structural identity at parser/coordinator/worker on base: not applicable, no
request is recognized, no goal exists, no worker job is submitted.
Prior-proof-state behavior on base: unrecognized input leaves last_* state
untouched (only UnderstoodLabel resets it).
Daemon routing on base: run_live_mode spawns module "hyge.main", which does
not match this checkout package; live daemon launch from this checkout is
broken at base.
Isolated-state paths on base: HYGE_SNAPSHOT_DIR is ignored; all state uses
the checkout snapshots/ directory.
Worker transport on base: display-text manifest with cases[0] fallback.

Original failure reproduction:

- BaseFailureNotReproduced(41e80785d4de090337a9dfc08439f2fcb45915dc, A/B/C).
- The strings from the operator transcript (expected-left-parenthesis,
  Use Predicate(constant), understood-a-natural-proof-request path) are
  absent from the base tree entirely. No regression repair is claimed on
  this base. The import proceeds as a compatibility and feature-import test.

Raw logs: verification/2026-09-12-int-baseline-A/B/C/D.log.

## STEP 4 — IMPORT

Runtime import: cherry-picked the exact four commits in dependency order onto
the clean session base:

- 5cb6993 [SHARED] add machine-native live proof ingress (from 41bcbf4)
- c791c5f [SHARED] isolate live state and correct daemon package routing (from a5c4efd)
- d74b5a4 [SHARED] preserve live goals across comparison-worker transport (from 1e8aab6)
- 95e8cb7 [SHARED] preserve scoped goals and verify actual worker receipts (from 0334915)

Zero conflicts. Imported HEAD tree cd64d7ded38bd0343340c20dc0d7489eec42ee77,
byte-identical to the source tree at 0334915. No wholesale branch merge.

Evidence import (separate commit, evidence only, never production inputs):

- 6567286 [INT] import live-ingress verification evidence from 155e444 + 90765947
- Contents: before/after/tests/live-transcript/manual inputs+transcript,
  defect ledger, 45 receipt wire files under
  verification/live-proof-ingress-receipts/.

INT test additions (separate commit):

- 839a85e [INT] ingress negative tests + dated admission artifacts
- ingress_tests.py gains four committed assertions (unrecognized formal
  cannot submit; clarification/malformed messages end in No proof submitted;
  canonical goal keeps its forall head). Style kept to machine terms, no new
  functions, no host-container constructs in the added lines.
- verification/2026-09-12-int-ingress-negative.sh: N3/N4/N5/N5b/N7.

## STEP 5 — TARGETED ACCEPTANCE

Committed ingress regression suite:

- python3 -u -m cat_theo_machine.ingress_tests → exit 0,
  PASS: proof ingress parser/dispatcher/scope regressions.
- Log: verification/2026-09-12-int-ingress-tests-console.txt.

Real live entrypoint (fixture verification/live-proof-ingress.sh with
HYGE_PARENT_FORMAL set to the base D log):

- exit 0, 8/8 acceptance groups.
- Valid requests: exactly 3 foreground submissions, 3 coordinator-preserved
  confirmations, one per valid request.
- Positive-integer request: canonical goal
  forall(n, implies(lt(2, ...), nosolutions(positive-integers, ...))) reaches
  the foreground prover.
- Natural-number request: precise clarification naming the zero question,
  zero submission.
- Malformed request: parse-failure, zero submission; the following why
  reports nothing to explain, so no prior goal or stale result leaks.
- Worker transport: 15/15 receipts structurally equal
  (parser == dispatcher == worker request == receipt == search goal),
  no bundled-example fallback, no stringified-goal substitution.
- Formal query: parent and candidate both return four (byte-identical,
  shared digest ab929fcd5594037960792ea0b98caf5fdaf6b60645e4ef248c28db74260f393e).
- Isolation: daemon cycles the isolated talk_state.wire; shared-state hashes
  unchanged before/after; foreign daemon marker preserved; foreign-owned
  state refuses a second daemon.
- Daemon: launches cat_theo_machine.main from the current checkout.
- Search outcome: stalls; no theorem asserted. Expected: ingress-only scope.

Independent live session (separate process, manual inputs, fresh state):

- exit 0; 1/1 foreground submission; 5/5 worker receipts structurally equal;
  clarification 1, parse-failure 1, formal four present.

Logs: verification/2026-09-12-int-live-proof-ingress-{tests,live-transcript,
after,console,manual-transcript,manual-receipts}.*.

## STEP 6 — NEGATIVE TESTS

Committed suite verification/2026-09-12-int-ingress-negative.sh, exit 0:

- N3 pass: malformed input submits nothing and clears the pending goal
  (fresh live: 1 submission for the valid line, parse-failure for the
  malformed line, why reports nothing to explain).
- N4 pass: worker with no request exits nonzero refusing a substitute
  theorem (no fallback to the first bundled example).
- N5 pass: worker with an unmatched legacy manifest exits nonzero refusing
  a substitute goal.
- N5b pass: tampered .received.wire fails ingress_receipts (nonzero exit,
  never silently accepted).
- N7 pass: result root honors HYGE_SNAPSHOT_DIR and keeps the old default
  otherwise.

Property mapping for the eight required negatives:

1. unrecognized natural request cannot submit a worker job — committed
   (formal unrecognized: recognized false AND SubmitForegroundGoal empty;
   plus live fixture phase gate: submissions only in parsed phases).
2. malformed input cannot submit a worker job — committed (seven malformed
   shapes: goal empty AND submit empty AND No-proof-submitted message;
   plus N3 live count).
3. failed parse clears any pending foreground goal — committed (N3) and
   retained (fixture why-after-malformed gate).
4. worker cannot fall back to the first bundled theorem example — committed
   (N4, N5) and retained (15/15 + 5/5 receipts equal submitted goals).
5. worker rejects a receipt whose goal differs structurally — retained
   (ingress_receipts machine-equality on request/receipt/search-goal for
   every receipt) with committed tamper-evidence (N5b fails closed).
6. normalization cannot reorder a quantified goal tree — committed
   (canonical == direct goal for seven valid shapes; forall head pinned).
7. result directory cannot escape the isolated-state root — committed (N7)
   and retained (fixture shared-hash + isolation gates).
8. a prior session result cannot satisfy a new request — retained by
   mechanism plus suite: _search_worker_snapshot_matches_current_problem
   demands TermEqual start/goal/heuristic before reuse, and receipts corpus
   membership plus exact-five-per-goal counts reject foreign goals;
   suite search_worker_resume_* tests cover the resume path.

## STEP 7 — FULL ADMISSION

Shard runner: tools/shard_suite.py as committed on this base. 252
registration slots, round-robin → 126 constructed per shard. This cut has no
OPEN sentinel concept; OPEN count is not applicable here.

Candidate (commit 839a85e, tree 0a5a52b47ce0099e4bf00fa7d64607a14e1f1006):

- shard 0: exit 0 (runner masks failures), elapsed 518.3 s.
  constructed 126, executed 126, passed 123, failed 3, skipped 0.
  failure set: converse_default_mode_test,
  tree_insert_deep_pair_lookup_avoids_recursion_test,
  compare_search_modes_fill_warms_resident_pool_before_root_wave_test.
- shard 1: exit 1. Installation abort in ConversePropositionTest constructor
  (testsuite.py:7448, M.Tail chain over an unexpected Converse outcome
  shape, AttributeError: Thingy has no tail). Slot 181 of 252 (shard-1
  member). No report produced, executed count unavailable past the abort.

Pristine base (archive of 41e8078, fresh snapshots, same runner):

- shard 0: exit 0, elapsed 530.4 s. Same 126/123/3 split with the identical
  three failure names.
- shard 1: exit 1. Identical abort at the same file, line, constructor, and
  exception.

Delta candidate-vs-base: zero on both shards. The three shard-0 failures and
the shard-1 installation abort are pre-existing suite defects at this cut,
outside ingress scope (Converse outcome shape; tree-insert; resident-pool
warmup). The candidate neither repairs nor extends them.

Per the standing rule, installation abort means no admission. Full admission
is therefore BLOCKED, the tag is withheld, and no merge is cut. The
rehearse-import, targeted gates, negatives, and both-shard evidence remain
committed on this branch for a follow-up after the suite defect is repaired
on its owning lane.

Raw logs and digests:

- verification/2026-09-12-int-shard-0.log 8d0bcd5fbf857795bba284d9ad1c649c13f7103291a1586c74cc50839bb0a12e
- verification/2026-09-12-int-shard-1.log b101fb19ba0a0863336200a4d7133d01299256e2928b9daeb77cde04b52b2700
- verification/2026-09-12-int-base-shard-0.log 2bf2b7e00312f0378c5bfc9056b043860b2a3711f8d2e83377d1bfb2711bc2a5
- verification/2026-09-12-int-base-shard-1.log 8d57653576d4b45777c4f3a75cc5da2fc6b107882aec7634f9d9e421862c5bfb
- verification/2026-09-12-int-baseline-A.log afc1c3fec96c927ae290af4fa1906a738337a3696c6b73c091e6122b2e27c86b
- verification/2026-09-12-int-baseline-B.log 48990f1c5cd98f4e89fcafcdb891a8d737f2dc74889a68ed529ef5d35478ec0c
- verification/2026-09-12-int-baseline-C.log 34d6d1f7c733587192ea1e61e2a9e9cf09e2817f310f00e27cb41dc467126ce7
- verification/2026-09-12-int-baseline-D.log ab929fcd5594037960792ea0b98caf5fdaf6b60645e4ef248c28db74260f393e
- verification/2026-09-12-int-formal-candidate.log ab929fcd5594037960792ea0b98caf5fdaf6b60645e4ef248c28db74260f393e
- verification/2026-09-12-int-ingress-tests-console.txt 3d86add0599df2ae325bf3d01a62d06a2baf6a0b461b96c968eeffac40900820
- verification/2026-09-12-int-live-proof-ingress-tests.txt 6682d99768e45820fea36e9357a6c9e32af2502adf63ab520854cfc7371f44e9
- verification/2026-09-12-int-live-proof-ingress-live-transcript.txt cb8e6b0eb7ee5d82270fff42d2c0b347081f0fbe29e78480cda1575269f4093c
- verification/2026-09-12-int-live-proof-ingress-after.txt ffbd46f1b125897bd6d79a06491421ece4c67a0bc408a87073c3d08e5f93ddc1
- verification/2026-09-12-int-live-proof-ingress-console.txt ffbd46f1b125897bd6d79a06491421ece4c67a0bc408a87073c3d08e5f93ddc1
- verification/2026-09-12-int-live-proof-ingress-manual-transcript.txt 318b9559a93bc48ab0908076205b0fbd0ef6390e7ec5aa38d4d514c238a5b93f
- verification/2026-09-12-int-live-proof-ingress-manual-receipts.txt b898dad40a3c742e92365d71b79ab172ffb237929d4a023a1c9b059f577cb2da
- verification/2026-09-12-int-ingress-negative-console.txt d8b0666a84bec03aa219f66a0b98caf5fdaf6b60645e4ef248c28db74260f393e
- verification/2026-09-12-int-negative-n3-transcript.txt d9ab97195058794367d6cef1f9f32f176a2798396a19a6c698845e31507a8c5e
- verification/2026-09-12-int-negative-n4.log 0cafa2957def0f5984d581977940ec4f71b1de9e970af64f52ebf2bfd374f2b2
- verification/2026-09-12-int-negative-n5.log 38a00b5087487cba2e5b4aeb7f34bbe2eee67f01b294d005cb31c30736e5f69b
- verification/2026-09-12-int-negative-n5b.log 334247d456dc8d423293c1a7ea43497cb0cff943a7c8446b990786ddaffa80e5

Commands and environment:

- fetch: git fetch origin arena/01a091e2-cat-theo-machine, arena/01a00f6b-cat-theo-machine, master, arena/*, tags
- import: git cherry-pick 41bcbf4 a5c4efd 1e8aab6 0334915; git checkout 90765947 -- verification/
- regressions: python3 -u -m cat_theo_machine.ingress_tests
- formal: HYGE_SNAPSHOT_DIR=<fresh> python3 -u -m cat_theo_machine.main talk 'add ( two , two )'
- fixture: HYGE_PARENT_FORMAL=<base D log> bash verification/live-proof-ingress.sh
- manual: HYGE_SNAPSHOT_DIR=<fresh> HYGE_SEARCH_WORKER_TIMEOUT=5 python3 -u -m cat_theo_machine.main live --workers 1 < manual-inputs; then ingress_receipts with the same state
- negatives: bash verification/2026-09-12-int-ingress-negative.sh
- shards: PYTHONPATH=<root> HYGE_SNAPSHOT_DIR=<per-shard fresh> python3 -u cat_theo_machine/tools/shard_suite.py <0|1> 2
- environment: sandbox Bash, Python 3.11.2, gmpy2 2.3.1, pyyaml 6.0.3.

Daemon/live-mode tests: no daemon-named suite tests exist at this cut;
daemon routing, isolated state, ownership refusal, and live conversation
behavior are covered by the live fixture and N3 (all green).

## STEP 8 — CLASSIFY AND TAG

Classification: SEMANTIC.

Grounds: changes which natural-language requests become proof goals; changes
cross-process goal transport; changes isolated live-state routing.

Ruling: full admission BLOCKED by the pre-existing shard-1 installation
abort (identical on pristine base and candidate). No merge cut, no tag cut.
Withheld strictly per the installation-abort rule even though the targeted
ingress gates are all green and the shard delta is zero.

The rehearse-import stays on this branch, branch-pushed, with lane evidence
preserved separately (commit 6567286) and INT artifacts dated 2026-09-12.

Removed blocker (demonstrated on this branch, unreleased):

- natural request → canonical goal → correct worker transport

Still open:

- canonical goal → shell-level concrete residual (D11 shell characterization integration)
- shell residual → checked quantified proof (binder-safe logical checker; premise-bound teaching)
- trusted theorem → exact requested premise
- SUCCESS → every obligation replayed (D21/D22 per-obligation acceptance)
- session → content-addressed checkpoint and complete identity header (F1 checkpoint replay, D12 identity header)
- suite health at this cut: shard-1 ConversePropositionTest installation abort (owning lane: Converse/grammar suite health; blocks any full admission here)
- onto-INT-line import: daemon-routing spelling and dispatch-precedence reviews; research-grammar re-verification
- final combined semantic tag

No F readiness is announced. Measurements using this path still require
blank-control reruns after any future release.

## END REPORT

agent: INT
authoritative base: arena/01a00f6b-cat-theo-machine@41e80785d4de090337a9dfc08439f2fcb45915dc
runtime source: 0334915
evidence source: 155e444 + 90765947
original failure reproduced: no (BaseFailureNotReproduced; compatibility and feature-import test)
overlaps: none blocking on this base; two named hunks returned for onto-INT-line review (daemon-routing spelling: source lane vs research/live-display lane; dispatch precedence: source lane vs research-protocol lane)
targeted ingress tests: 8/8 groups green; regressions green; negatives N3/N4/N5/N5b/N7 green
worker receipts: 15/15 fixture + 5/5 independent, all structurally equal
independent live run: pass
formal-query regression: pass (byte-identical four)
both shards: 252 slots, 126 per shard; shard 0 exit 0 with 123 pass / 3 pre-existing failures (converse_default_mode_test, tree_insert_deep_pair_lookup_avoids_recursion_test, compare_search_modes_fill_warms_resident_pool_before_root_wave_test); shard 1 exit 1 installation abort in ConversePropositionTest, identical on pristine base; delta zero; OPEN n/a at this cut
classification: SEMANTIC
integrated commit: none (full admission blocked; rehearse-import held on this branch at 839a85e)
tag: none
tag scope: none
remaining blockers: shard-1 ConversePropositionTest installation abort; D11 shell characterization integration; binder-safe logical checker; premise-bound teaching; D21/D22 per-obligation acceptance; F1 checkpoint replay and D12 identity header; onto-INT-line daemon/dispatch reviews; final combined semantic tag
